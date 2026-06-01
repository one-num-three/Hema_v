---
name: ppt-page-image-grsai
description: Use Grsai image generation to create unified, page-by-page PPT visuals. Trigger when users ask for PPT逐页生图, PPT页面视觉生成, product-launch style slide images, unified deck visuals, 16:9 4K PPT image prompts, or Grsai/gpt-image-2 slide background generation. Always ask for aspect ratio/size and generation model before calling Grsai if they are missing.
---

# PPT Page Image Generation with Grsai

Use this skill to generate a coherent set of PPT page visuals with Grsai. The goal is not a single pretty image; the goal is a deck that looks like one product launch, one narrative system, and one brand language.

If the user asks low-level Grsai API questions, also load `grsai-api`.

If the user provides only a broad PPT topic and has not approved a page-by-page outline yet, load `ppt-content-breakdown` first. Generate images only after the user confirms the outline, page order, and emphasis.

## Required Choices

Before generating, confirm these two choices if the user has not already provided them:

- **Generation model**: `gpt-image-2` or `gpt-image-2-vip`
- **Aspect ratio / size**: recommend `16:9` for PPT; use `3840x2160` for 4K when using `gpt-image-2-vip`, otherwise use `2048x1152` or the user's requested size

Also collect or infer:

```text
PPT topic:
Page title:
Page purpose: overview / section / case / mechanism / workflow / closing
Page layout: split / stacked / hub-and-spoke / progressive / workflow
Unified visual style:
Core content:
Material slots: phone screenshot / tablet screenshot / case cards / flow nodes / feature modules / product object
Canvas requirement: 16:9, 4K, PPT-ready
```

Use `GRSAI_API_KEY` from the environment. If it is missing, ask the user to set it in `.env` or provide it through the local Hermes setup path. Do not ask the user to paste secrets into a public chat.

## Grsai Defaults

- Domestic base URL: `https://grsai.dakka.com.cn`
- Global base URL: `https://grsaiapi.com`
- Generate endpoint: `POST /v1/api/generate`
- Result endpoint: `GET /v1/api/result?id=<task_id>`
- Authentication: `Authorization: Bearer <API_KEY>`

Prefer the domestic base URL for users in mainland China unless they request the global endpoint.

## Fixed Layer System

Every generated PPT page must follow this four-layer structure:

```text
Layer 1: background base
Layer 2: transparent gradient overlay
Layer 3: foreground content area
Layer 4: independent top title area
```

Rules:

- Keep the main title in a consistent top area.
- Never let foreground modules cover the title.
- Keep enough breathing room around the title.
- Align same-level subtitles and labels.
- Keep repeated cards the same size, radius, shadow, and transparency.
- Favor whitespace over filling the page.

## Unified Style Lock

Start every page prompt with the same style lock. Do not reinvent the style per page.

Default style lock:

```text
Maintain a unified high-end technology launch-event visual language across the whole PPT deck: bright, clean, spacious, floating modules, translucent glass cards, soft light and shadow, subtle spatial depth, consistent color system, consistent material language, suitable for formal presentation and commercial storytelling.
```

If the user specifies another style, keep it fixed for the whole deck.

## Layout Rules

### Split Layout

Use for two parallel concepts such as external/internal, system/data, human view/AI view, input/output.

Prompt structure:

```text
Top independent title area. Main body split into two equal large floating content zones. Left and right subtitles align on one baseline. Each zone contains icon, subtitle, small supporting line, explanation text, screenshot placeholder or feature card. Keep visual weight balanced.
```

### Stacked Layout

Use when the page first explains logic and then shows cases or screenshots.

Prompt structure:

```text
Top independent title area. Upper half is logic explanation area. Lower half is case/material display area with phone screenshots, tablet screenshots, case cards, or feature examples. Separate the two zones with a subtle divider, glow band, or spatial depth. Lower materials are equal height, evenly spaced, and aligned.
```

### Hub-And-Spoke Layout

Use when one core product/agent/platform expands into multiple capabilities.

Prompt structure:

```text
Top independent title area. Center contains the core object, such as Agent, AI core, product module, or platform hub. Surround it with parallel feature cards. Each card has icon, title, and one short line. Cards share the same size and title position. Connection lines or light flows are subtle and secondary.
```

### Progressive Layout

Use for trends, outlook, and closing pages.

Prompt structure:

```text
Top independent title area. Present information from top to bottom: industry trend, core viewpoint, key differentiation, product positioning, closing statement. Each layer has its own text zone. Important slogan may be larger but must remain visually subordinate to the main title system.
```

### Workflow Layout

Use for task decomposition, agent collaboration, SOP, or process explanation.

Prompt structure:

```text
Top independent title area. Main body arranges steps horizontally or vertically. Each step contains number, title, icon, and one short line. Steps are connected by arrows, lines, or light flow. Complex tasks may use: main Agent -> sub-agent division -> recursive iteration -> final delivery. Nodes must align, not scatter randomly.
```

## Device And Screenshot Slots

Phone slots:

- Use realistic phone frames.
- Keep portrait phone proportions.
- Keep the screenshot area clear.
- Use soft shadow and glow without covering content.

Tablet slots:

- Use horizontal tablet frames.
- Use tablet proportions suitable for dashboards, knowledge graphs, or system panels.
- If phone and tablet appear together, establish clear hierarchy.

Screenshot captions:

- Add short explanatory captions near each screenshot.
- Captions explain capability, value, or scenario; they do not merely repeat what is visible.
- Keep captions like PPT speaker notes, not long documentation.

## Content Module Rules

Feature cards:

```text
icon + feature title + one-sentence explanation
same card radius, shadow, transparency, size, and spacing
```

Body copy:

- Use 2-4 lines maximum.
- Speak to an audience; do not sound like a product manual.
- One paragraph explains one point.

Text hierarchy:

- Main title: fixed top title area.
- Module title: top of a card or section.
- Body copy: explanation of capability and value.
- Tags: supporting keywords only.

## Prompt Template

Use this template and fill every bracket:

```text
Generate one 16:9 4K PPT visual page.

Page title: [page title].
Use an independent top title area. Place the main title in the top-left or fixed top position, with a consistent small decorative line or visual mark under it. Keep the title clear and unobstructed.

Unified visual style: [style lock].
The page must belong to the same PPT deck: consistent color system, material language, glass-card style, lighting, whitespace, title system, and visual rhythm.

Use a four-layer structure:
Layer 1: background base;
Layer 2: transparent gradient overlay;
Layer 3: foreground content area;
Layer 4: independent top title area.

Layout: [split / stacked / hub-and-spoke / progressive / workflow].

Page content:
[Describe each region, module title, short body text, screenshot slots, device frames, feature cards, workflow nodes, or product object.]

Composition requirements:
Align same-level titles;
keep repeated modules the same size and spacing;
phone and tablet screenshots must use realistic device frames;
cards use floating translucent glass material;
main information is clear;
leave generous whitespace;
avoid clutter and decorative noise;
make it suitable for PPT presentation.

Text rendering note:
Keep text simple and clean. Important title text should be accurate. Complex body text may appear as clean placeholder layout areas for later PPT editing.

Do not add unrelated icons or extra text. Do not change the deck's unified visual style.
```

## Generation SOP

1. Determine page role: overview, category, case, mechanism, workflow, or closing.
2. Choose layout:
   - Two parallel concepts -> split
   - Logic then case -> stacked
   - One core with capabilities -> hub-and-spoke
   - Task decomposition -> workflow
   - Future trend / closing -> progressive
3. Lock the unified style for the whole deck.
4. Reduce each page to one main title, 2-4 module titles, brief body copy, and necessary screenshot/case slots.
5. Ask for missing model and aspect ratio/size.
6. Generate with Grsai.
7. Review consistency against the checklist below.

## Helper Script

Use the bundled script to call Grsai after the final prompt is ready:

```powershell
python skills\productivity\ppt-page-image-grsai\scripts\grsai_generate_image.py `
  --model gpt-image-2-vip `
  --aspect-ratio 3840x2160 `
  --prompt-file prompt.txt `
  --out-dir outputs\ppt-page-images `
  --filename 001_cover.png
```

Optional arguments:

- `--base-url https://grsai.dakka.com.cn`
- `--reply-type json` or `--reply-type async`
- `--filename 001_page-title.png` to preserve slide order
- `--api-key <key>` only for local trusted use; prefer `GRSAI_API_KEY`

The script prints JSON and downloads the first returned image URL when possible.

After all slide images are generated, load and follow `ppt-image-deck-assembler`. The final deliverable must be a folder containing the PPTX and an `images/` subfolder with all generated images in order.

## Consistency Checklist

```text
□ Main title is in the unified position
□ Independent top title area is preserved
□ Four-layer structure is visible
□ Unified visual style is unchanged
□ Cards share the same style and size
□ Device screenshots use frames
□ Same-level titles align
□ Page content matches its narrative role
□ Decoration is restrained
□ Image can be placed directly into PPT
```

## Core Principle

Do not generate isolated beautiful pictures. Generate each page as part of one coherent PPT narrative system with shared layers, title logic, layout rules, material language, and visual rhythm.
