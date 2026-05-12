# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values not listed here must NOT appear in SVGs.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- primary: #000000
- accent: #000000
- text: #333333
- text_secondary: #666666
- text_tertiary: #999999
- border: #CCCCCC
- grid_bg: #F5F5F5

## typography
- font_family: Inter, "Microsoft YaHei", Arial, sans-serif
- title_family: Montserrat, "Microsoft YaHei", Arial, sans-serif
- body_family: Inter, "Microsoft YaHei", Arial, sans-serif
- emphasis_family: Montserrat, "Microsoft YaHei", Arial, sans-serif
- code_family: "Roboto Mono", Consolas, "Courier New", monospace
- cover_title: 96
- title: 64
- subtitle: 48
- large_body: 32
- body: 28
- small_body: 24
- annotation: 20
- metadata: 16

## icons
- library: tabler-outline
- stroke_width: 2
- size: 48
- hero_size: 64
- color: #000000

## icons_used
- target
- tool
- database
- book
- refresh
- arrow-right
- chevron-down
- circle-check
- alert-circle
- columns

## images
(none)

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: dense
- P06: breathing
- P07: breathing
- P08: dense
- P09: breathing
- P10: anchor

## page_layouts
(none - all pages are free design)

## page_charts
(none - all visualizations are custom diagrams)

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`
