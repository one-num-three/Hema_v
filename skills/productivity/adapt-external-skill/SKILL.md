---
name: adapt-external-skill
description: >-
  Adapt a skill file from an external source (GitHub repo, docs, etc.) into
  Hermes Agent format. Handles path substitution, line number stripping,
  markdown link fixing, and Windows environment adaptation.
---

# Adapt External Skill for Hermes Agent

> Use when you need to install or update a Hermes skill from an external
> reference (e.g., a GitHub repo that ships its own `SKILL.md`, or an
> upstream documentation skill).

## Overview

An external skill file typically uses:
- `${SKILL_DIR}` or `${PROJECT_ROOT}` variables
- `python3` instead of `python`
- Relative paths (e.g., `references/foo.md`, `workflows/bar.md`)
- Markdown links with relative targets

These MUST be resolved to absolute paths that work from `~/.hermes/skills/`.

## Prerequisites

- The external skill's source file (e.g., repo's `skills/xxx/SKILL.md`)
- Write permission to `~/.hermes/skills/<category>/<name>/SKILL.md`
- All referenced files (scripts, references, templates, workflows) locally accessible

## Common Traps

### Trap 1: `read_file()` returns line number prefixes

When you call `read_file(path)`, the `["content"]` field contains lines
with `LINE_NUM|CONTENT` format:

```
     1|---
     2|name: my-skill
```

Writing this directly into the target file corrupts it. **ALWAYS strip
line number prefixes first:**

```python
import re
lines = raw_content.split('\n')
cleaned = []
for line in lines:
    m = re.match(r'^\s*\d+\|(.*)', line)
    if m:
        cleaned.append(m.group(1))
    else:
        cleaned.append(line)
content = '\n'.join(cleaned)
```

### Trap 2: Ripple-effect regexes

Multiple regex substitutions applied sequentially can interfere. Example:
1. Fix markdown links: `[text](workflows/x.md)` → `[text](/abs/path/workflows/x.md)`
2. Fix backtick paths: `` `workflows/x.md` `` → `` `/abs/path/workflows/x.md` ``

**Problem**: If the markdown link fix runs first and produces
`](SKILL_DIR/workflows/x.md)`, the backtick regex might then match
`SKILL_DIR/workflows/x.md` because it contains `workflows/`.

**Solution**: Use a **single pass** approach — fix each class of
reference in isolation, verifying no overlap. Or better: build the
adapted content in one script without sequential regex interference.

### Trap 3: Three classes of relative paths

| Class | Example | Fix |
|-------|---------|-----|
| Markdown links | `[text](workflows/x.md)` | `[text](/abs/path/workflows/x.md)` |
| Inline code (backticks) | `` `references/x.md` `` | `` `/abs/path/references/x.md` `` |
| Plain text instructions | `Read references/strategist.md` | `Read /abs/path/references/strategist.md` |

Use distinct regexes for each. The backtick class and plain-text class
can share a similar pattern but must NOT match already-fixed absolute
paths.

### Trap 4: Code blocks vs. instructions

Inside ``` fences, `Read references/x.md` is an instruction for the AI
(not markdown). Outside fences, it's just prose. Both need updating,
but code-block content is harder to match with simple regexes. Best
approach: use multiline regex with `^` anchor for line-start patterns.

## Recommended Workflow

### Step 1: Read and strip

```python
from hermes_tools import read_file, write_file
import re

raw = read_file("/path/to/external/SKILL.md", limit=9999)
lines = raw["content"].split('\n')
cleaned = []
for line in lines:
    m = re.match(r'^\s*\d+\|(.*)', line)
    cleaned.append(m.group(1) if m else line)
content = '\n'.join(cleaned)
```

### Step 2: Apply substitutions

```python
SKILL_DIR = "/f/hema-fix/xxx/skills/xxx"

# Variable replacements
content = content.replace("${SKILL_DIR}", SKILL_DIR)
content = content.replace("python3 ", "python ")

# Fix markdown links with relative paths
content = re.sub(
    r'(\]\()([^)]+?)(\))',
    lambda m: m.group(1) + SKILL_DIR + '/' + m.group(2) + m.group(3)
    if not m.group(2).startswith('/') and not m.group(2).startswith('http')
    else m.group(0),
    content
)

# Fix "Read references/xxx.md" patterns (line-start instructions)
content = re.sub(
    r'^Read (references/|templates/|workflows/|docs/)',
    lambda m: f"Read {SKILL_DIR}/{m.group(1)}",
    content,
    flags=re.MULTILINE
)

# Fix bare `templates/xxx` in backtick code
for prefix in ["templates/", "references/", "workflows/", "docs/"]:
    content = re.sub(
        rf'`{re.escape(prefix)}',
        f"`{SKILL_DIR}/{prefix}",
        content
    )
```

### Step 3: Verify before writing

```python
assert content.count("${SKILL_DIR}") == 0, "Unresolved SKILL_DIR vars"
assert content.count("python3 ") == 0, "Unresolved python3"
assert not re.search(r'^\s*\d+\|', content, re.MULTILINE), "Line number prefixes remain"
```

### Step 4: Write to target

```python
target = "/c/Users/Keke_/.hermes/skills/<category>/<name>/SKILL.md"
result = write_file(target, content)
```

### Step 5: Verify the skill loads

```python
# In a subsequent turn, call skill_view(name)
# and check that all linked files resolve
```

### Step 6: Verify referenced files exist

Grep, list, or glob-check every file referenced in the skill
(scripts, references, templates, workflows) to ensure they're
actually present at the absolute paths written into the skill.

## Verification

After writing, call `skill_view("<name>")` and confirm:
- [ ] YAML frontmatter intact (`name:`, `description:`)
- [ ] No `${SKILL_DIR}` or `python3` remaining
- [ ] No line number prefixes (`1|`, ` 2|`, etc.)
- [ ] All markdown links point to absolute paths
- [ ] `read_file`/`Read` instructions point to absolute paths
- [ ] All referenced files exist on disk
