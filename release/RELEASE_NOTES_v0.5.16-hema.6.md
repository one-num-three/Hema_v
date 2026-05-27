# Hema v0.5.16-hema.6

This build includes the v0.5.16-hema.5 Web UI streaming fixes, plus the latest
Windows launcher and installer hardening.

## Fixed

- The Web UI desktop shortcut now verifies that the Hermes gateway is running
  before opening the browser.
- If an existing Web UI process reports `gateway: stopped`, the launcher restarts
  it instead of opening a disconnected page.
- The installer icon is regenerated from the bundled hippo image when the `.ico`
  file is missing or invalid, avoiding the Windows Forms icon constructor error.
- The Web UI sidebar relay link (`中转站` / `API Relay`) is patched to:
  `https://ai.opcstore.com/login?expired=true`.
- The Web UI compatibility patch now runs after install and before startup, so
  CDN and npm-installed Web UI copies receive the same local fixes.

## Validation

- `git diff --check` passed for the tracked code changes.
- Local Web UI health check returned `gateway: running` after startup.
- The installed Web UI client bundle contains the new relay URL and no longer
  contains the old `apikey.fun` relay URL.
