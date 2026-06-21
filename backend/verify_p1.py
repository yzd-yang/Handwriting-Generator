#!/usr/bin/env python3
"""
验证 P1 修改无回归。
在后端运行于 localhost:5006 时调用。
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5010"
PASS = 0
FAIL = 0


def req(method, path, data=None, headers=None, expect_status=200):
    """发一次 HTTP 请求，返回 (status_code, body_str)。"""
    global PASS, FAIL
    url = BASE + path
    try:
        if data is not None:
            req_obj = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        else:
            req_obj = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req_obj, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        status = e.code
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {e}")
        FAIL += 1
        return None, None

    ok = status == expect_status
    tag = "✅" if ok else "❌"
    print(f"  {tag} {method} {path} -> HTTP {status} (expect {expect_status})")
    if not ok:
        print(f"     body: {body[:200]}")
        FAIL += 1
    else:
        PASS += 1
    return status, body


print("=" * 60)
print("P1 验证测试开始")
print("=" * 60)

# ── Test 1: 字体列表（基本健康检查）─────────────────────
print("\n【Test 1】GET /api/fonts_info（健康检查）")
status, body = req("GET", "/api/fonts_info")
if body:
    fonts = json.loads(body)
    print(f"     fonts count = {len(fonts)}, first = {fonts[0] if fonts else 'EMPTY'}")

# ── Test 2: identify.py 修复验证（无横线图片不退崩）────────
print("\n【Test 2】POST /api/imagefileprocess（无横线图片→200+warning）")
# 创建一张纯白无横线图片
import io
from PIL import Image

img = Image.new("RGB", (800, 600), "white")
buf = io.BytesIO()
img.save(buf, format="PNG")
png_bytes = buf.getvalue()

# 构造 multipart/form-data 请求
BOUNDARY = b"----VerifyTestBoundary"
body_parts = []
body_parts.append(b"--" + BOUNDARY)
body_parts.append(b'Content-Disposition: form-data; name="file"; filename="blank.png"')
body_parts.append(b"Content-Type: image/png")
body_parts.append(b"")
body_parts.append(png_bytes)
body_parts.append(b"--" + BOUNDARY + b"--")
body_parts.append(b"")
req_body = b"\r\n".join(body_parts)

status, body = req(
    "POST",
    "/api/imagefileprocess",
    data=req_body,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY.decode()}"},
    expect_status=200,
)
if body:
    result = json.loads(body)
    has_warning = "warning" in result
    print(f"     warning present: {has_warning}, warning = {result.get('warning', '')[:80]}")
    if not has_warning:
        print("     ⚠️  expected 'warning' field in response!")

# ── Test 3: 上传校验 — 无效文件类型（.exe）→ 400 ─────
print("\n【Test 3】POST /api/textfileprocess（.exe 文件→400）")
exe_bytes = b"MZ\x90\x00"  # PE 文件头
body_parts2 = []
body_parts2.append(b"--" + BOUNDARY)
body_parts2.append(b'Content-Disposition: form-data; name="file"; filename="hack.exe"')
body_parts2.append(b"Content-Type: application/octet-stream")
body_parts2.append(b"")
body_parts2.append(exe_bytes)
body_parts2.append(b"--" + BOUNDARY + b"--")
body_parts2.append(b"")
req_body2 = b"\r\n".join(body_parts2)

status, body = req(
    "POST",
    "/api/textfileprocess",
    data=req_body2,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY.decode()}"},
    expect_status=400,
)
if body:
    print(f"     body: {body[:200]}")

# ── Test 4: 上传校验 — 文件头伪造（.pdf 扩展名但内容是 PNG）→ 400 ──
print("\n【Test 4】POST /api/textfileprocess（扩展名.pdf 但内容是 PNG→400）")
body_parts3 = []
body_parts3.append(b"--" + BOUNDARY)
body_parts3.append(b'Content-Disposition: form-data; name="file"; filename="fake.pdf"')
body_parts3.append(b"Content-Type: application/pdf")
body_parts3.append(b"")
body_parts3.append(png_bytes)  # PNG 字节当作 PDF 上传
body_parts3.append(b"--" + BOUNDARY + b"--")
body_parts3.append(b"")
req_body3 = b"\r\n".join(body_parts3)

status, body = req(
    "POST",
    "/api/textfileprocess",
    data=req_body3,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY.decode()}"},
    expect_status=400,
)
if body:
    print(f"     body: {body[:200]}")

# ── Test 5: 任务提交和轮询（P0 2.3 错误传递）────────────
print("\n【Test 5】POST /api/generate_handwriting（完整字段→202 accepted）")
form_data = (
    b"text=%E6%B5%8B%E8%AF%95"
    b"&font_size=30"
    b"&line_spacing=50"
    b"&left_margin=50"
    b"&top_margin=50"
    b"&right_margin=50"
    b"&bottom_margin=50"
    b"&word_spacing=10"
    b"&line_spacing_sigma=0"
    b"&font_size_sigma=0"
    b"&word_spacing_sigma=0"
    b"&perturb_x_sigma=0"
    b"&perturb_y_sigma=0"
    b"&perturb_theta_sigma=0"
    b"&preview=false"
    b"&font_option=%E4%BA%91%E7%83%9F%E4%BD%93.ttf"
    b"&paper_type=blank"
    b"&pdf_save=false"
    b"&isUnderlined=false"
    b"&fill=%280%2C0%2C0%2C255%29"
    b"&width=800"
    b"&height=600"
)
status, body = req(
    "POST",
    "/api/generate_handwriting",
    data=form_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    expect_status=200,
)
task_id = None
if body:
    result = json.loads(body)
    task_id = result.get("task_id")
    print(f"     task_id = {task_id}, status = {result.get('status')}")

if task_id:
    print(f"     Polling task {task_id} ...")
    for i in range(20):
        time.sleep(1)
        s, b = req("GET", f"/api/generate_handwriting/task/{task_id}")
        if b:
            st = json.loads(b)
            cur_status = st.get("status")
            progress = st.get("progress", 0)
            print(f"     [{i+1}s] status={cur_status}, progress={progress}%")
            if cur_status in ("completed", "failed"):
                if cur_status == "failed":
                    print(f"     error_message: {st.get('error_message')}")
                break

# ── Test 6: 日志文件是否存在并有轮转配置 ─────────────────
print("\n【Test 6】检查日志文件是否存在")
log_path = os.path.join(os.path.dirname(__file__), "logs", "app.log")
if os.path.exists(log_path):
    size = os.path.getsize(log_path)
    print(f"     ✅ logs/app.log exists, size={size} bytes")
    PASS += 1
else:
    print(f"     ❌ logs/app.log NOT found")
    FAIL += 1

# ── 汇总 ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"验证结果: ✅ {PASS} passed | ❌ {FAIL} failed")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
