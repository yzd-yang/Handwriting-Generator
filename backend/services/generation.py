"""
手写文字生成核心逻辑。

从 app.py 中拆分出来（P1 2.4 重构）。
包含 generate_handwriting_impl（CPU 密集渲染）和 run_generation_task（后台任务调度）。
"""

import asyncio
import base64
import io
import json
import os
import shutil
import tempfile
import time
from typing import Union

import psutil
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse, Response
from handright import Template, handwrite
from PIL import Image, ImageFont

from pdf import generate_pdf
from services.cleanup import (
    safe_remove_directory,
    safe_remove_file,
    safe_save_and_close_image,
)
from services.file_processing import apply_paragraph_layout
from services.fonts import get_font_file_names, get_font_path
from services.image_utils import create_notebook_image
from services.task_manager import (
    model_to_dict,
    push_task_status_update,
)
from task_store import set_task as set_generation_task
from task_types import GenerateHandwritingParams

from config import settings

from utils.logging_setup import get_logger

logger = get_logger(__name__)

# 同时执行的上限——控制 generate_handwriting_impl 的真正并发数
MAX_CONCURRENT_EXECUTIONS = 2
_generation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)


def generate_handwriting_impl(
    base_url: str,
    params: GenerateHandwritingParams,
    background_image: Union[UploadFile, str, bytes] = File(None),
    font_file: Union[UploadFile, str, bytes] = File(None),
    progress_hook=None,
):
    """
    CPU 密集的手写渲染函数。

    设计为同步函数，由 run_generation_task 通过 asyncio.to_thread() 调用，
    避免阻塞事件循环（WebSocket 推送、其他请求均不受影响）。
    """

    def report_progress(stage, message, progress):
        if progress_hook is not None:
            progress_hook(stage=stage, message=message, progress=progress)

    report_progress("validating", "正在校验参数", 5)
    # 归一化：前端可能发字符串 "null"，需要转成 Python None
    if isinstance(background_image, str):
        background_image = None
    if isinstance(font_file, str):
        font_file = None
    # 把所有 form 字段收拢成 data dict，方便后续代码不大改
    data = model_to_dict(params)

    report_progress("system_check", "正在检查服务器负载", 10)
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 90:
        return JSONResponse(
            {
                "status": "waiting",
                "message": f"CPU usage is too high. Please wait and try again. current cpu_usage: {cpu_usage}%",
            },
            status_code=429,
        )

    enable_user_auth = os.getenv("ENABLE_USER_AUTH", "false")
    if enable_user_auth.lower() == "true":
        pass

    if len(data["text"]) > 10000:
        return JSONResponse(
            {
                "status": "error",
                "message": "The text is too long to process. If you want to use this service, please build your own application.",
            },
            status_code=500,
        )

    # 如果用户提供了宽度和高度，创建一个新的笔记本背景图像
    if "width" in data and "height" in data:
        report_progress("prepare_background", "正在创建背景图", 20)
        line_spacing = int(data.get("line_spacing", 30))
        top_margin = int(data.get("top_margin", 0))
        bottom_margin = int(data.get("bottom_margin", 0))
        left_margin = int(data.get("left_margin", 0))
        right_margin = int(data.get("right_margin", 0))
        width = int(data["width"])
        height = int(data["height"])
        font_size = int(data.get("font_size", 0))
        isUnderlined = data.get("isUnderlined", False)
        paper_type = data.get("paper_type", "lines")
        paper_color = data.get("paper_color", "#FFFFFF")
        background_image_obj = create_notebook_image(
            width,
            height,
            line_spacing,
            top_margin,
            bottom_margin,
            left_margin,
            right_margin,
            font_size,
            isUnderlined,
            paper_type=paper_type,
            paper_color=paper_color,
        )

    else:
        report_progress("prepare_background", "正在读取背景图", 20)
        if background_image is None:
            return JSONResponse(
                {
                    "status": "fail",
                    "message": "Missing required field: background_image",
                },
                status_code=400,
            )
        if isinstance(background_image, (bytes, bytearray)):
            image_data = io.BytesIO(background_image)
        else:
            image_data = io.BytesIO(background_image.read())

        try:
            background_image_obj = Image.open(image_data)
            if background_image_obj.mode in ("RGBA", "LA"):
                background_image_obj = background_image_obj.convert("RGB")
        except IOError:
            return JSONResponse({"status": "error", "message": "Invalid image format"}, status_code=400)

    text_to_generate = data["text"]

    # Conditionally adjust spacing for English text based on user setting
    if data.get("enableEnglishSpacing", "false").lower() == "true":
        import re

        def replace_english_spaces(text):
            """Replace single spaces with double spaces only for English text"""
            english_pattern = r"^[a-zA-Z0-9.,!?;:\'\"()\-_]+$"
            lines = text.split("\n")
            processed_lines = []
            for line in lines:
                parts = line.split(" ")
                if len(parts) <= 1:
                    processed_lines.append(line)
                    continue
                result = []
                for i, part in enumerate(parts):
                    result.append(part)
                    if i < len(parts) - 1:
                        current_is_english = bool(re.match(english_pattern, part)) if part.strip() else False
                        next_is_english = (
                            bool(re.match(english_pattern, parts[i + 1])) if parts[i + 1].strip() else False
                        )
                        if current_is_english and next_is_english:
                            result.append("  ")
                        else:
                            result.append(" ")
                processed_lines.append("".join(result))
            return "\n".join(processed_lines)

        text_to_generate = replace_english_spaces(text_to_generate)

    logger.info("text_to_generate length=%d", len(text_to_generate))

    # 字体处理
    if font_file is not None:
        report_progress("prepare_font", "正在加载字体文件", 30)
        if isinstance(font_file, (bytes, bytearray)):
            font_bytes = font_file
        else:
            font_bytes = font_file.read()
        font = ImageFont.truetype(io.BytesIO(font_bytes), size=int(data["font_size"]))
    else:
        report_progress("prepare_font", "正在读取系统字体", 30)
        font_option = data["font_option"]
        font_names = get_font_file_names()
        logger.info(f"font_option: {font_option}")
        logger.info(f"font_file_names: {font_names}")
        if font_option in font_names:
            font_path = get_font_path(font_option)
            logger.info(f"font_path: {font_path}")
            with open(font_path, "rb") as f:
                font_content = f.read()
            font = ImageFont.truetype(io.BytesIO(font_content), size=int(data["font_size"]))
        else:
            return JSONResponse(
                {
                    "status": "fail",
                    "message": "Missing  fontfile.",
                },
                status_code=400,
            )

    template = Template(
        background=background_image_obj,
        font=font,
        line_spacing=int(data["line_spacing"]),
        left_margin=int(data["left_margin"]),
        top_margin=int(data["top_margin"]),
        right_margin=int(data["right_margin"]) - int(data["word_spacing"]) * 2,
        bottom_margin=int(data["bottom_margin"]),
        word_spacing=int(data["word_spacing"]),
        line_spacing_sigma=int(data["line_spacing_sigma"]),
        font_size_sigma=int(data["font_size_sigma"]),
        word_spacing_sigma=int(data["word_spacing_sigma"]),
        end_chars="，。",
        perturb_x_sigma=int(data["perturb_x_sigma"]),
        perturb_y_sigma=int(data["perturb_y_sigma"]),
        perturb_theta_sigma=float(data["perturb_theta_sigma"]),
        strikethrough_probability=float(data["strikethrough_probability"]),
        strikethrough_length_sigma=float(data["strikethrough_length_sigma"]),
        strikethrough_width_sigma=float(data["strikethrough_width_sigma"]),
        strikethrough_angle_sigma=float(data["strikethrough_angle_sigma"]),
        strikethrough_width=float(data["strikethrough_width"]),
        ink_depth_sigma=float(data["ink_depth_sigma"]),
    )

    # 段落排版预处理
    try:
        _layout = data.get("paragraph_layout", "default")
        _indent = int(data.get("first_line_indent", "0"))
        _pspacing = int(data.get("paragraph_spacing", "0"))
        _bg_w = background_image_obj.width
        _box_w = _bg_w - int(data["left_margin"]) - int(data["right_margin"])
    except Exception:
        _layout, _indent, _pspacing, _box_w = "default", 0, 0, 0

    if (_layout != "default") or (_indent > 0) or (_pspacing > 0):
        text_to_generate = apply_paragraph_layout(text_to_generate, data, font, _box_w)
        logger.info(
            "apply_paragraph_layout: layout=%s indent=%d spacing=%d box_width=%d",
            _layout,
            _indent,
            _pspacing,
            _box_w,
        )

    logger.info(f"data[pdf_save]: {data['pdf_save']}")
    if not data["pdf_save"] == "true":
        report_progress("rendering", "正在生成手写图像", 45)
        images = handwrite(text_to_generate, template)
        logger.info("handwrite initial images generated successfully")
        project_temp_base = settings.temp_dir
        os.makedirs(project_temp_base, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=project_temp_base)
        unique_filename = "images_" + str(time.time())
        zip_path = os.path.join(project_temp_base, f"{unique_filename}.zip")
        is_preview = data["preview"] == "true"
        full_preview = data.get("full_preview", "true") if is_preview else None
        if is_preview:
            logger.info(f"Preview mode enabled, full_preview: {full_preview}")

        try:
            preview_images_base64 = []
            try:
                total_images = len(images)
                if total_images <= 0:
                    total_images = 1
            except TypeError:
                total_images = None
            for i, im in enumerate(images):
                if total_images is None:
                    dynamic_progress = min(90, 60 + min(i, 30))
                    report_progress("rendering", f"正在处理第 {i + 1} 页", dynamic_progress)
                else:
                    dynamic_progress = min(90, 60 + int((i / total_images) * 25))
                    report_progress("rendering", f"正在处理第 {i + 1}/{total_images} 页", dynamic_progress)
                image_path = os.path.join(temp_dir, f"{i}.png")

                if safe_save_and_close_image(im, image_path):
                    logger.info(f"Image {i} saved successfully")
                else:
                    logger.error(f"Failed to save image {i}")

                del im

                if is_preview:
                    with open(image_path, "rb") as f:
                        image_data = f.read()

                    if full_preview == "false":
                        safe_remove_directory(temp_dir)
                        report_progress("finalizing", "正在返回预览结果", 100)
                        return Response(
                            content=image_data,
                            media_type="image/png",
                        )

                    base64_str = base64.b64encode(image_data).decode("utf-8")
                    preview_images_base64.append(base64_str)

            if is_preview:
                safe_remove_directory(temp_dir)
                report_progress("finalizing", "正在返回预览结果", 100)
                return JSONResponse({"status": "success", "images": preview_images_base64})

            if not is_preview:
                report_progress("packaging", "正在打包ZIP文件", 92)
                shutil.make_archive(zip_path[:-4], "zip", temp_dir)

                try:
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()
                    safe_remove_file(zip_path)
                    report_progress("finalizing", "正在返回ZIP结果", 100)
                    response = Response(
                        content=zip_data,
                        media_type="application/zip",
                        headers={"Content-Disposition": "attachment; filename=images.zip"},
                    )
                except Exception as e:
                    logger.error(f"Failed to read ZIP file: {e}")
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()
                    report_progress("finalizing", "正在返回ZIP结果", 100)
                    response = Response(
                        content=zip_data,
                        media_type="application/zip",
                        headers={"Content-Disposition": "attachment; filename=images.zip"},
                    )
            return response
        finally:
            safe_remove_directory(temp_dir)
    else:
        logger.info("PDF generate")
        temp_pdf_file_path = None
        report_progress("rendering", "正在生成手写图像", 45)
        images = handwrite(text_to_generate, template)
        try:
            report_progress("packaging", "正在导出PDF文件", 92)
            temp_pdf_file_path = generate_pdf(images=images)
            with open(temp_pdf_file_path, "rb") as f:
                pdf_data = f.read()
            report_progress("finalizing", "正在返回PDF结果", 100)
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=images.pdf"},
            )
        finally:
            if temp_pdf_file_path is not None and os.path.exists(temp_pdf_file_path):
                safe_remove_file(temp_pdf_file_path)


async def run_generation_task(task_id, base_url, payload):
    """
    后台执行手写生成任务。

    - 用 asyncio.to_thread() 把 CPU 密集的 handwrite() 消费循环
      移到线程池，避免阻塞事件循环（WebSocket 推送卡顿问题）。
    - progress_notify 通过 run_coroutine_threadsafe 跨线程安全推送进度。
    """
    logger.info("run_generation_task START, task_id=%s", task_id)
    loop = asyncio.get_event_loop()

    def progress_notify(**kwargs):
        """线程安全的进度通知。"""
        set_generation_task(task_id, **kwargs)
        asyncio.run_coroutine_threadsafe(push_task_status_update(task_id), loop)

    set_generation_task(
        task_id,
        status="processing",
        stage="started",
        message="任务已开始",
        progress=1,
    )
    await push_task_status_update(task_id)

    try:
        async with _generation_semaphore:
            set_generation_task(task_id, stage="executing", message="正在生成中")
            await push_task_status_update(task_id)

            response = await asyncio.to_thread(
                generate_handwriting_impl,
                base_url=base_url,
                progress_hook=progress_notify,
                **payload,
            )

        # 检查是否为错误响应（非 2xx）
        if not (200 <= response.status_code < 300):
            try:
                body_text = response.body.decode("utf-8") if response.body else ""
                err_data = json.loads(body_text)
                err_msg = err_data.get("message", body_text)
            except Exception:
                err_msg = f"生成失败 (HTTP {response.status_code})"
            set_generation_task(
                task_id,
                status="failed",
                error_message=err_msg,
                stage="failed",
                message="任务处理失败",
            )
            await push_task_status_update(task_id)
            return

        # 成功路径
        response_body = response.body if response.body is not None else b""
        response_headers = {}
        if "content-disposition" in response.headers:
            response_headers["Content-Disposition"] = response.headers["content-disposition"]
        set_generation_task(
            task_id,
            status="completed",
            response_status_code=response.status_code,
            response_content_type=response.headers.get("content-type")
            or response.media_type
            or "application/octet-stream",
            response_headers=response_headers,
            response_body=response_body,
            stage="completed",
            message="任务处理完成",
            progress=100,
        )
        await push_task_status_update(task_id)
    except Exception as e:
        logger.exception("Generation task failed, task_id=%s", task_id)
        set_generation_task(
            task_id,
            status="failed",
            error_message=str(e),
            stage="failed",
            message="任务处理失败",
        )
        await push_task_status_update(task_id)
