Hema v0.5.16-hema.6 Full Local Package

This package is intended for local/offline Windows installation.

Included:
- python_embedded
- node_embedded
- installed hermes-web-ui 0.5.16 runtime
- tools/7za.exe and project runtime files
- latest gateway/Web UI startup, auth-disabled, uninstaller, SSE, icon, and relay-link fixes

Excluded on purpose:
- .git
- .env
- cli-config.yaml
- logs, caches, temporary files
- release output files

Usage:
1. Extract the zip to a local folder.
2. Run installer_gui.bat for graphical installation, or run install.bat full.
3. After installation, use the desktop shortcuts or start_webui.bat.

Notes:
- The installer should reuse the bundled Python, Node.js, and Web UI files
  instead of downloading them again.
- The Web UI shortcut should start/verify the Hermes gateway automatically.
- The sidebar relay entry opens https://ai.opcstore.com/login?expired=true.
- If Windows or the browser warns about an unsafe download, that is usually
  because the package is unsigned and/or served over HTTP. Code signing and
  HTTPS hosting are needed to reduce those warnings.
