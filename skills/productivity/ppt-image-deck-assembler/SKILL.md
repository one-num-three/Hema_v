---
name: ppt-image-deck-assembler
description: Assemble ordered PPT page images into a deliverable folder containing a PPTX file and an images subfolder. Use after ppt-page-image-grsai finishes generating slide images, or when users provide existing ordered images and ask to make a PPT, 整合PPT, 合成PPT, 输出PPT文件夹, or package slide images into PowerPoint.
---

# PPT Image Deck Assembler

Use this skill as the final step of the PPT image workflow:

```text
ppt-content-breakdown -> user approves outline -> ppt-page-image-grsai generates ordered images -> ppt-image-deck-assembler creates the final PPT folder
```

This skill does not design slide content and does not call Grsai. It packages finished page images into a PowerPoint file.

## Output Contract

Always create one output folder containing:

```text
<output-folder>/
  <deck-name>.pptx
  images/
    001_<name>.png
    002_<name>.png
    ...
  manifest.json
```

The PPTX must contain one full-slide image per slide, in the same order as the `images/` subfolder.

## When To Use

Use after:

- Grsai has generated all page images for a PPT deck.
- The user gives an existing folder of slide images.
- The user asks to combine images into a PPT.
- The user wants the final deliverable as a folder with PPT + all images.

If the user has only a broad theme and no images yet, load `ppt-content-breakdown` first. If the outline is approved but images are not generated yet, load `ppt-page-image-grsai` first.

## Required Inputs

Collect or infer:

```text
图片目录：
PPT文件名：
输出文件夹：
页面比例：默认 16:9
图片排序规则：默认按文件名自然排序
图片适配方式：默认 stretch；可选 contain
```

Preferred convention after Grsai generation:

```text
outputs/<deck-name>/generated-images/
  001_cover.png
  002_background.png
  ...
```

Final package:

```text
outputs/<deck-name>/final/
  <deck-name>.pptx
  images/
```

## Assembly Rules

- Preserve page order. Use natural filename sorting: `2.png` comes before `10.png`.
- Copy images into a clean `images/` subfolder using numbered filenames.
- Create a 16:9 PPT deck by default.
- Add each image as a full-slide visual.
- Prefer `stretch` only when images already match the slide ratio, which Grsai PPT images should.
- Use `contain` when user-provided images have mixed ratios and should not be distorted.
- Do not add extra text boxes, decorations, watermarks, or title overlays.
- Do not delete source images.

## Helper Script

Run:

```powershell
python skills\productivity\ppt-image-deck-assembler\scripts\assemble_ppt_from_images.py `
  --images-dir outputs\my-deck\generated-images `
  --out-dir outputs\my-deck\final `
  --deck-name my-deck `
  --fit stretch
```

Options:

```text
--images-dir     Source image folder.
--out-dir        Final output folder.
--deck-name      PPTX filename stem.
--image-subdir   Image subfolder name; default images.
--fit            stretch or contain; default stretch.
--clean          Remove existing out-dir before packaging.
```

The script prints JSON with:

```text
pptx path
images dir
image count
ordered copied images
manifest path
```

## Verification

After assembly, verify:

```text
□ PPTX exists
□ images/ subfolder exists
□ image count equals slide count
□ filenames are numbered in expected order
□ manifest.json exists
□ user receives the final output folder path
```

## Handoff Wording

When finishing, say:

```text
已经整合完成：输出文件夹里有 PPTX 和 images 子文件夹。PPT 每一页按图片顺序铺满页面，原始生成图也按页码保存在 images/ 里。
```
