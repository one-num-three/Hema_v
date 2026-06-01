---
name: document-formatting
title: 文档排版与格式化
category: productivity
description: 专业的中文文档排版与格式化工具。支持 DOCX、Markdown、TXT 等格式的自动排版——中英文混排加空格、标点符号规范化、段落间距/首行缩进/字体统一、自动生成目录、页眉页脚设置。一键排版即可生成整洁规范的文档。
triggers:
  - 文档排版
  - 格式化文档
  - 排版
  - 文档美化
  - document formatting
  - typesetting
---

# 文档排版与格式化 Skill

## 触发条件

当用户提到以下任何一个时，请加载此 skill：
- "帮我排版这个文档"
- "文档格式化"
- "美化文档"
- "调整格式"
- "中文排版"
- "文档规范"
- 涉及 .docx / .md 文件的格式美化

## 概述

支持三种文档格式的排版处理：
1. **DOCX** (python-docx) — 完整排版：字体、段落、页边距、目录
2. **Markdown** — 清理格式、统一风格、添加目录
3. **纯文本 TXT** — 中英文间距、标点规范、段落重排

## 准备工作

```python
import subprocess, sys

def ensure_package(package_name, import_name=None):
    try:
        if import_name:
            __import__(import_name)
        else:
            __import__(package_name.replace("-", "_"))
    except ImportError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package_name, "-q"
        ])

# 按需安装
ensure_package("python-docx", "docx")
```

## 排版规则

### 1. 中英文混排加空格
- 中文与英文之间加空格：`你好World` → `你好 World`
- 中文与数字之间加空格：`你好123` → `你好 123`
- 英文/数字与中文标点之间不加空格：`World。` 保持不变

### 2. 标点符号规范化
- 中文内容使用全角标点（，。！？；：“”‘’（）【】《》——……·）
- 英文内容保持半角标点（, . ! ? ; : " ' ( ) [ ] <>）
- 连续省略号规范化：`......` → `......`（6个点=一个中文省略号）→ `……`
- 破折号规范化：`--` → `—`（em dash），`---` → `——`
- 引号配对检查与修复

### 3. 段落格式
- 首行缩进 2 字符（DOCX：设置 first_line_indent）
- 段落间距：段前 0，段后 6pt（约0.5行）
- 行距：1.5 倍或固定 22pt
- 标题与正文间距适当加大

### 4. 字体规范
- 正文：中文用宋体/思源宋体，英文用 Times New Roman，字号 12pt（小四）
- 标题1：黑体/思源黑体，18pt（小二），加粗
- 标题2：黑体，15pt（小三），加粗
- 标题3：黑体，13pt（四号），加粗
- 代码/等宽内容：Consolas / 等线，10pt

### 5. 页面设置
- A4 纸张（210mm × 297mm）
- 页边距：上下 2.54cm，左右 3.17cm（Word 默认）
- 页眉 1.5cm，页脚 1.75cm

## 核心函数

### 函数1: format_chinese_text(text: str) -> str
对纯文本执行中文排版规则：
- 中英文之间加空格
- 中文与数字之间加空格
- 全角/半角标点规范化
- 连续符号规范化

```python
import re

def format_chinese_text(text: str) -> str:
    # 1. 中文与英文之间加空格
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])([\u4e00-\u9fff])', r'\1 \2', text)

    # 2. 中文与数字之间加空格
    text = re.sub(r'([\u4e00-\u9fff])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([\u4e00-\u9fff])', r'\1 \2', text)

    # 3. 全角英文字母转半角（中文文本中的全角英文）
    text = re.sub(r'[\uff41-\uff5a]', lambda m: chr(ord(m.group(0)) - 0xfee0), text)  # 全角小写→半角
    text = re.sub(r'[\uff21-\uff3a]', lambda m: chr(ord(m.group(0)) - 0xfee0), text)  # 全角大写→半角

    # 4. 全角数字转半角
    text = re.sub(r'[\uff10-\uff19]', lambda m: chr(ord(m.group(0)) - 0xfee0), text)

    # 5. 连续点号→中文省略号
    text = re.sub(r'\.{6,}', '……', text)
    text = re.sub(r'。{2,}', '……', text)

    # 6. 连续破折号→中文破折号
    text = re.sub(r'-{3,}', '——', text)
    text = re.sub(r'—{2,}', '——', text)

    # 7. 去除多余空格（中文内部的空格）
    text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)

    # 8. 中文后跟英文标点→中文标点
    punct_map = {
        ',': '，', '.': '。', '?': '？', '!': '！',
        ':': '：', ';': '；'
    }
    for eng, chn in punct_map.items():
        text = re.sub(f'([\u4e00-\u9fff]){re.escape(eng)}', rf'\1{chn}', text)

    return text.strip()
```

### 函数2: format_docx(input_path: str, output_path: str = None)
对 DOCX 文件执行完整排版：
- 设置默认字体（中/英文分开）
- 统一段落格式（首行缩进、行距、段间距）
- 标题样式美化
- 页面设置（纸张、边距）
- 添加自动目录（可选）

### 函数3: format_markdown(input_path: str, output_path: str = None)
对 Markdown 文件：
- 中英文排版规则
- 统一标题层级
- 添加 TOC 目录（可选）
- 代码块美化
- 表格对齐

### 函数4: extract_and_format(path: str) -> str
读取文件、排版、输出格式化后的文本内容。

## 完整排版脚本 (DOCX)

```python
from docx import Document
from docx.shared import Pt, Cm, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re

def full_format_docx(input_path: str, output_path: str = None):
    doc = Document(input_path)
    if not output_path:
        output_path = input_path.replace('.docx', '_排版后.docx')

    # 设置默认字体
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 设置页面
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # 处理每个段落
    for para in doc.paragraphs:
        # 应用中文排版规则到文本
        for run in para.runs:
            run.text = format_chinese_text(run.text)

        if para.style.name.startswith('Heading'):
            # 标题：加大字号、加粗、取消缩进
            para.paragraph_format.first_line_indent = Pt(0)
            para.paragraph_format.space_before = Pt(18)
            para.paragraph_format.space_after = Pt(12)
            para.paragraph_format.line_spacing = 1.5
            level = para.style.name.replace('Heading ', '')
            size_map = {'1': Pt(22), '2': Pt(16), '3': Pt(14)}
            for run in para.runs:
                run.bold = True
                run.font.size = size_map.get(level, Pt(14))
        else:
            # 正文：首行缩进2字符、合适行距
            para.paragraph_format.first_line_indent = Pt(24)
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = Pt(6)
            para.paragraph_format.line_spacing = 1.5

    doc.save(output_path)
    return output_path
```

## 排版 Markdown 脚本

```python
import re

def format_markdown(input_path: str, output_path: str = None):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not output_path:
        output_path = input_path.replace('.md', '_排版后.md')

    # 1. 中英文排版
    lines = content.split('\n')
    formatted_lines = []
    in_code_block = False

    for line in lines:
        # 不处理代码块内的内容
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            formatted_lines.append(line)
            continue

        if in_code_block:
            formatted_lines.append(line)
            continue

        # 不处理标题行、列表项、表格
        if line.strip().startswith(('#', '-', '*', '>', '|', '1.', '2.')):
            formatted_lines.append(line)
            continue

        formatted_lines.append(format_chinese_text(line))

    result = '\n'.join(formatted_lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    return output_path
```

## 注意事项
- 处理 DOCX 前先备份原文件
- 中文排版对技术文档（含大量代码）需要跳过代码块
- 表格和列表中的内容也应用中英文间距规则
- 如果用户有特殊字体要求，优先使用用户指定的字体
