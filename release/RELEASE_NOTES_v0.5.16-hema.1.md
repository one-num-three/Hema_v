# Hema v0.5.16-hema.1

This release packages the current `fix/install-bat-path-issues` branch after
the Web UI context, startup, and installer workflow fixes.

## Fixed

- Preserve Web UI conversation history when calling the Hermes gateway
  `/v1/responses` endpoint.
- Forward the Web UI `session_id` to the gateway in patched Web UI bundles.
- Keep assistant replies visible after reopening Web UI sessions.
- Harden Web UI and gateway startup scripts with clearer diagnostics.
- Generate both `安装Hermes.exe` and `HermesSetup.exe` in the installer
  workflow for CDN compatibility.
- Fix the Web UI bundle workflow YAML parse error caused by an unquoted step
  name containing `:`.

## Validation

- Workflow YAML files parse successfully with PyYAML.
- Python compile check passed for gateway, tests, and patch script.
- A lightweight aiohttp test confirmed `/v1/responses` passes
  `conversation_history` and `session_id` into `_run_agent`.
