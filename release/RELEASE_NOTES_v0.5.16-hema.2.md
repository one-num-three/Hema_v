# Hema v0.5.16-hema.2

This build includes the v0.5.16-hema.1 gateway/Web UI fixes plus a hardened
uninstaller.

## Fixed

- Replaced the fragile batch-only uninstaller with a stable `uninstall.bat`
  launcher plus `uninstall.ps1` implementation.
- Added `/dry-run`, `/quiet`, and `/purge-user-data` uninstall modes.
- Stops only processes that belong to the current install directory.
- Keeps shared PID files when they point to a different install.
- Removes desktop shortcuts by name and by target path.
- Keeps user data by default and requires explicit confirmation before purge.

## Validation

- `uninstall.bat /dry-run /quiet` completed successfully on the real install.
- A temporary fake install was fully removed with `uninstall.bat /quiet`.
- The real `node_embedded`, `python_embedded`, and `webui` directories were
  confirmed still present after dry-run testing.
