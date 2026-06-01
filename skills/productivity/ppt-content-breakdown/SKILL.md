---
name: ppt-content-breakdown
description: Break a complex topic into a clear, narrative, presentation-ready PPT page outline before visual generation. Use when users ask for PPT内容主题拆解, PPT大纲, 拆页, 演讲页结构, slide-by-slide planning, story flow, or preparing pages before calling ppt-page-image-grsai. After the outline is approved, hand off to ppt-page-image-grsai to ask for aspect ratio/model and generate page images with Grsai.
---

# PPT Content Theme Breakdown

Use this skill before generating PPT visuals. Its job is to decide what the deck should say, how many pages it needs, what each page contributes to the story, and what visual/material slots each page needs.

Do not generate final images in this skill. After the user approves the page outline, load and follow `ppt-page-image-grsai` to ask for the generation model and aspect ratio/size, then start page-by-page image generation.

## Required Inputs

Collect or infer these fields before producing the final outline. If several are missing, ask a concise question; if enough context exists, make reasonable assumptions and label them.

```text
PPT总主题：
目标听众：
演讲时长：
核心目的：
已有素材：
必须出现的关键词：
希望观众最后记住的一句话：
整体语气：
是否需要产品介绍：
是否需要案例展示：
是否需要未来展望：
```

Example:

```text
PPT总主题：河马与安装实战
目标听众：技术分享会观众
演讲时长：15分钟
核心目的：说明 Hermes / 河马如何通过 Agent 和 Skill 完成真实任务
已有素材：聊天截图、知识图谱截图、安装实战页面、内容产出页面
必须出现的关键词：Agent、Skill、SOP、本地场景服务、多源信息聚合、内容产出、All for AI
希望观众最后记住的一句话：Hermes 是接触 Agent 集群的最好入口
整体语气：科技感、实战感、未来感
```

## Core Principles

### One Page, One Point

Each page carries one core idea. If a page must explain a concept, show a case, and explain technical mechanism at the same time, split it.

### Narrative First, Materials Second

PPT is not a pile of assets. Split the deck according to the audience's understanding path:

```text
问题背景 -> 核心概念 -> 产品能力 -> 真实案例 -> 运行机制 -> 价值总结 -> 未来展望
```

### Time-To-Page Heuristic

```text
5分钟：3到5页
10分钟：6到8页
15分钟：8到12页
20分钟：12到16页
30分钟：18到24页
```

For launch-event style decks, page count may be higher and information per page should be lighter.

### Page Role Before Layout

First classify each page:

```text
开场页 / 问题页 / 概念页 / 能力页 / 案例页 / 机制页 / 对比页 / 总结页 / 展望页 / 收尾页
```

Then choose layout:

```text
并列内容 -> 左右分栏
逻辑 + 案例 -> 上下分段
核心主体 + 多功能 -> 总分式
流程拆解 -> 流程式
趋势升华 -> 递进式
```

Use these layout names when preparing handoff to `ppt-page-image-grsai`:

```text
左右分栏 -> split
上下分段 -> stacked
总分式 -> hub-and-spoke
递进式 -> progressive
流程式 -> workflow
```

## Breakdown Workflow

### Step 1: Extract Theme Keywords

Output this compact analysis:

```text
核心对象：
核心动作：
核心价值：
核心证据：
核心机制：
最终结论：
```

### Step 2: Sort Content Into Five Buckets

```text
1. 背景问题：现在为什么需要这个东西？
2. 核心能力：它能做哪些事情？
3. 真实案例：它实际完成过什么任务？
4. 运行机制：它背后如何工作？
5. 未来判断：它代表什么趋势？
```

### Step 3: Decide Page Count Per Bucket

Default:

```text
背景问题：1页
核心能力：2到4页
真实案例：1到3页
运行机制：1到2页
未来判断：1到2页
```

If the user has many assets, add case pages before adding concept pages.

### Step 4: Produce A Page Structure Table

Every row must include:

```text
页码
页面标题
页面角色
核心观点
主要内容
建议版式
建议视觉元素
与上一页的衔接关系
```

Final table format:

```text
| 页码 | 标题 | 页面角色 | 核心观点 | 建议版式 | 需要素材 | 视觉重点 |
```

After the table, add:

```text
推荐总页数：
推荐演讲节奏：
哪些页必须保留：
哪些页可以删减：
哪些页适合做重点视觉页：
```

## Page Count Presets

### Lightweight: 5-6 Pages

Use for short sharing or quick roadshows.

```text
1. 首页：主题与身份
2. 背景：为什么需要 Agent / Skill
3. 核心能力：河马能做什么
4. 案例展示：安装实战或内容产出
5. 机制说明：Agent + Skill + SOP 如何协作
6. 收尾展望：All for AI / Hermes 入口
```

### Standard: 8-10 Pages

Use for a complete 10-15 minute talk.

```text
1. 首页：河马与安装实战
2. 背景：AI 从聊天工具变成提效工具
3. 核心概念：Skill 是能力单元，Agent 是调度者
4. 本地场景服务：系统、环境、文件、数据处理
5. 多源信息聚合：外部资讯 + 内部记忆
6. 内容产出案例：学习内容、知识图谱、推荐
7. 多元内容生成：PPT、图片、视频、漫剧等
8. 运行机制：主 Agent 拆分任务，子 Agent 分工执行
9. SOP 与递归迭代：从一次任务到可复用流程
10. 未来展望：All for AI，Hermes 是 Agent 集群入口
```

### Full: 12-15 Pages

Use for formal launches or deeper technical sharing.

```text
1. 首页：主题、主讲人、公司身份
2. 开场问题：为什么现在需要新的智能体入口
3. 趋势判断：AI 正从聊天搜索走向任务执行
4. 核心概念：Agent、Skill、SOP 的关系
5. Skill 能力单元：每个 Skill 解决一个具体任务
6. 本地场景服务：环境部署、系统优化、文件处理
7. 安装实战案例：从需求到执行结果
8. 多源信息聚合：外部行情资讯与内部记忆管理
9. 内容产出案例：每日学习内容推荐
10. 知识图谱案例：从笔记到结构化知识网络
11. 多元内容生成：PPT、图片、动画、漫剧
12. 多 Agent 协作机制：主 Agent 拆任务，子 Agent 执行
13. 递归迭代机制：复杂任务如何逐步完成
14. 未来展望：信息分为给人看的和给 AI 看的
15. 收尾页：All for AI，Hermes 是接触 Agent 集群的最好入口
```

## Add Or Merge Pages

Add a page when:

```text
一个页面有两个以上核心观点
一页同时放概念、案例、机制
截图太多导致说明被压缩
某个案例需要讲完整过程
某个概念观众不熟
收尾观点很重要，需要独立升华
```

Merge pages when:

```text
两页重复解释同一能力
某页没有独立观点
案例截图不足以独立成页
机制过细，观众不需要
演讲时间不足
```

## Single Page Breakdown Template

Use this template internally for each page:

```text
页码：
页面标题：
页面角色：
本页一句话观点：
观众看完这一页应该明白：
主要内容：
建议版式：
建议视觉元素：
是否需要截图：
是否需要流程：
是否需要案例：
本页和上一页的衔接：
本页引向下一页：
```

## User Review Gate

After outputting the full outline, stop and ask the user to verify the structure before image generation.

Use wording like:

```text
你先确认一下这个拆页结构：页数、顺序、重点页和删减页是否合适？如果没问题，我下一步会调用 `ppt-page-image-grsai`，先问你生成模型和比例/尺寸，然后开始逐页生图。
```

Do not call Grsai or generate images before the user approves the outline.

## Handoff To Image Generation Skill

After the user approves, load and follow `ppt-page-image-grsai`. If the user has not specified them, ask:

```text
1. 生成模型用 `gpt-image-2` 还是 `gpt-image-2-vip`？
2. PPT比例/尺寸用什么？推荐 `16:9 / 3840x2160`；如果想省成本可用 `2048x1152`。
```

For each page, hand off this structure:

```text
本页标题：
页面角色：
核心观点：
页面布局：
主要内容：
需要素材：
截图占位：
视觉重点：
生成图像要求：
```

Map the Chinese layout to the image skill's layout:

```text
左右分栏 -> split
上下分段 -> stacked
总分式 -> hub-and-spoke
递进式 -> progressive
流程式 -> workflow
```

After all page images are generated, load `ppt-image-deck-assembler` to create the final output folder:

```text
final/
  <deck-name>.pptx
  images/
    001_...
    002_...
```

## Quality Checklist

Before asking for user approval, check:

```text
□ 是否有明确开场
□ 是否有问题背景
□ 是否解释核心概念
□ 是否展示真实案例
□ 是否讲清运行机制
□ 是否有未来展望
□ 是否有强收尾
□ 每页是否只有一个核心观点
□ 页面顺序是否符合观众理解路径
□ 是否避免素材堆叠
□ 是否能顺畅讲成一个故事
```

## Core Principle

Do not average materials across pages. Turn the audience's understanding path into a sequence of cognitive steps, where each slide has one clear narrative job.
