# Hema v0.5.16-hema.4

This build includes the v0.5.16-hema.3 local Web UI auth and uninstaller fixes,
plus a gateway response fix for reasoning-only model outputs.

## Fixed

- If a model returns useful text only in `reasoning` / `<think>` style fields
  and leaves assistant `content` empty, Hermes now returns that text as the
  final assistant response immediately.
- Prevents Web UI conversations from showing only user bubbles when the model
  generated a reasoning-only answer.

## Validation

- `python_embedded\python.exe -m py_compile run_agent.py` passed.
- Gateway was restarted locally.
- A direct `POST /v1/responses` test with `你好` returned `status=completed`
  and non-empty assistant text.
