# app_pdf.py
import os, base64, fitz, io
from PIL import Image
import gradio as gr
from gradio_pdf import PDF
from openai import OpenAI
from pathlib import Path

VLLM_BASE   = os.getenv("VLLM_API_BASE", "http://10.127.153.69:8000/v1/")
VLLM_APIKEY = os.getenv("VLLM_API_KEY",  "dummy")
MODEL_ID    = os.getenv("MODEL_ID",      "Qwen/Qwen3.5-9B")

client = OpenAI(base_url=VLLM_BASE, api_key=VLLM_APIKEY)

def pdf_to_images_b64(pdf_path: str, max_pages: int = 1, dpi: int = 160, max_side: int = 1800):
    """
    将 PDF 的前 max_pages 页渲染为 PNG，并限制最长边到 max_side，返回 [(mime, b64), ...]
    """
    images = []
    with fitz.open(pdf_path) as doc:
        pages = min(len(doc), max_pages)
        for i in range(pages):
            page = doc[i]
            # DPI -> 缩放矩阵
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 可选：限制分辨率，避免图片过大
            w, h = img.size
            scale = min(1.0, max_side / max(w, h))
            if scale < 1.0:
                img = img.resize((int(w*scale), int(h*scale)), Image.BICUBIC)

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
            images.append(("image/png", b64))
    return images

def ask_about_pdf(pdf_file,  max_pages, dpi, sign_or_not,date_or_not):
    question = "请检查如上图纸。"
    if pdf_file is None:
        return "请先上传 PDF。"
    if not question.strip():
        question = "请根据这些页面提取要点并给出结构化摘要。"

    # 1) PDF -> 多张图片（data URL）
    img_items = []
    for mime, b64 in pdf_to_images_b64(pdf_file.name, max_pages=max_pages, dpi=dpi):
        img_items.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"}
        })
    sign_or_not="右下角标题栏中签名框" + sign_or_not
    date_or_not="右下角标题栏Date框"+date_or_not
    question=f"{question}{sign_or_not}{date_or_not}"
    if not img_items:
        return "未能从 PDF 渲染出页面，请确认PDF是否加密/损坏。"

    # 2) 组装多模态消息（图片 + 文本）
    content = img_items + [{"type": "text", "text": question}]

    # 3) 调用 vLLM (OpenAI 兼容) 的 /v1/chat/completions
    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
                    {
                        "role": "system",
                        "content": "你是一个设计图纸审阅检查的专家。目标：你需要根据设计要求检查图纸，并最终给出图纸的检查结论。"
                                   "设计要求：1.除了右下角标题栏外，其他区域的中文使用仿宋_GB2312，英文每个字母都使用大写，字体为：仿宋_GB2312。需检查是否有中文错别字以及英文拼写是否正确。"
                                   "2.图纸右下角的标题栏中Drawing号，若是D3开头检查是否是9位数字，若是D8开头检查是否满足10位数字。标题栏日期若有的话，格式为：YYYY-MM-DD。例如：2025-06-18。Change notice的格式为ECO_xx_xxxxxxx,x为数字。标题栏中是否有中英对照的零部件名称两行文本，上方第一行为中文，下方第二行为英文，英文不需要全大写，只需要单词首字母大写。format必须为A3或者A4。标题栏中文使用仿宋_GB2312，英文使用Tahoma字体。"
                                   "约束：不得臆测；不确定的地方就不进行输入；只输出与能够正确判断的相关内容；如需列表请用 Markdown。"
                      },
                      {
                        "role": "user",
                        "content": content
                      }
                    ]
    )
    return resp.choices[0].message.content

def to_pdf_view(file):
    """把 File 组件的返回值转换成 gr.PDF 可用的路径，并回显状态"""
    if not file:
        return None, "尚未选择文件"

    path = None
    # 兼容多种返回类型：dict、str、FileData等
    if isinstance(file, dict):
        path = file.get("name") or file.get("path")
    elif isinstance(file, str):
        path = file
    elif hasattr(file, "name"):
        path = file.name

    if path and Path(path).suffix.lower() == ".pdf" and Path(path).exists():
        return path, f"✅ 已加载：{Path(path).name}"
    return None, "❌ 不是有效的 PDF 或文件不存在"

with gr.Blocks(title="Qwen‑VL + vLLM：PDF 识图问答") as demo:
    gr.Markdown("### 上传图纸 PDF（图片/扫描件）进行格式检查 Powered by Qwen‑VL")
    with gr.Row():
        pdf = gr.File(label="上传 PDF", file_types=[".pdf"], type="filepath")
      #  q   = gr.Textbox(label="你的问题", lines=3, value="请逐页提炼要点，给出摘要和清单。")
        out = gr.Textbox(label="模型回答", lines=10)
    with gr.Row():
        max_pages = gr.Slider(1, 12, value=1, step=1, label="处理页数上限")
        dpi       = gr.Slider(96, 240, value=160, step=8, label="渲染 DPI（越高越清晰也越占内存）")
    with gr.Row():
        sign_or_not=gr.Dropdown(
            choices=["不需要签名", "需要签名"],
            value="不需要签名",  # 默认值（必须在 choices 内）
            label="选择是否需要签名",
            type="value"  # 默认就是 "value"，返回字符串本身
            )
        date_or_not=gr.Dropdown(
            choices=["不需要日期", "需要日期"],
            value="不需要日期",  # 默认值（必须在 choices 内）
            label="选择是否需要日期",
            type="value"  # 默认就是 "value"，返回字符串本身
            )


    run = gr.Button("开始分析")
    #out = gr.Textbox(label="模型回答", lines=16)

    status = gr.Markdown()
    preview = PDF(label="PDF 预览", height=740)  # 可调高度
    pdf.upload(fn=to_pdf_view, inputs=pdf, outputs=[preview, status])

    run.click(fn=ask_about_pdf, inputs=[pdf, max_pages, dpi,sign_or_not,date_or_not], outputs=out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
