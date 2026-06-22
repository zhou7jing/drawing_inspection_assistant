# 📄 Drawing Inspection Assistant (PDF)

**Powered by Qwen-VL + vLLM**

## 📌 项目简介

本项目基于 **Qwen-VL 多模态模型 + vLLM 推理服务**，实现一个面向工程图纸的 **PDF 自动检测助手**。

核心能力：

* ✅ 上传 PDF 图纸（扫描件/图片型）
* ✅ 自动解析前 N 页为图像
* ✅ 使用多模态大模型进行检测
* ✅ 输出结构化审查结果

应用场景：

* 工程图纸审核
* 标题栏规范检查
* 字体/格式一致性检查
* Drawing 编号、日期、ECO格式校验

***

## ⚙️ 技术架构

```
Gradio UI
   ↓
PDF → 图片 (PyMuPDF + PIL)
   ↓
Base64 图片输入
   ↓
vLLM (OpenAI API 兼容)
   ↓
Qwen-VL 多模态推理
   ↓
结构化文本输出
```

***

## 📦 依赖安装

```bash
pip install -r requirements.txt
```

**核心依赖：**

```txt
gradio
gradio-pdf
pymupdf
pillow
openai
```

***

## 🚀 启动方式

```bash
python app_pdf.py
```

默认访问地址：

```
http://0.0.0.0:7860
```

***

## 🔧 环境变量配置

```bash
export VLLM_API_BASE=http://your-vllm-server:8000/v1
export VLLM_API_KEY=dummy
export MODEL_ID=Qwen/Qwen3.5-9B
```

说明：

| 变量              | 描述             |
| --------------- | -------------- |
| `VLLM_API_BASE` | vLLM 服务地址      |
| `VLLM_API_KEY`  | API Key（任意值即可） |
| `MODEL_ID`      | 使用的模型          |

***

## 🧠 功能说明

### 1️⃣ PDF → 图像转换

函数：

```python
pdf_to_images_b64()
```

功能：

* 将 PDF 转为 PNG 图像
* 支持 DPI 控制清晰度
* 自动限制最大分辨率（避免 OOM）
* 输出 base64 编码

***

### 2️⃣ 图纸检测逻辑

核心函数：

```python
ask_about_pdf()
```

执行流程：

1. PDF 转图片
2. 拼接多模态输入（图片 + 文本）
3. 调用 vLLM API
4. 返回模型检测结果

***

### 3️⃣ 检测规则（模型提示词核心）

模型被约束执行以下检查：

#### ✅ 字体规范

* 中文：仿宋\_GB2312
* 英文：全大写 + 仿宋\_GB2312

#### ✅ 标题栏规则

* Drawing号：
  * D3 → 9位数字
  * D8 → 10位数字
* 日期格式：
  ```
  YYYY-MM-DD
  ```
* ECO格式：
  ```
  ECO_xx_xxxxxxx
  ```

#### ✅ 双语规范

* 中文在上
* 英文在下
* 英文首字母大写（非全大写）

#### ✅ 图幅格式

* A3 / A4

#### ⚠️ 输出约束

* 不允许猜测
* 不确定不输出
* 使用 Markdown 列表

***

## 🖥️ 前端功能（Gradio）

### 页面组件：

| 组件    | 功能     |
| ----- | ------ |
| PDF上传 | 支持图纸上传 |
| PDF预览 | 可视化查看  |
| 页数控制  | 限制处理页  |
| DPI控制 | 控制图像质量 |
| 签名选项  | 是否要求签名 |
| 日期选项  | 是否要求日期 |
| 输出框   | 模型检测结果 |

***

## ✅ 参数说明

| 参数            | 作用     |
| ------------- | ------ |
| `max_pages`   | 最大处理页数 |
| `dpi`         | 渲染清晰度  |
| `sign_or_not` | 是否检测签名 |
| `date_or_not` | 是否检测日期 |

***

## 📊 示例输入

* PDF图纸文件
* 选择：
  * ✅ 需要签名
  * ✅ 需要日期

***

## 📊 示例输出

```markdown
- 标题栏 Drawing 号格式正确
- 日期格式错误，应为 YYYY-MM-DD
- 存在英文拼写错误："VALVE" -> "VALUE"
- 未发现签名
```

***

## ⚠️ 注意事项

* 仅适用于 **扫描类PDF / 图片PDF**
* 对矢量PDF效果有限
* 分辨率过高会影响性能
* vLLM 服务必须可访问

***

## 🧩 可扩展方向

### ✅ 功能增强

* 多页对比检查
* CAD 原生支持
* OCR 预处理增强

### ✅ 工程优化

* 批量处理
* 结果结构化 JSON 输出
* 报告导出（Word / PDF）

### ✅ AI能力升级

* Fine-tune 专属图纸模型
* 增加行业规范规则库

***

