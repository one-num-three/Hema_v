# Hema v0.5.16-hema.7

This build replaces the broken v0.5.16-hema.6 full-local package.

## Fixed

- The full local package now includes embedded Python standard-library archive
  files such as `python_embedded\python313.zip`.
- `install.bat` no longer trusts `python.exe` alone. It verifies that embedded
  Python can import `encodings`; if not, it treats the runtime as incomplete and
  reinstalls it.
- Python extraction now fails early with a clear message if `python*.zip` is
  missing.
- `get-pip.py` download failures now show a specific network/TLS/proxy hint
  instead of continuing into a confusing Python startup crash.
- Added a guarded full-local package builder that refuses to produce a zip if
  required runtime files are missing.

## Still Included

- Web UI shortcut auto-starts/verifies the Hermes gateway before opening.
- Installer icon hardening for invalid `.ico` files.
- Web UI `中转站` / `API Relay` link points to
  `https://ai.opcstore.com/login?expired=true`.
- hermes-web-ui 0.5.16 runtime is included for local/offline install.
