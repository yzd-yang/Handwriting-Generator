"""
图像工具函数：纸张背景生成、颜色转换。

从 app.py 中拆分出来（P1 2.4 重构）。
"""

import colorsys

from PIL import Image, ImageDraw

from utils.logging_setup import get_logger

logger = get_logger(__name__)


def _hex_to_rgb(hex_str):
    """将 #RRGGBB 或 RRGGBB 格式的十六进制颜色转为 (R, G, B) 元组。"""
    if not hex_str or not isinstance(hex_str, str):
        return None
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return None
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return None


def _adjust_color_for_visibility(bg_rgb):
    """根据背景色亮度返回一个保证可见的线/点颜色。

    亮度 > 0.5 → 调暗 30%（白底得淡灰线）；
    亮度 ≤ 0.5 → 调亮 30%（深底得浅色线）。
    """
    r, g, b = [c / 255.0 for c in bg_rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l > 0.5:
        l = max(0.0, l * 0.7)  # 调暗
    else:
        l = min(1.0, l + (1.0 - l) * 0.5 + 0.25)  # 调亮，且至少抬到 0.25 以上
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return (int(nr * 255), int(ng * 255), int(nb * 255))


def create_notebook_image(
    width,
    height,
    line_spacing,
    top_margin,
    bottom_margin,
    left_margin,
    right_margin,
    font_size,
    isUnderlined,
    paper_type="lines",
    paper_color="#FFFFFF",
):
    """创建纸张背景图片（横线/方格/点阵/空白）。"""
    # paper_type 归一：老请求只传 isUnderlined=true 时映射为 lines
    if not paper_type or paper_type not in ("blank", "lines", "grid", "dots"):
        if isinstance(isUnderlined, str):
            need_lines = isUnderlined.lower() == "true"
        else:
            need_lines = bool(isUnderlined)
        paper_type = "lines" if need_lines else "blank"

    # 解析纸张颜色
    bg_rgb = _hex_to_rgb(paper_color) or (255, 255, 255)
    image = Image.new("RGB", (width, height), bg_rgb)

    # blank 直接返回纯色底
    if paper_type == "blank":
        return image

    # lines / grid / dots 需要画线或点，先算线/点颜色
    line_rgb = _adjust_color_for_visibility(bg_rgb)

    draw = ImageDraw.Draw(image)

    # 横线区域
    x_start = left_margin
    x_end = max(left_margin + 1, width - right_margin)
    y_top = top_margin + line_spacing
    y_bottom = height - bottom_margin

    if paper_type == "lines":
        y = y_top
        while y < y_bottom:
            draw.line((x_start, y, x_end, y), fill=line_rgb)
            y += line_spacing
        return image

    if paper_type == "grid":
        y = y_top
        while y < y_bottom:
            draw.line((x_start, y, x_end, y), fill=line_rgb)
            y += line_spacing
        x = x_start
        while x < x_end:
            draw.line((x, y_top, x, y_bottom), fill=line_rgb)
            x += line_spacing
        return image

    if paper_type == "dots":
        r = max(2.0, line_spacing * 0.03)
        y = y_top
        while y < y_bottom:
            x = x_start
            while x < x_end:
                draw.ellipse(
                    (x - r, y - r, x + r, y + r),
                    fill=line_rgb,
                )
                x += line_spacing
            y += line_spacing
        return image

    return image
