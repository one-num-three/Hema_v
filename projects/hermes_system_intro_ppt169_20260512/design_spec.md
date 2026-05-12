# Hermes Agent System - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Hermes Agent System Introduction |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 pages |
| **Design Style** | A) General Versatile + Monochrome Grid-Based Minimalism |
| **Target Audience** | Freshman students (limited technical background, first exposure to AI agent concepts) |
| **Use Case** | Classroom presentation / educational lecture |
| **Created Date** | 2026-05-12 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/Right: 60px, Top/Bottom: 50px |
| **Content Area** | 1160×620 (centered) |

---

## III. Visual Theme

### Theme Style

- **Style**: Monochrome Grid-Based Minimalism
- **Theme**: Light theme (pure white background)
- **Tone**: Educational, clean, systematic, architectural

### Design Philosophy

This presentation adopts a **black-and-white grid system** inspired by Bauhaus and Swiss design principles. The visual language emphasizes:

1. **Geometric precision** — all elements align to an 8×8 modular grid
2. **High contrast** — pure black (#000000) on pure white (#FFFFFF) for maximum clarity
3. **Systematic hierarchy** — information weight expressed through scale, not color
4. **Architectural clarity** — structure made visible through grid lines, frames, and dividers

The style serves the educational mission: complex AI concepts become approachable through visual order and spatial clarity.

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | Page background (pure white) |
| **Primary** | `#000000` | Titles, key text, icons, frames, dividers |
| **Accent** | `#000000` | Data highlights, emphasis (same as primary — monochrome) |
| **Body text** | `#333333` | Main body text (slightly softened for readability) |
| **Secondary text** | `#666666` | Captions, annotations, supporting info |
| **Tertiary text** | `#999999` | Footers, page numbers, metadata |
| **Border/divider** | `#CCCCCC` | Subtle grid lines, section dividers |
| **Grid background** | `#F5F5F5` | Optional subtle grid pattern overlay |

### Grid System

- **Base grid**: 8×8 modular grid (160px × 90px cells)
- **Visual elements**:
  - Thin grid lines (1px, #CCCCCC) as subtle background texture
  - Bold black frames (4-6px) for section emphasis
  - Geometric dividers (horizontal/vertical rules)
  - Pixel-style corner brackets for anchoring elements

---

## IV. Typography System

### Font Plan

**Design rationale**: Geometric sans-serif fonts reinforce the grid-based, architectural aesthetic. Montserrat provides strong geometric forms for titles; Inter offers excellent readability for body text with a technical feel; Roboto Mono adds precision for code/technical terms.

| Role | Font Stack | Rationale |
| ---- | ---------- | --------- |
| **Title** | Montserrat, "Microsoft YaHei", Arial, sans-serif | Geometric sans-serif with strong presence |
| **Body** | Inter, "Microsoft YaHei", Arial, sans-serif | Clean, technical, highly readable |
| **Emphasis** | Montserrat, "Microsoft YaHei", Arial, sans-serif | Same as title for consistency |
| **Code** | "Roboto Mono", Consolas, "Courier New", monospace | Technical precision |

**Per-role font stacks** (copy to spec_lock.md verbatim):
- `font_family: Inter, "Microsoft YaHei", Arial, sans-serif`
- `title_family: Montserrat, "Microsoft YaHei", Arial, sans-serif`
- `body_family: Inter, "Microsoft YaHei", Arial, sans-serif`
- `emphasis_family: Montserrat, "Microsoft YaHei", Arial, sans-serif`
- `code_family: "Roboto Mono", Consolas, "Courier New", monospace`

### Font Size Hierarchy

| Role | Size (px) | Usage |
| ---- | -------- | ----- |
| **Cover title** | 96 | Cover page main title |
| **Title** | 64 | Section titles, chapter pages |
| **Subtitle** | 48 | Page titles, key statements |
| **Large body** | 32 | Primary content, key points |
| **Body** | 28 | Standard body text (baseline) |
| **Small body** | 24 | Supporting text, list items |
| **Annotation** | 20 | Captions, footnotes |
| **Metadata** | 16 | Page numbers, timestamps |

**Baseline**: `body: 28px` — all other sizes derive as ratios of this anchor.

---

## V. Layout Principles

### Page Structure

- **Header area**: 0-100px — optional page number, section indicator
- **Content area**: 100-670px — main content zone (570px height)
- **Footer area**: 670-720px — optional metadata, progress indicator

### Layout Pattern Library

This deck uses the following patterns (combined/broken as content demands):

| Pattern | Used In Pages | Purpose |
| ------- | ------------- | ------- |
| **Single column centered** | P01, P02, P09, P10 | Cover, definition, summary, closing |
| **Symmetric split (5:5)** | P03 | Comparison (chatbot vs agent) |
| **Asymmetric split (3:7)** | — | (Not used in this deck) |
| **Three/four column cards** | — | (Not used in this deck) |
| **Matrix grid (2×2)** | P03 | Comparison matrix |
| **Vertical flow diagram** | P04, P05 | Architecture, workflow |
| **Z-pattern / waterfall** | P06 | Case study breakdown |
| **Center-radiating** | P04 | Core modules diagram |
| **Full-bleed + floating text** | — | (Not used in this deck) |
| **Negative-space-driven** | P02, P07, P09 | Key statements with breathing room |

### Spacing Specification

**Universal** (any container type):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | 60px |
| Content block gap | 24-40px | 40px |
| Icon-text gap | 8-16px | 12px |

**Non-card containers** (this deck uses minimal cards, primarily naked text blocks and diagrams):

- Vertical rhythm carried by **whitespace** — block gaps run wider (40-60px)
- **Line-height**: 1.5× body font size (42px for 28px body)
- **Grid alignment**: all elements snap to 8px base grid
- **Frame thickness**: 4-6px for bold black borders

---

## VI. Icon Usage Specification

### Icon Source

- **Library**: Lucide Icons (line-based, geometric, monochrome-friendly)
- **Style**: Stroke-based, 2px stroke width, black (#000000)
- **Size**: 48×48px standard, 64×64px for hero icons

### Icon Placeholder Syntax

```
{{icon:target}}
{{icon:wrench}}
{{icon:database}}
{{icon:book}}
{{icon:refresh-cw}}
```

### Recommended Icon List

| Concept | Icon Name | Usage |
| ------- | --------- | ----- |
| Planner | `target`, `list` | Task planning module |
| Tool System | `wrench`, `tool` | External tool integration |
| Memory | `database`, `brain` | Long-term memory system |
| Skill Library | `book`, `layers` | Skill accumulation |
| Reflection | `refresh-cw`, `repeat` | Self-improvement loop |
| Workflow | `arrow-right`, `chevron-down` | Process flow |
| Comparison | `git-compare`, `columns` | Before/after contrast |
| Success | `check-circle` | Positive indicators |
| Challenge | `alert-circle` | Problem areas |

---

## VII. Visualization Reference List

| Page | Visualization Type | Reference Template Path | Purpose |
| ---- | ------------------ | ---------------------- | ------- |
| P03 | Comparison Matrix (2×2) | no-template-match | Chatbot vs Agent comparison |
| P04 | Architecture Diagram (center-radiating) | no-template-match | 5 core modules visualization |
| P05 | Vertical Flowchart | no-template-match | Workflow from input to output |
| P06 | Step-by-step Breakdown | no-template-match | PPT generation case study |

**Note**: All visualizations are custom-designed to match the monochrome grid aesthetic. No pre-built chart templates apply.

---

## VIII. Image Resource List

**Strategy**: No photographic images. All visuals are geometric diagrams, icons, and typographic elements.

| Filename | Dimensions | Ratio | Purpose | Status | Acquire Via |
| -------- | ---------- | ----- | ------- | ------ | ----------- |
| (none) | — | — | Pure graphic design deck | N/A | N/A |

---

## IX. Content Outline

### Page Roster & Rhythm

| Page | Type | Rhythm | Layout Pattern | Title | Key Message |
| ---- | ---- | ------ | -------------- | ----- | ----------- |
| P01 | Cover | anchor | Single column centered | Hermes Agent System | An Intelligent AI Agent Architecture |
| P02 | Definition | breathing | Negative-space-driven | What is Hermes? | AI that thinks, acts, and learns |
| P03 | Comparison | dense | Matrix grid (2×2) | Beyond Chatbots | Chatbot vs Agent capabilities |
| P04 | Architecture | dense | Center-radiating | Core Architecture | 5 modules working together |
| P05 | Workflow | dense | Vertical flowchart | How It Works | From input to output |
| P06 | Case Study | breathing | Z-pattern | Use Case: PPT Generation | Real-world task breakdown |
| P07 | Value Proposition | breathing | Negative-space-driven | Why It Matters | Evolution from chatbot to assistant |
| P08 | Challenges | dense | Vertical list | Challenges | Cost, errors, security |
| P09 | Summary | breathing | Single column centered | Key Takeaway | Core definition statement |
| P10 | Closing | anchor | Single column centered | Thank You | Q&A invitation |

---

### Detailed Page Content

#### P01: Cover (anchor)

**Layout**: Single column centered, large title with grid background

**Content**:
- Main title: "HERMES AGENT SYSTEM"
- Subtitle: "An Intelligent AI Agent Architecture"
- Decorative element: Subtle 8×8 grid pattern background
- Footer: "For Freshman Students | 2026"

**Visual elements**:
- Bold black frame around title
- Pixel-style corner brackets
- Minimal, high-impact typography

---

#### P02: What is Hermes? (breathing)

**Layout**: Negative-space-driven, centered definition

**Content**:
- Page title: "What is Hermes?"
- Core definition (large text):
  > "An AI agent that thinks, uses tools, remembers experiences, and continuously learns."
- Supporting text:
  - "Unlike chatbots that only talk..."
  - "Hermes completes tasks like a human assistant."

**Visual elements**:
- Large body text (32px) for definition
- 60% whitespace for emphasis
- Thin horizontal divider above/below definition

---

#### P03: Beyond Chatbots (dense)

**Layout**: 2×2 comparison matrix

**Content**:
- Page title: "Beyond Chatbots"
- Matrix structure:

| | **Regular Chatbot** | **Hermes Agent** |
|---|---|---|
| **Capability** | Answers questions | Completes tasks |
| **Tools** | None | Browser, Python, APIs, Files |
| **Memory** | Session-only | Long-term memory |
| **Learning** | Static | Self-evolving |

**Visual elements**:
- Bold black grid lines (4px)
- Icons in each quadrant
- High contrast text hierarchy

---

#### P04: Core Architecture (dense)

**Layout**: Center-radiating diagram

**Content**:
- Page title: "Core Architecture"
- Central node: "HERMES AGENT"
- 5 surrounding modules (with icons):
  1. **Planner** {{icon:target}} — Breaks tasks into steps
  2. **Tool System** {{icon:wrench}} — Executes operations
  3. **Memory** {{icon:database}} — Stores experiences
  4. **Skill Library** {{icon:book}} — Reuses solutions
  5. **Reflection** {{icon:refresh-cw}} — Self-improves

**Visual elements**:
- Geometric connecting lines
- Module boxes with icons
- Circular or radial layout

---

#### P05: How It Works (dense)

**Layout**: Vertical flowchart

**Content**:
- Page title: "How It Works"
- Workflow steps (top to bottom):
  1. **Understand Task** — Parse user input
  2. **Break Down Steps** — Planner creates subtasks
  3. **Call Tools** — Execute operations
  4. **Search Information** — Gather data
  5. **Generate Result** — Produce output
  6. **Save Experience** — Update memory
  7. **Optimize Next Time** — Reflection loop

**Visual elements**:
- Vertical arrows between steps
- Step numbers in circles
- Consistent box sizing

---

#### P06: Use Case: PPT Generation (breathing)

**Layout**: Z-pattern step breakdown

**Content**:
- Page title: "Use Case: PPT Generation"
- User request: *"Create an AI industry analysis PPT"*
- Hermes process:
  1. **Analyze** — Understand requirements
  2. **Research** — Search industry data
  3. **Structure** — Organize content outline
  4. **Visualize** — Generate charts
  5. **Export** — Produce final PPTX

**Visual elements**:
- Step boxes alternate left/right
- Arrow flow guiding the eye
- Example text in code font

---

#### P07: Why It Matters (breathing)

**Layout**: Negative-space-driven, large statement

**Content**:
- Page title: "Why It Matters"
- Key statement (large text):
  > "Hermes represents the evolution from **chatbot** to **intelligent assistant**."
- Supporting points:
  - Automates complex workflows
  - Learns from experience
  - Scales human capability

**Visual elements**:
- Bold emphasis on key words
- Generous whitespace (50%+)
- Horizontal divider

---

#### P08: Challenges (dense)

**Layout**: Vertical list with icons

**Content**:
- Page title: "Challenges"
- Challenge list:
  1. {{icon:alert-circle}} **High Cost** — Computational resources
  2. {{icon:alert-circle}} **Error Chains** — Long task sequences can fail
  3. {{icon:alert-circle}} **Bad Memory** — Incorrect experiences persist
  4. {{icon:alert-circle}} **Security Risks** — Tool permissions require safeguards

**Visual elements**:
- Icon + text pairs
- Consistent vertical spacing
- Alert icons in black

---

#### P09: Key Takeaway (breathing)

**Layout**: Single column centered, large quote

**Content**:
- Page title: "Key Takeaway"
- Core definition (extra large text):
  > "Hermes Agent is an AI system that **thinks**, **uses tools**, **accumulates experience**, and **continuously grows**."

**Visual elements**:
- Maximum font size (48-64px)
- Bold keywords
- Frame or bracket decoration

---

#### P10: Thank You (anchor)

**Layout**: Single column centered, minimal

**Content**:
- Main text: "THANK YOU"
- Subtitle: "Questions?"
- Optional: Contact info or next steps

**Visual elements**:
- Grid background (matching cover)
- Clean, symmetrical layout
- Pixel-style corner brackets

---

## X. Speaker Notes Requirements

**Strategy**: No speaker notes required (user confirmed).

**File naming**: `notes/P<NN>_<slug>.md` (e.g., `notes/P01_cover.md`)

**Content structure**: N/A

---

## XI. Technical Constraints Reminder

### SVG Generation Rules

1. **Grid alignment**: All elements snap to 8px base grid
2. **Stroke consistency**: 2px for icons, 4-6px for frames, 1px for subtle lines
3. **No gradients**: Pure black/white/gray only (monochrome constraint)
4. **Font fallbacks**: Every stack ends with cross-platform font
5. **Icon embedding**: Use `{{icon:name}}` placeholder, resolved by finalize_svg.py

### PPT Compatibility Rules

1. **Font stacks**: Must end with Microsoft YaHei / Arial / Consolas
2. **No rgba()**: Use solid HEX colors only
3. **No `<style>` or `class`**: Inline all attributes
4. **Text as `<text>`**: No `<foreignObject>` or `textPath`
5. **Shapes as primitives**: `<rect>`, `<circle>`, `<line>`, `<path>` only

---

## Design Spec Complete

**Next steps**:
1. ✅ Eight Confirmations completed (user confirmed)
2. ✅ Design Specification generated
3. ⏭️ Generate `spec_lock.md` (execution contract)
4. ⏭️ Proceed to Executor phase (SVG generation)
| Content block gap | 24-40px | 32px |
| Icon-text gap | 8-16px | 12px |

**Non-card containers** (this deck uses minimal cards, primarily naked text blocks and diagrams):

- Vertical rhythm carried by **whitespace** and grid alignment
- **Line-height**: 1.5× body font size (42px for 28px body)
- **Grid snap**: all elements align to 8px baseline grid
- **Divider weight**: 2px for subtle dividers, 4-6px for bold frames

---

## VI. Icon Usage Specification

### Icon Source

- **Library**: Lucide Icons (line-based, geometric, monochrome-friendly)
- **Style**: Stroke-based, 2px stroke weight, black (#000000)
- **Size**: 48×48px standard, 64×64px for hero icons

### Placeholder Syntax

```
{{icon:target}}
{{icon:tool}}
{{icon:database}}
{{icon:book-open}}
{{icon:refresh-cw}}
{{icon:arrow-right}}
{{icon:check-circle}}
{{icon:alert-triangle}}
```

### Recommended Icon List

| Concept | Icon Name | Usage |
| ------- | --------- | ----- |
| Planner | `target` / `list-checks` | Task planning module |
| Tool System | `wrench` / `tool` | External tool integration |
| Memory | `database` / `brain` | Long-term memory system |
| Skill Library | `book-open` / `layers` | Skill accumulation |
| Reflection | `refresh-cw` / `repeat` | Self-learning loop |
| Workflow | `arrow-right` / `chevron-right` | Process flow |
| Success | `check-circle` | Advantages |
| Challenge | `alert-triangle` | Limitations |
| User | `user` | User input |
| Output | `file-text` | System output |

---

## VII. Visualization Reference List

| Page | Visualization Type | Reference Template Path | Purpose |
| ---- | ------------------ | ---------------------- | ------- |
| P03 | Comparison Matrix (2×2) | no-template-match | Chatbot vs Agent comparison |
| P04 | Architecture Diagram (center-radiating) | no-template-match | 5 core modules visualization |
| P05 | Vertical Flowchart | no-template-match | Workflow steps |
| P06 | Step-by-step Breakdown | no-template-match | Use case example |

**Note**: All visualizations are custom-designed to match the monochrome grid aesthetic. No pre-built chart templates apply.

---

## VIII. Image Resource List

**Strategy**: This deck uses **no photographic images**. All visuals are geometric diagrams, icons, and typographic elements generated within SVG.

| Filename | Dimensions | Ratio | Purpose | Status | Acquire Via |
| -------- | ---------- | ----- | ------- | ------ | ----------- |
| (none) | — | — | Pure diagram-based deck | N/A | N/A |

---

## IX. Content Outline

### Page Rhythm Map

| Page | Rhythm | Rationale |
| ---- | ------ | --------- |
| P01 | `anchor` | Cover — establishes visual identity |
| P02 | `breathing` | Definition — single core concept with space |
| P03 | `dense` | Comparison matrix — information-rich |
| P04 | `dense` | Architecture diagram — 5 modules + connections |
| P05 | `dense` | Workflow — multi-step process |
| P06 | `breathing` | Use case — narrative example with space |
| P07 | `breathing` | Importance statement — key message emphasis |
| P08 | `dense` | Advantages + Challenges — dual lists |
| P09 | `breathing` | Summary — single takeaway statement |
| P10 | `anchor` | Closing — clean exit |

---

### Chapter 1: Introduction (P01-P02)

#### P01: Cover Page
- **Layout**: Single column centered, `anchor` rhythm
- **Title**: "HERMES AGENT SYSTEM"
- **Subtitle**: "An Intelligent AI Agent Architecture"
- **Visual elements**:
  - Large title with geometric frame
  - Subtle grid background
  - Minimal metadata (date, presenter info optional)
- **Key message**: Establish professional, systematic tone

#### P02: Definition Page
- **Layout**: Single column centered, `breathing` rhythm
- **Title**: "What is Hermes?"
- **Content**:
  - Core definition: "An AI agent that thinks, acts, and learns"
  - Key distinction: "Beyond chatbots — Hermes completes tasks like a human assistant"
- **Visual elements**:
  - Large body text (32px)
  - Icon: `{{icon:brain}}` or `{{icon:cpu}}`
  - Ample whitespace for emphasis
- **Key message**: Hermes is fundamentally different from traditional chatbots

---

### Chapter 2: Core Concepts (P03-P05)

#### P03: Comparison Page
- **Layout**: 2×2 matrix grid, `dense` rhythm
- **Title**: "Beyond Chatbots"
- **Content**:
  - **Traditional AI Chatbot**:
    - Only responds to questions
    - No memory between sessions
    - Cannot use external tools
    - Passive interaction
  - **Hermes Agent**:
    - Completes complex tasks
    - Long-term memory
    - Calls external tools
    - Autonomous execution
- **Visual elements**:
  - 2×2 comparison matrix
  - Icons: `{{icon:message-circle}}` (chatbot) vs `{{icon:cpu}}` (agent)
  - Bold divider line between columns
- **Key message**: Hermes represents a paradigm shift in AI capability

#### P04: Architecture Page
- **Layout**: Center-radiating diagram, `dense` rhythm
- **Title**: "Core Architecture"
- **Content**: 5 core modules
  1. **Planner** — Task decomposition
  2. **Tool System** — External integrations
  3. **Memory** — Long-term storage
  4. **Skill Library** — Experience accumulation
  5. **Reflection** — Self-improvement
- **Visual elements**:
  - Central node: "Hermes Core"
  - 5 surrounding modules with icons
  - Connection lines showing relationships
  - Icons: `{{icon:target}}`, `{{icon:tool}}`, `{{icon:database}}`, `{{icon:book-open}}`, `{{icon:refresh-cw}}`
- **Key message**: Hermes is a multi-component system working in harmony

#### P05: Workflow Page
- **Layout**: Vertical flowchart, `dense` rhythm
- **Title**: "How It Works"
- **Content**: Step-by-step process
  1. User Input → "Analyze AI industry"
  2. Understand Task
  3. Decompose Steps
  4. Call Tools
  5. Search Information
  6. Generate Results
  7. Save Experience
  8. Optimize for Next Time
- **Visual elements**:
  - Vertical flow with arrows `{{icon:arrow-down}}`
  - Each step in a black-bordered box
  - Grid-aligned spacing
- **Key message**: Hermes follows a systematic, repeatable process

---

### Chapter 3: Application & Impact (P06-P08)

#### P06: Use Case Page
- **Layout**: Z-pattern / waterfall, `breathing` rhythm
- **Title**: "Use Case: PPT Generation"
- **Content**: Real-world example breakdown
  - **User Request**: "Create an AI industry analysis PPT"
  - **Hermes Process**:
    1. Search industry data
    2. Organize content structure
    3. Generate charts
    4. Design layout
    5. Output final PPTX
- **Visual elements**:
  - Step-by-step breakdown with icons
  - Alternating left/right alignment (Z-pattern)
  - Icon: `{{icon:file-text}}`
- **Key message**: Hermes handles complex, multi-step tasks autonomously

#### P07: Importance Page
- **Layout**: Single column centered, `breathing` rhythm
- **Title**: "Why It Matters"
- **Content**:
  - Core statement: "AI evolves from chatbot to intelligent assistant"
  - Future applications:
    - Automated office work
    - Autonomous coding
    - Report generation
    - Research automation
- **Visual elements**:
  - Large statement text (48px)
  - Icon: `{{icon:trending-up}}`
  - Minimal decoration, maximum impact
- **Key message**: Hermes represents the future of AI assistance

#### P08: Advantages & Challenges Page
- **Layout**: Symmetric split (5:5), `dense` rhythm
- **Title**: "Strengths & Challenges"
- **Content**:
  - **Left column — Advantages**:
    - Handles complex tasks
    - Tool integration
    - Long-term memory
    - Continuous learning
    - High automation
  - **Right column — Challenges**:
    - High operational cost
    - Error propagation risk
    - Memory quality issues
    - Security concerns
- **Visual elements**:
  - Two columns with icons
  - Icons: `{{icon:check-circle}}` (advantages), `{{icon:alert-triangle}}` (challenges)
  - Vertical divider line
- **Key message**: Hermes is powerful but requires careful deployment

---

### Chapter 4: Conclusion (P09-P10)

#### P09: Summary Page
- **Layout**: Single column centered, `breathing` rhythm
- **Title**: "Key Takeaway"
- **Content**:
  - Core definition: "Hermes Agent is an AI system that thinks, uses tools, accumulates experience, and continuously evolves."
- **Visual elements**:
  - Large quote-style text (36px)
  - Geometric frame around statement
  - Icon: `{{icon:lightbulb}}`
- **Key message**: One-sentence essence of Hermes

#### P10: Closing Page
- **Layout**: Single column centered, `anchor` rhythm
- **Title**: "THANK YOU"
- **Subtitle**: "Questions?"
- **Visual elements**:
  - Clean, minimal design
  - Grid background
  - Optional contact info placeholder
- **Key message**: Professional closing, invite discussion

---

## X. Speaker Notes Requirements

**Strategy**: No speaker notes required (user specified "不需要备注").

**File naming**: `notes/total.md` (standard pipeline output, will be empty or minimal)

**Content structure**: N/A

---

## XI. Technical Constraints Reminder

### SVG Generation Rules

1. **Grid alignment**: All elements snap to 8px baseline grid
2. **Stroke consistency**: All lines use consistent stroke-width (2px for icons/dividers, 4-6px for bold frames)
3. **Monochrome discipline**: Only use colors from spec_lock.md (black, white, grays)
4. **No gradients**: Pure flat colors only (monochrome aesthetic)
5. **Icon embedding**: Use `{{icon:name}}` placeholders, resolved by finalize_svg.py
6. **Text rendering**: Use `<text>` elements with proper font-family fallback stacks

### PPT Compatibility Rules

1. **Font stacks**: All stacks end with cross-platform fonts (Arial, sans-serif, etc.)
2. **No forbidden features**: No `<foreignObject>`, `<style>`, `class`, `rgba()`, `<animate>`
3. **Viewbox consistency**: All SVGs use `viewBox="0 0 1280 720"`
4. **Text encoding**: Use raw Unicode for special characters, XML entities for reserved chars only
5. **Shape primitives**: Use `<rect>`, `<circle>`, `<line>`, `<path>` for geometric elements

---

## Design Spec Complete

**Next steps**:
1. ✅ Design Specification generated
2. ⏭️ Generate `spec_lock.md` (execution contract)
3. ⏭️ Proceed to Executor Phase (SVG generation)
