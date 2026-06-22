import time
from typing import Optional, Union

from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# run_in_threadpool 已移除：handwrite() 返回惰性生成器（map 对象），
# 真正的 CPU 密集渲染在后续 for 循环消费生成器时才发生，
# 而 generate_handwriting_impl 整体运行在 BackgroundTask 里，HTTP 请求已秒回，
# 所以 run_in_threadpool 在此场景下无法真正释放事件循环。

# from threading import Thread

load_dotenv()

# 导入配置（敏感信息从环境变量读取，不得硬编码）
from config import settings, DATA_ROOT
import os
from contextlib import asynccontextmanager

# 桌面模式：内嵌 pandoc 支持（必须在 pypandoc 使用前设置）
# DATA_ROOT 在 PyInstaller 下指向 _internal/，开发模式下指向 backend/
if settings.desktop_mode.lower() == "true":
    _pandoc_path = os.path.join(DATA_ROOT, "pandoc", "pandoc.exe")
    if os.path.isfile(_pandoc_path):
        os.environ["PYPANDOC_PANDOC"] = _pandoc_path
        print(f"Desktop mode: using bundled pandoc at {_pandoc_path}")

from utils.logging_setup import setup_logging
from uuid import uuid4

import pypandoc

# 图片处理模块
from identify import identify_distance
from werkzeug.utils import secure_filename


from services.cleanup import (
    safe_remove_file,
    cleanup_marked_directories,
)

# 装饰器 7.15
from functools import wraps

# 定时清理文件 10.28

# sentry 错误报告7.7
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# 限制请求速率 7.9
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from task_store import cleanup_expired as cleanup_expired_generation_tasks
from task_store import get_active_task_count as get_generation_active_task_count
from task_store import get_task as get_generation_task
from task_store import pop_task as pop_generation_task
from task_store import read_result_file
from task_store import set_task as set_generation_task
from task_types import (
    GenerateHandwritingParams,
    form_dependency_from_model,
)

# 获取环境变量
mysql_host = os.getenv("MYSQL_HOST", "db")
enable_user_auth = os.getenv("ENABLE_USER_AUTH", "false")

# 上传文件临时目录（使用 settings.upload_dir，避免 cwd 问题）
upload_base = settings.upload_dir
textfileprocess_dir = os.path.join(upload_base, "textfileprocess")
imagefileprocess_dir = os.path.join(upload_base, "imagefileprocess")
for d in [textfileprocess_dir, imagefileprocess_dir]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

font_assets_dir = settings.font_assets_dir
font_assets_bundled_dir = settings.font_assets_bundled_dir

from services.fonts import sync_font_assets

os.makedirs(font_assets_dir, exist_ok=True)
# sync_font_assets 已移至 lifespan，避免导入副作用
# sync_font_assets(font_assets_bundled_dir, font_assets_dir)

# font_file_names 已移至 services.fonts.get_font_file_names()
# 日志配置：使用 utils.logging_setup 统一配置（RotatingFileHandler + 级别控制）
logger = setup_logging(settings.log_level)

# sentry部分 7.7
# 仅当配置了 DSN 时才初始化 Sentry，避免硬编码
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
else:
    logger.warning("SENTRY_DSN 未配置，错误上报已禁用")

# 启动计划任务线程, 定时清理（移至 lifespan）
# schedule_clean.start_schedule_thread()  # 已移至 lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期：启动时初始化，关闭时清理。
    所有模块级副作用统一在此执行，避免 import 时产生副作用。
    """
    logger.info("Application starting up...")

    # 1. 同步字体文件
    sync_font_assets(font_assets_bundled_dir, font_assets_dir)
    # 重新扫描字体文件列表（font_file_names 已移至 services.fonts）

    # 2. 确保 Pandoc 可用（import pypandoc 已在模块顶层完成）
    # 桌面模式：绝不联网下载，缺了就报错
    # 非桌面模式：缺了自动下载
    try:
        pypandoc.get_pandoc_version()
        logger.info("Pandoc is available")
    except (OSError, RuntimeError):
        if settings.desktop_mode.lower() == "true":
            logger.error("桌面模式缺少 pandoc，请检查打包。pandoc.exe 应位于 %s", os.path.join(DATA_ROOT, "pandoc", "pandoc.exe"))
            # 桌面模式不下载，但也不强制崩溃——让接口在用时报错，方便用户排查
        else:
            logger.info("Pandoc not found, downloading...")
            pypandoc.download_pandoc()
            logger.info("Pandoc downloaded successfully.")

    # 3. 初始化任务数据库
    from task_store import init as init_task_store

    init_task_store()

    # 4. 启动定时清理线程
    from schedule_clean import start_schedule_thread

    start_schedule_thread()

    logger.info("Application startup complete.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# 自定义 422 错误响应，把字段名提取出来让前端更易读
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    missing_fields = []
    invalid_fields = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err["loc"] if l not in ("body", "query", "path"))
        if err["type"] in ("missing", "value_error.missing"):
            missing_fields.append(loc)
        else:
            invalid_fields.append(f"{loc}: {err['msg']}")

    if missing_fields:
        message = f"缺少必填字段: {', '.join(missing_fields)}"
    else:
        message = f"字段验证失败: {', '.join(invalid_fields)}"

    return JSONResponse(
        status_code=422,
        content={
            "status": "fail",
            "message": message,
            "errors": [
                {"field": ".".join(str(l) for l in e["loc"] if l not in ("body", "query", "path")), "message": e["msg"]}
                for e in exc.errors()
            ],
        },
    )


# 设置Flask app的logger级别
# app.logger.setLevel(logging.DEBUG)

# SECRET_KEY 已移至环境变量（当前未启用用户认证）
# 如需启用，在 .env 中配置 SECRET_KEY

# app.config["SESSION_TYPE"] = "filesystem"  # 设置session存储方式为文件
# Session(app)  # 初始化扩展，传入应用程序实例
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per 5 minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 创建一个新的笔记本背景图片，支持四种纸张模板与自定义纸张颜色
from services.file_processing import (
    convert_docx_to_text,
    read_pdf,
)


def handle_exceptions(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            logger.info("An error occurred during the request: %s", e)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    return decorated_function


from services.task_manager import (
    build_task_status_payload,
    register_task_websocket,
    unregister_task_websocket,
)

# _generation_semaphore 已移至 services.generation

from services.generation import (
    run_generation_task,
)


@app.post("/api/generate_handwriting")
@limiter.limit("200 per 5 minute")
@handle_exceptions  # 错误捕获的装饰器7.15
async def generate_handwriting(
    request: Request,
    background_tasks: BackgroundTasks,
    params: GenerateHandwritingParams = Depends(form_dependency_from_model(GenerateHandwritingParams)),
    background_image: Union[UploadFile, str] = File(None),
    font_file: Union[UploadFile, str] = File(None),
):
    cleanup_expired_generation_tasks()

    # ── 并发上限检查 ────────────────────────────────────────────────────
    MAX_ACTIVE_TASKS = 8  # pending + processing 总数上限，根据服务器配置调整
    # 队列满时给用户的建议等待时间（秒），固定值比瞎算可靠
    ESTIMATED_WAIT_SECONDS = 60

    active_count = get_generation_active_task_count()
    if active_count >= MAX_ACTIVE_TASKS:
        return JSONResponse(
            {
                "status": "queue_full",
                "message": "当前服务器队列已满，请稍后再试",
                "active_task_count": active_count,
                "max_active_tasks": MAX_ACTIVE_TASKS,
                "estimated_wait_seconds": ESTIMATED_WAIT_SECONDS,
            },
            status_code=503,
        )
    # ────────────────────────────────────────────────────────────────────

    background_image_bytes = None
    # 注意：starlette.datastructures.UploadFile 可能是 fastapi.UploadFile 的运行时类型
    # 用 hasattr 兼容两者：检查是否有 read 方法（UploadFile 特征）
    if hasattr(background_image, "read") and hasattr(background_image, "filename"):
        background_image_bytes = await background_image.read()

    font_file_bytes = None
    # 同样用 hasattr 兼容 starlette 和 fastapi 的 UploadFile
    if hasattr(font_file, "read") and hasattr(font_file, "filename"):
        font_file_bytes = await font_file.read()

    payload = {
        "params": params,
        "background_image": background_image_bytes,
        "font_file": font_file_bytes,
    }

    task_id = uuid4().hex
    now = time.time()
    set_generation_task(
        task_id,
        status="pending",
        stage="queued",
        message="任务排队中",
        progress=0,
        created_at=now,
        updated_at=now,
        response_status_code=None,
        response_content_type=None,
        response_headers={},
        error_message=None,
    )
    background_tasks.add_task(run_generation_task, task_id, str(request.base_url), payload)

    return JSONResponse({"status": "accepted", "task_id": task_id})


@app.websocket("/api/generate_handwriting/ws/{task_id}")
async def generate_handwriting_task_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    await register_task_websocket(task_id, websocket)
    try:
        task = get_generation_task(task_id)
        if task is None:
            await websocket.send_json({"status": "error", "message": "Task not found", "task_id": task_id})
            return
        await websocket.send_json(build_task_status_payload(task_id, task=task))

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await unregister_task_websocket(task_id, websocket)


@app.get("/api/generate_handwriting/task/{task_id}")
@limiter.limit("600 per 5 minute")
@handle_exceptions
async def get_generate_handwriting_task_status(request: Request, task_id: str):
    cleanup_expired_generation_tasks()
    task = get_generation_task(task_id)
    if task is None:
        return JSONResponse(
            {"status": "error", "message": "Task not found"},
            status_code=404,
        )
    return JSONResponse(build_task_status_payload(task_id, task=task))


@app.get("/api/generate_handwriting/task/{task_id}/result")
@limiter.limit("600 per 5 minute")
@handle_exceptions
async def get_generate_handwriting_task_result(request: Request, task_id: str):
    cleanup_expired_generation_tasks()
    task = get_generation_task(task_id)
    if task is None:
        return JSONResponse(
            {"status": "error", "message": "Task not found"},
            status_code=404,
        )

    task_status = task.get("status")
    if task_status in ("pending", "processing"):
        return JSONResponse(
            {"status": "processing", "message": "Task is still running"},
            status_code=409,
        )
    if task_status == "failed":
        pop_generation_task(task_id)
        return JSONResponse(
            {"status": "error", "message": task.get("error_message", "Task failed")},
            status_code=500,
        )

    # 从磁盘文件读取响应体
    result_file_path = task.get("result_file_path")
    response_body = read_result_file(result_file_path) if result_file_path else b""
    if response_body is None:
        response_body = b""

    response = Response(
        content=response_body,
        media_type=task.get("response_content_type") or "application/octet-stream",
        status_code=task.get("response_status_code") or 200,
        headers=task.get("response_headers") or {},
    )
    pop_generation_task(task_id)
    return response


# @app.after_request
# def cleanup(response):
#     # 从请求上下文中获取文件路径
#     temp_file_path = getattr(request, 'temp_file_path', None)
#     if temp_file_path is not None:
#         # 尝试删除文件
#         try:
#             os.remove(temp_file_path)
#         except Exception as e:
#             app.logger.error(f"Failed to remove temporary PDF file: {e}")
#     # 返回原始响应
#     return response
_ALLOWED_EXTENSIONS = {
    "docx": b"PK\x03\x04",
    "doc": b"PK\x03\x04",
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "txt": None,  # 无严格魔数，跳过
    "rtf": None,
}


def validate_upload(content: bytes, filename: str) -> Optional[str]:
    """校验上传文件：大小 + 魔数。返回错误消息字符串，或 None 表示通过。"""
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        return f"文件过大（最大 {settings.max_upload_mb}MB）"

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    expected_magic = _ALLOWED_EXTENSIONS.get(ext)
    if expected_magic is not None and not content.startswith(expected_magic):
        return f"无效的文件类型：{filename}（文件头不匹配）"
    return None


@app.post("/api/textfileprocess")
@limiter.limit("200 per 5 minute")
async def textfileprocess(request: Request, file: UploadFile = File(...)):
    if file is None or file.filename == "":
        return JSONResponse({"error": "No file part in the request"}, status_code=400)

    if file and (
        file.filename.endswith(".docx")
        or file.filename.endswith(".pdf")
        or file.filename.endswith(".doc")
        or file.filename.endswith(".txt")
        or file.filename.endswith(".rtf")
    ):
        # secure_filename 会清掉中文等非 ASCII 字符（如"我的论文.docx" -> "docx"），
        # 导致多文件冲突或路径异常，这里加上 uuid 前缀保证唯一与可读
        safe_name = secure_filename(file.filename)
        # 如果 secure_filename 把名字清空（纯中文文件名），用 uuid 兜底并保留扩展名
        if not safe_name or safe_name == os.path.splitext(file.filename)[1].lstrip("."):
            ext = os.path.splitext(file.filename)[1]
            safe_name = f"{uuid4().hex}{ext}"
        else:
            safe_name = f"{uuid4().hex}_{safe_name}"
        filename = safe_name
        filepath = os.path.join(textfileprocess_dir, filename)  # 临时目录
        content = await file.read()
        err = validate_upload(content, file.filename)
        if err:
            return JSONResponse({"error": err}, status_code=400)
        with open(filepath, "wb") as f:
            f.write(content)
        text = "读取失败"  # Default value for text
        try:
            if file.filename.endswith(".docx"):
                text = convert_docx_to_text(filepath)
            elif file.filename.endswith(".pdf"):
                text = read_pdf(filepath)
            elif file.filename.endswith(".txt") or file.filename.endswith(".rtf"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif file.filename.endswith(".doc"):
                text = "doc文件暂不支持"
        except Exception as e:
            logger.exception("textfileprocess failed for file: %s", filename)
            return JSONResponse({"error": f"Error reading file: {str(e)}"}, status_code=500)

        # 删除临时文件
        safe_remove_file(filepath)

        return JSONResponse({"text": text})

    return JSONResponse({"error": "Invalid file type"}, status_code=400)


@app.post("/api/imagefileprocess")
@limiter.limit("200 per 5 minute")
async def imagefileprocess(request: Request, file: UploadFile = File(...)):
    if file is None or file.filename == "":
        return JSONResponse({"error": "No file part in the request"}, status_code=400)

    if file and (file.filename.endswith(".jpg") or file.filename.endswith(".png") or file.filename.endswith(".jpeg")):
        filename = secure_filename(file.filename)
        filepath = os.path.join(imagefileprocess_dir, filename)
        content = await file.read()
        err = validate_upload(content, file.filename)
        if err:
            return JSONResponse({"error": err}, status_code=400)
        with open(filepath, "wb") as f:
            f.write(content)
        try:
            (
                avg_l_whitespace,
                avg_r_whitespace,
                avg_t_whitespace,
                avg_b_whitespace,
                avg_distance,
            ) = identify_distance(filepath)
        except Exception as e:
            safe_remove_file(filepath)
            return JSONResponse(
                {"error": f"图片识别失败: {str(e)}", "warning": "无法识别图片中的横线，请换一张图片重试"},
                status_code=200,
            )
        finally:
            # 确保文件被清理
            if os.path.exists(filepath):
                safe_remove_file(filepath)
        # 检查识别结果是否全0（识别失败兜底）
        if (
            avg_l_whitespace == 0
            and avg_r_whitespace == 0
            and avg_t_whitespace == 0
            and avg_b_whitespace == 0
            and avg_distance == 0
        ):
            return JSONResponse(
                {
                    "marginLeft": 0,
                    "marginRight": 0,
                    "marginTop": 0,
                    "marginBottom": 0,
                    "lineSpacing": 0,
                    "warning": "未检测到横线，已返回默认值0。请尝试上传横线更清晰的图片。",
                }
            )
        return JSONResponse(
            {
                "marginLeft": avg_l_whitespace,
                "marginRight": avg_r_whitespace,
                "marginTop": avg_t_whitespace,
                "marginBottom": avg_b_whitespace,
                "lineSpacing": avg_distance,
            }
        )
    else:
        return JSONResponse({"error": "Invalid file type, only .jpg/.png/.jpeg allowed"}, status_code=400)


def get_filenames_in_dir(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(".ttf")]


@app.get("/api/fonts_info")
def get_fonts_info():
    filenames = get_filenames_in_dir(font_assets_dir)
    logger.info(f"filenames: {filenames}")
    if filenames == []:
        return JSONResponse({"error": "fontfile not found"}, status_code=400)
    return JSONResponse(filenames)


def mysql_operation(image_data):
    # session 已移除，此函数为死代码保留
    # cursor = current_app.cnx.cursor()
    # username = session["username"]
    # 先检查用户是否已存在
    # cursor.execute("SELECT * FROM user_images WHERE username=%s", (username,))
    # result = cursor.fetchone()

    # 根据查询结果来判断应该插入新纪录还是更新旧纪录
    # if result is None:
    #     # 如果用户不存在，插入新纪录
    #     sql = "INSERT INTO user_images (username, image) VALUES (%s, %s)"
    #     params = (username, image_data)
    # else:
    #     # 如果用户已存在，更新旧纪录
    #     sql = "UPDATE user_images SET image=%s WHERE username=%s"
    #     params = (image_data, username)
    try:
        pass
        # 执行 SQL 语句
        # 提交到数据库执行
        # cursor.execute(sql, params)
        # current_app.cnx.commit()
    except Exception as e:
        # 发生错误时回滚
        # current_app.cnx.rollback()
        logger.info(f"An error occurred: {e}")


# @app.route("/api/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     logger.info(f"Received username: {username}")  # 打印接收到的用户名
#     logger.info(f"Received password: {password}")  # 打印接收到的密码
#     try:
#         cursor = current_app.cnx.cursor()
#         cursor.execute(
#             f"SELECT password FROM user_images WHERE username=%s", (username,)
#         )
#         result = cursor.fetchone()
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         return jsonify({"error": "An error occurred"}), 500

#     if result and result[0] == password:
#         session["username"] = username
#         session.permanent = True
#         logger.info(f"Login success for user: {username}")
#         return {"status": "success"}, 200
#     else:
#         logger.error(f"Login failed for user: {username}")
#         return {
#             "status": "failed",
#             "error": "Login failed. Check your username and password.",
#         }, 401


# @app.route("/api/register", methods=["POST"])
# def register():
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     try:
#         cursor = current_app.cnx.cursor()
#         cursor.execute(f"SELECT * FROM user_images WHERE username=%s", (username,))
#         result = cursor.fetchone()
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         return jsonify({"error": "An error occurred"}), 500

#     if not result:
#         try:
#             cursor.execute(
#                 f"INSERT INTO user_images (username, password) VALUES (%s, %s)",
#                 (username, password),
#             )
#             current_app.cnx.commit()
#             session["username"] = username
#             logger.info(f"User: {username} registered successfully.")
#             return jsonify(
#                 {
#                     "status": "success",
#                     "message": "Account created successfully. You can now log in.",
#                 }
#             )
#         except mysql.connector.Error as err:
#             logger.error(f"Failed to insert user: {username} into DB. Error: {err}")
#             return (
#                 jsonify(
#                     {
#                         "status": "fail",
#                         "message": "Error occurred during registration.",
#                     }
#                 ),
#                 500,
#             )
#     else:
#         logger.error(f"Username: {username} already exists.")
#         return (
#             jsonify(
#                 {
#                     "status": "fail",
#                     "message": "Username already exists. Choose a different one.",
#                 }
#             ),
#             400,
#         )


# 捕获所有未捕获的异常，返回给前端，只能用于生产环境7.12
# @app.errorhandler(Exception)
# def handle_exception(e):
#     # Pass the error to Flask's default error handling.
#       tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
#     response = {
#
#             "type": type(e).__name__,  # The type of the exception
#             "message": str(e),  # The message of the exception
#
#     }
#     return jsonify(response), 500


# @app.before_request
# def before_request():
#     if enable_user_auth.lower() == "true":
#         current_app.cnx = mysql.connector.connect(
#             host=mysql_host, user="myuser", password="mypassword", database="mydatabase"
#         )
#     else:
#         pass


@app.middleware("http")
async def after_request(request: Request, call_next):
    response = await call_next(request)
    if enable_user_auth.lower() == "true":
        # if hasattr(current_app, "cnx"):
        #     current_app.cnx.close()
        # 仅用于调试 7.13
        # session.clear()
        return response
    else:
        print(response)
        return response


# ── 桌面模式：挂载前端静态文件 ──────────────────────────────────────────────────
# 必须放在所有 API 路由之后，否则 catch-all 会吞掉 /api。
# 通过环境变量 DESKTOP_MODE=true 启用（settings.desktop_mode）。

if settings.desktop_mode.lower() == "true":
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    _fe_dist = settings.frontend_dist
    if os.path.isdir(_fe_dist):
        # 挂载 /assets 静态目录（JS/CSS/图片等）
        _assets_dir = os.path.join(_fe_dist, "assets")
        if os.path.isdir(_assets_dir):
            app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

        @app.get("/")
        async def desktop_index():
            """桌面模式：根路径返回前端 index.html"""
            return FileResponse(os.path.join(_fe_dist, "index.html"))

        @app.get("/{full_path:path}")
        async def desktop_spa_fallback(full_path: str):
            """SPA 历史模式回退：非 API 路径返回 index.html（或静态文件）。"""
            candidate = os.path.join(_fe_dist, full_path)
            if os.path.isfile(candidate):
                return FileResponse(candidate)
            return FileResponse(os.path.join(_fe_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn

    # 启动时清理之前标记的目录
    cleanup_marked_directories()
    uvicorn.run(app, host="0.0.0.0", port=5005)


# poetry
def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5005)

    # good luck 6/16/2023
    # thank you 2/14/2025


"""
数据库初始化操作

CREATE TABLE user_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    image BLOB,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


数据库结构
mysql -u root -p进入数据库
USE your_database;数据库中的一个库
describe user_images;表：
"""
