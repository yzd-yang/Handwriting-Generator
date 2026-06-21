"""
文档处理工具：docx/PDF 读取、段落排版预处理。

从 app.py 中拆分出来（P1 2.4 重构）。
"""

import re

import pypandoc
import PyPDF2
from docx import Document

from utils.logging_setup import get_logger

logger = get_logger(__name__)


def read_docx(file_path):
    """读取 .docx 文件的纯文本内容。"""
    document = Document(file_path)
    text = " ".join([paragraph.text for paragraph in document.paragraphs])
    return text


def convert_docx_to_text(docx_file_path):
    """将 .docx 转为 HTML 文本（用于前端展示和解析段落格式）。"""
    text = pypandoc.convert_file(docx_file_path, "html", format="docx")
    m_body = re.search(r"<body[^>]*>(.*?)</body>", text, re.DOTALL | re.IGNORECASE)
    if m_body:
        text = m_body.group(1)
    text = re.sub(r"</?html[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?head[^>]*>.*?</head>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<title[^>]*>.*?</title>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def apply_paragraph_layout(text, data, font, box_width):
    """对送入 handwrite() 的文本做段落排版预处理。

    handright 是逐字符流式布局，每行起点 x=left_margin 固定、遇 \\n 换行无段间距，
    原生不支持首行缩进 / 居中 / 右对齐 / 段间距。这里在渲染前对纯文本做转换：
      - 首行缩进：每段首行前插 N 个全角空格「　」
      - 段间距：段与段之间插入指定数量的空行
      - 居中 / 右对齐：用 PIL 离屏测量每行像素宽，在行首前置空格把内容"推"到中间或右侧

    Args:
        text: 原始文本
        data: 表单参数 dict
        font: PIL ImageFont 实例（用于测量宽度）
        box_width: 单行可用像素宽 = 画面宽 - 左边距 - 右边距
    """
    layout = data.get("paragraph_layout", "default")
    try:
        indent = int(data.get("first_line_indent", "0"))
    except (TypeError, ValueError):
        indent = 0
    try:
        spacing = int(data.get("paragraph_spacing", "0"))
    except (TypeError, ValueError):
        spacing = 0

    # 三项都没启用则原样返回
    if layout == "default" and indent <= 0 and spacing <= 0:
        return text

    full_space = "　"  # 全角空格

    # 全角空格在当前字体下的像素宽
    try:
        full_space_w = font.getlength(full_space)
    except Exception:
        full_space_w = font.size
    if full_space_w <= 0:
        full_space_w = max(font.size, 1)

    # 半角空格像素宽
    try:
        half_space_w = font.getlength(" ")
    except Exception:
        half_space_w = font.size / 2
    if half_space_w <= 0:
        half_space_w = max(font.size / 2, 1)

    def center_or_right_align_line(line):
        """对单行做居中/右对齐的前置空格填充。"""
        if not line.strip():
            return line
        try:
            line_w = font.getlength(line)
        except Exception:
            return line
        if line_w >= box_width:
            return line

        if layout == "center":
            target_pad = (box_width - line_w) / 2
        else:  # right
            target_pad = box_width - line_w

        if target_pad <= 0:
            return line

        n_full = int(target_pad // full_space_w)
        remain = target_pad - n_full * full_space_w
        n_half = int(round(remain / half_space_w))
        if n_half < 0:
            n_half = 0
        return full_space * n_full + " " * n_half + line

    def layout_paragraph(para):
        """处理单个段落：首行缩进 + 对每行做居中/右对齐。"""
        lines = para.split("\n")
        out_lines = []
        for i, ln in enumerate(lines):
            if i == 0 and indent > 0:
                ln = full_space * indent + ln
            if layout in ("center", "right"):
                ln = center_or_right_align_line(ln)
            out_lines.append(ln)
        return "\n".join(out_lines)

    paragraphs = text.split("\n")
    processed = [layout_paragraph(p) for p in paragraphs]

    if spacing > 0:
        gap = "\n" * spacing
        result = gap.join(processed)
    else:
        result = "\n".join(processed)

    return result


def read_pdf(file_path):
    """读取 PDF 文件，返回 HTML 格式的段落文本。"""
    text = ""
    with open(file_path, "rb") as pdf_file_obj:
        pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
        for page_num in range(len(pdf_reader.pages)):
            page_obj = pdf_reader.pages[page_num]
            page_text = page_obj.extract_text()
            if page_text:
                paragraphs = page_text.split("\n\n")
                for para in paragraphs:
                    cleaned = para.strip().replace("\n", " ")
                    if cleaned:
                        text += f"<p>{cleaned}</p>"
    return text if text else ""
