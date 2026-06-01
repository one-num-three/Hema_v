---
name: hermes-agent-setup
description: Help users configure Hermes Agent — CLI usage, setup wizard, model/provider selection, tools, skills, voice/STT/TTS, gateway, and troubleshooting. Use when someone asks to enable features, configure settings, or needs help with Hermes itself.
version: 1.2.0
author: Hermes Agent
tags: [setup, configuration, tools, stt, tts, voice, hermes, cli, skills]
---

# Hermes Agent Setup & Configuration

Use this skill when a user asks about configuring Hermes, enabling features, setting up voice, managing tools/skills, or troubleshooting.

## Key Paths

- Config: `~/.hermes/config.yaml`
- API keys: `~/.hermes/.env`
- Skills: `~/.hermes/skills/`
- Hermes install: `~/.hermes/hermes-agent/`
- Venv: `~/.hermes/hermes-agent/venv/`

## CLI Overview

Hermes is used via the `hermes` command (or `python -m hermes_cli.main` from the repo).

### Core commands:

```
hermes                          Interactive chat (default)
hermes chat -q "question"       Single query, then exit
hermes chat -m MODEL            Chat with a specific model
hermes -c                       Resume most recent session
hermes -c "project name"        Resume session by name
hermes --resume SESSION_ID      Resume by exact ID
hermes -w                       Isolated git worktree mode
hermes -s skill1,skill2         Preload skills for the session
hermes --yolo                   Skip dangerous command approval
```

### Configuration & setup:

```
hermes setup                    Interactive setup wizard (provider, API keys, model)
hermes model                    Interactive model/provider selection
hermes config                   View current configuration
hermes config edit              Open config.yaml in $EDITOR
hermes config set KEY VALUE     Set a config value directly
hermes login                    Authenticate with a provider
hermes logout                   Clear stored auth
hermes doctor                   Check configuration and dependencies
```

### Tools & skills:

```
hermes tools                    Interactive tool enable/disable per platform
hermes skills list              List installed skills
hermes skills search QUERY      Search the skills hub
hermes skills install NAME      Install a skill from the hub
hermes skills config            Enable/disable skills per platform
```

### Gateway (messaging platforms):

```
hermes gateway run              Start the messaging gateway
hermes gateway install          Install gateway as background service
hermes gateway status           Check gateway status
```

### Session management:

```
hermes sessions list            List past sessions
hermes sessions browse          Interactive session picker
hermes sessions rename ID TITLE Rename a session
hermes sessions export ID       Export session as markdown
hermes sessions prune           Clean up old sessions
```

### Other:

```
hermes status                   Show status of all components
hermes cron list                List cron jobs
hermes insights                 Usage analytics
hermes update                   Update to latest version
hermes pairing                  Manage DM authorization codes
```

## Setup Wizard (`hermes setup`)

The interactive setup wizard walks through:
1. **Provider selection** — OpenRouter, Anthropic, OpenAI, Google, DeepSeek, and many more
2. **API key entry** — stores securely in the env file
3. **Model selection** — picks from available models for the chosen provider
4. **Basic settings** — reasoning effort, tool preferences

Run it from terminal:
```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
python -m hermes_cli.main setup
```

To change just the model/provider later: `hermes model`

## Skills Configuration (`hermes skills`)

Skills are reusable instruction sets that extend what Hermes can do.

### Managing skills:

```bash
hermes skills list              # Show installed skills
hermes skills search "docker"   # Search the hub
hermes skills install NAME      # Install from hub
hermes skills config            # Enable/disable per platform
```

### Per-platform skill control:

`hermes skills config` opens an interactive UI where you can enable or disable specific skills for each platform (cli, telegram, discord, etc.). Disabled skills won't appear in the agent's available skills list for that platform.

### Loading skills in a session:

- CLI: `hermes -s skill-name` or `hermes -s skill1,skill2`
- Chat: `/skill skill-name`
- Gateway: type `/skill skill-name` in any chat

## Voice Messages (STT)

Voice messages from Telegram/Discord/WhatsApp/Slack/Signal are auto-transcribed when an STT provider is available.

### Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key, runs on CPU/GPU
2. **Groq Whisper** — free tier, needs GROQ_API_KEY
3. **OpenAI Whisper** — paid, needs VOICE_TOOLS_OPENAI_KEY

### Setup local STT (recommended):

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
pip install faster-whisper
```

Add to config.yaml under the `stt:` section:
```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base  # Options: tiny, base, small, medium, large-v3
```

Model downloads automatically on first use (~150 MB for base).

### Setup Groq STT (free cloud):

1. Get free key from https://console.groq.com
2. Add GROQ_API_KEY to the env file
3. Set provider to groq in config.yaml stt section

### Verify STT:

After config changes, restart the gateway (send /restart in chat, or restart `hermes gateway run`). Then send a voice message.

## Voice Replies (TTS)

Hermes can reply with voice when users send voice messages.

### TTS providers (set API key in env file):

| Provider | Env var | Free? |
|----------|---------|-------|
| ElevenLabs | ELEVENLABS_API_KEY | Free tier |
| OpenAI | VOICE_TOOLS_OPENAI_KEY | Paid |
| Kokoro (local) | None needed | Free |
| Fish Audio | FISH_AUDIO_API_KEY | Free tier |

### Voice commands (in any chat):
- `/voice on` — voice reply to voice messages only
- `/voice tts` — voice reply to all messages
- `/voice off` — text only (default)

## Enabling/Disabling Tools (`hermes tools`)

### Interactive tool config:

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
python -m hermes_cli.main tools
```

This opens a curses UI to enable/disable toolsets per platform (cli, telegram, discord, slack, etc.).

### After changing tools:

Use `/reset` in the chat to start a fresh session with the new toolset. Tool changes do NOT take effect mid-conversation (this preserves prompt caching and avoids cost spikes).

### Common toolsets:

| Toolset | What it provides |
|---------|-----------------|
| terminal | Shell command execution |
| file | File read/write/search/patch |
| web | Web search and extraction |
| browser | Browser automation (needs Browserbase) |
| image_gen | AI image generation |
| mcp | MCP server connections |
| voice | Text-to-speech output |
| cronjob | Scheduled tasks |

## Installing Dependencies

Some tools need extra packages:

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate

pip install faster-whisper    # Local STT (voice transcription)
pip install browserbase       # Browser automation
pip install mcp               # MCP server connections
```

## Config File Reference

The main config file is `~/.hermes/config.yaml`. Key sections:

```yaml
# Model and provider
model:
  default: anthropic/claude-opus-4.6
  provider: openrouter

# Agent behavior
agent:
  max_turns: 90
  reasoning_effort: high    # xhigh, high, medium, low, minimal, none

# Voice
stt:
  enabled: true
  provider: local           # local, groq, openai
tts:
  provider: elevenlabs      # elevenlabs, openai, kokoro, fish

# Display
display:
  skin: default             # default, ares, mono, slate
  tool_progress: full       # full, compact, off
  background_process_notifications: all  # all, result, error, off
```

Edit with `hermes config edit` or `hermes config set KEY VALUE`.

## Gateway Commands (Messaging Platforms)

| Command | What it does |
|---------|-------------|
| /reset or /new | Fresh session (picks up new tool config) |
| /help | Show all commands |
| /model [name] | Show or change model |
| /compact | Compress conversation to save context |
| /voice [mode] | Configure voice replies |
| /reasoning [effort] | Set reasoning level |
| /sethome | Set home channel for cron/notifications |
| /restart | Restart the gateway (picks up config changes) |
| /status | Show session info |
| /retry | Retry last message |
| /undo | Remove last exchange |
| /personality [name] | Set agent personality |
| /skill [name] | Load a skill |

## Troubleshooting

## How Terminal Execution Works on Windows (Architecture)

This is critical context for understanding any terminal-related issue on Windows.

**Hermes does NOT use cmd.exe for terminal commands.** It uses **Git Bash** (`bash.exe`).

### Runtime vs Shell: Two Different Things

There's an important distinction:

**Runtime (how Hermes itself launches):**
```
hermes.bat / START.bat
  ↓  (bat script runs in Windows cmd.exe)
cmd.exe
  ↓  sets PATH/PYTHONPATH/HERMES_ROOT/PYTHONIOENCODING=utf-8
python_embedded\python.exe
  ↓
python -m hermes_cli.main
```
`hermes.bat` is a standard `.bat` script executed by `cmd.exe`. It calls embedded Python directly. **No bash, no WSL involved in the runtime chain.** Confirmed by `hermes.bat` lines 86, 94-95, 107:
```bat
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%SCRIPT_DIR%node_modules\.bin;%PATH%"
set "HERMES_PYTHON=%PYTHON_EXE%"
set "HERMES_ROOT=%SCRIPT_DIR%"
"%PYTHON_EXE%" -m hermes_cli.main %*
```

**Shell (how the terminal tool executes commands):**
The `terminal` tool internally uses `bash.exe` (Git Bash) via `subprocess.Popen([bash, "-lic", command])`. This is separate from how Hermes itself launches.

### Running cmd.exe Commands from Within Git Bash

Since the terminal tool uses Git Bash, Windows cmd.exe commands won't work directly. But you can **force cmd.exe** execution with the `//c` flag (MSYS2 translates single `/c` to a path; double `//c` works):

```bash
# From within the Git Bash terminal tool:
cmd.exe //c "echo Current directory: %CD% && dir /b"
cmd.exe //c "ver"
cmd.exe //c "where bash"
cmd.exe //c "findstr /n something file.txt"
```

The `workdir` parameter on the terminal tool changes Git Bash's working directory. Combined with `cmd.exe //c`, this lets you work from any path:

```python
terminal("cmd.exe //c 'dir /b'", workdir="F:\\hema-fix\\hema-fix")
```

Note: Each `cmd.exe //c` invocation is a **separate process** — `cd` changes don't persist between calls. Chain commands with `&&` instead.

### Is Git Required for Hermes to Run? (Windows)

**No. Git is NOT a hard dependency.** Hermes runs perfectly fine on a system with zero Git installed.

#### Runtime (daily use): Zero git dependency

The Python code (`hermes_cli/` directory) has **zero** `subprocess.run("git...")` calls. Searched all `.py` files — no git invocations anywhere in the runtime.

The execution chain:
```
hermes.bat / START.bat
  ↓  (cmd.exe runs the bat script)
python_embedded\python.exe -m hermes_cli.main
  ↓  (pure Python)
Hermes Agent running
```
No `git.exe` is ever called after installation. You can delete Git from the system and Hermes will still start and work fine.

#### Installation: Optional, gracefully handled

Only `install.bat` uses `git.exe` (from Windows PATH, NOT from Git Bash shell):
```bat
where git >nul 2>&1
if %errorlevel% equ 0 (
    git submodule update --init --recursive --quiet 2>nul
) else (
    echo [INFO] Git not found - skipping submodules.
)
```

**When git is absent:**
- `install.bat` continues normally with just an info message
- The `mini-swe-agent` submodule won't be fetched (this is a code-editing feature, not core AI)
- Everything else (Python, dependencies, Web UI, skills) installs fine
- Hermes starts and runs without any missing-functionality errors

#### For pre-packaged/offline distribution

To make Hermes truly zero-dependency for beginners, pre-bundle these in the zip:
- `python_embedded/` — already bundled by install.bat
- `node_embedded/` — already bundled by full installer
- `webui/` — already bundled
- `mini-swe-agent/` — this is the only git submodule; just include it pre-fetched

With this, the user needs: Windows 10/11 (with cmd.exe) + the zip file. That's it. Double-click `START.bat` and go.

#### What about the terminal tool?

The `terminal` tool internally needs `bash.exe` (Git Bash) to run commands. This is a separate concern from Git (`git.exe`). See "How Terminal Execution Works on Windows" for details on Git Bash vs Git SCM.

**TL;DR:** Hermes runtime = `cmd.exe → python.exe`. Hermes terminal shell = `bash.exe`. For Windows-native commands, use `cmd.exe //c "command"`.

Reason: The terminal tool wraps commands in a fence protocol that uses bash syntax:
```bash
printf "__HERMES_FENCE_a9f7b3__\n"  # output boundary marker
echo $?                               # exit code capture
cmd1; cmd2                             # command chaining
```
These are bash-specific. cmd.exe doesn't support `$?`, `printf`, or semicolon chaining the same way.

### Shell Resolution Order (`tools/environments/local.py` → `_find_bash()`)

On Windows, `_find_bash()` searches in this order:

1. **`HERMES_GIT_BASH_PATH` env var** — full path to `bash.exe` (user override)
2. **`%LOCALAPPDATA%\Programs\Git\bin\bash.exe`** — per-user Git install
3. **`%ProgramFiles%\Git\bin\bash.exe`** — system-wide Git (usually `C:\Program Files\Git\bin\bash.exe`)
4. **`%ProgramFiles(x86)%\Git\bin\bash.exe`** — 32-bit Git on 64-bit Windows
5. **`shutil.which("bash")`** — PATH lookup (last resort, finds whatever `bash` resolves to)

### Why It Breaks on Portable / Non-C: Drive Setups

Step 5 (`shutil.which("bash")`) is dangerous on Windows 11: it finds **`C:\Windows\System32\bash.exe`** (the WSL AppX stub) **before** Git Bash, because `System32` is typically ahead of `Git\bin` in `%PATH%`.

When Git Bash is installed on a **non-C: drive** (e.g., `D:\Program Files\Git\bin\bash.exe`), steps 2–4 all miss (they only check C: paths). Step 5 then picks up the WSL stub, which can't mount the Windows filesystem correctly and outputs:
```
D:\WSL\Ubuntu-24.04\ext4.vhdx → ERROR_PATH_NOT_FOUND
```

**The portable package itself is pure Python** (embedded Python in `python_embedded/`). The ONLY external runtime dependency for terminal commands is Git Bash. Everything else (Python, Node.js, Web UI) is bundled.

**Key detail on how Popen is called:** The actual invocation in `tools/environments/local.py` lines 443-454 is:
```python
proc = subprocess.Popen(
    [user_shell, "-lic", fenced_cmd],  # bash -lic = interactive login shell with command
    text=True,
    cwd=work_dir,
    encoding="utf-8",
    errors="replace",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    stdin=subprocess.PIPE if effective_stdin is not None else subprocess.DEVNULL,
)
```
Note the encoding="utf-8" and errors="replace" — these are why garbled WSL output shows replacement characters (�) instead of crashing.

### Windows: How to check if Hermes is using WSL (and how to remove it)

**Check if installer was WSL-based:** Look at `~/.hermes/install-state.json`:
```json
{
    "distro": "Ubuntu-24.04",
    "port": "8648",
    "url": "http://localhost:8648/..."
}
```
If `distro` is set, the install wizard originally configured through WSL.

**Gateway tells you the active directory:** `~/.hermes/gateway_state.json`:
```json
{"argv": ["E:\\hema-fix\\hermes_cli\\main.py", "gateway"]}
```
The `argv` field shows which installation directory is actually running.

**The WSL stub problem (root cause of garbled terminal output):**

The WSL "stub" is a **0-byte AppX executable** that acts as a launcher for the WSL VM. It's found in TWO places in PATH on Windows 11:

1. `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe` (per-user, typically FIRST in PATH)
2. `C:\Windows\System32\bash.exe` (system-wide)

Both are **0 bytes** — they're not real bash. They just forward execution to the WSL Linux VM via `wsl.exe`. On systems where WSL is broken (no distro installed, enterprise logon restrictions, WSL on a different drive that isn't mounted), it fails with `ERROR_PATH_NOT_FOUND`.

**Why the WindowsApps per-user path is especially dangerous:** Modern Windows 11 puts `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps` at the **very front** of PATH. This means `where bash` finds the WSL stub BEFORE any real Git Bash. Even if Git Bash is on D: drive, the stub is hit first.

**Quick fix (no need to remove WSL entirely):** Just delete the bash.exe stub file from WindowsApps — this immediately fixes terminal output without affecting WSL functionality (you can still use `wsl` command directly):

```
del /f /q "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe"
```

The real Git Bash is typically at a path like `D:\\Program Files\\Git\\bin\\bash.exe`.

**Complete WSL removal (if you want WSL gone entirely):**

A full `remove_wsl_completely.bat` script:
```bat
@echo off
chcp 65001 >nul
:: Step 1: Shutdown and unregister all WSL distros
wsl --shutdown
wsl --unregister Ubuntu-24.04 2>nul
wsl --unregister Ubuntu 2>nul
wsl --unregister debian 2>nul
:: Step 2: Disable WSL Windows feature
dism /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart /quiet
:: Step 3: Delete the WSL bash stub (this is the critical fix)
takeown /f "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" /a >nul 2>&1
icacls "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" /grant Administrators:F >nul 2>&1
del /f /q "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" >nul 2>&1
:: Step 4: Clean up WSL user data
rmdir /s /q "%LOCALAPPDATA%\Packages\CanonicalGroupLimited.Ubuntu*" >nul 2>&1
```
**Must reboot** after running for changes to fully take effect. After reboot, `where bash` should only show the real Git Bash path.

**To completely remove WSL** (does NOT affect Git Bash — they are completely separate):

PowerShell (as Administrator):
```powershell
# 1. List installed distros
wsl --list --verbose

# 2. Unregister all distros (deletes their virtual disks)
wsl --unregister Ubuntu-24.04     # or whatever distro you see

# 3. Shutdown WSL
wsl --shutdown

# 4. Disable WSL feature
dism /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart

# 5. (Optional) Also disable VirtualMachinePlatform
dism /online /disable-feature /featurename:VirtualMachinePlatform /norestart

# 6. Delete WSL virtual hard disks (can be GB-sized)
Remove-Item "D:\WSL" -Recurse -Force   # your WSL install dir
# Also check: %USERPROFILE%\AppData\Local\Packages\
```

**Why this helps Hermes:** After removing WSL, `shutil.which("bash")` in `_find_bash()` will NOT find the WSL stub anymore (no `C:\\Windows\\System32\\bash.exe` to confuse it). But you still need `HERMES_GIT_BASH_PATH` if Git Bash is on a non-C: drive, because the hardcoded paths only check C: drives.

### Windows Portable: Terminal returns binary/garbled output
**Symptom:** `terminal()` returns `�e�l\�x�v...ERROR_PATH_NOT_FOUND` with binary data instead of command output.

**Cause:** The terminal tool is finding WSL's `bash.exe` stub (in `System32`) instead of Git Bash. WSL is not installed/used in portable mode.

**Fix:** Set `HERMES_GIT_BASH_PATH` to your actual Git Bash executable:
```yaml
# In ~/.hermes/.env:
HERMES_GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe
# Or if installed per-user:
# HERMES_GIT_BASH_PATH=C:\Users\<username>\AppData\Local\Programs\Git\bin\bash.exe
```
To find your Git Bash: run `where bash` in cmd/PowerShell, and use the path under `Git\bin\bash.exe`, NOT `System32\bash.exe`.

### Web UI: Messages disappear after page refresh (AI replies missing)

**Symptom:** After closing and reopening the Web UI browser tab, you can only see your own messages — the AI assistant's replies are gone.

**Root cause:** The Web UI Node.js server (`webui/dist/server/index.js`) has a bug in `handleRun()`. The function stores user messages to the local SQLite DB via `addMessage()`, but **assistant (AI) response messages are only kept in the in-memory `sessionMap` object and never written to the database**. On page refresh, `resumeSession()` → `loadSessionStateFromDb()` reads from SQLite, which only has user messages.

**Fix location:** In `webui/dist/server/index.js`, after `run.completed` event processing, call the DB persistence function (similar to how user messages call `addMessage()`/`pW()`). The function signature is like:
```javascript
pW({session_id: W, role: "assistant", content: finalContent, timestamp: ...})
```
This needs to be added in the `run.completed` case handler where the assistant's final output is assembled.

**Note:** The server JS is a bundled single file (~7MB). Search for `handleRun`, `run.completed`, and `addMessage` patterns to find the code section.

### Windows Portable: Diagnostic technique (bypass broken tools)

**Symptom:** `read_file` returns "File not found" for existing files, `terminal` returns garbled binary output, `search_files` fails without ripgrep.

**Workaround:** Use `execute_code` with Python's built-in `open()` to read files and `os.walk()`/`os.listdir()` to explore the filesystem:
```python
# Read a file that read_file can't find
import os
with open(r"C:\Users\Keke_\.hermes\config.yaml", "r", encoding="utf-8", errors="replace") as f:
    print(f.read())

# List directory with file sizes
for root, dirs, files in os.walk(r"C:\Users\Keke_\.hermes"):
    for f in files:
        path = os.path.join(root, f)
        print(f"{path} ({os.path.getsize(path)} bytes)")
```
This avoids the path resolution bug in `read_file` and encoding issues in `terminal`.

### Windows Portable: Find which installation is actually running (E:/ vs F:/)

**Symptom:** Multiple copies of Hermes exist on different drives (e.g., `E:\hema-fix` and `F:\hema-fix\hema-fix`). You need to know which one is currently active.

**Diagnostic script** (run via `execute_code`):
```python
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. Check which Python is in use
print(f"sys.executable: {sys.executable}")

# 2. Check PYTHONPATH (tells you which install dir is on the Python path)
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")

# 3. Check gateway_state.json for the gateway's argv (actual startup path)
hermes_dir = os.path.join(os.environ.get("USERPROFILE", "C:\Users\Keke_"), ".hermes")
gw_path = os.path.join(hermes_dir, "gateway_state.json")
if os.path.exists(gw_path):
    with open(gw_path, "r", encoding="utf-8") as f:
        print(f"\ngateway_state.json:\n{f.read()}")

# 4. Check if two copies are identical (compare main.py hashes)
def file_hash(path):
    with open(path, "rb") as f:
        return hash(f.read())

f_main = r"F:\hema-fix\hema-fix\hermes_cli\main.py"
e_main = r"E:\hema-fix\hermes_cli\main.py"
if os.path.exists(f_main) and os.path.exists(e_main):
    print(f"F: main.py hash: {file_hash(f_main)}")
    print(f"E: main.py hash: {file_hash(e_main)}")
    print(f"Identical: {file_hash(f_main) == file_hash(e_main)}")

# 5. Check config.yaml for port setting (old=8644, new=8642)
config_path = os.path.join(hermes_dir, "config.yaml")
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        print(f"\nconfig.yaml:\n{f.read()}")
```

**Key indicators from gateway_state.json:**
- `argv` field shows the actual startup path (e.g., `["E:\\hema-fix\\hermes_cli\\main.py", "gateway"]`)
- `exit_reason` field like `"api_server: failed to connect"` indicates port conflict or stale gateway

**To switch active installation:** Update `C:\Users\<username>\.hermes\config.yaml` to point to the desired path and restart the gateway.

### Windows Portable: "tirith spawn failed" warnings on every tool call
**Symptom:** Every tool call logs `WARNING tools.tirith_security: tirith spawn failed: [WinError 2] 系统找不到指定的文件。`

**Cause:** tirith security sandbox has no Windows binary. The file `~/.hermes/.tirith-install-failed` contains `unsupported_platform`.

**Fix:** Disable tirith in `~/.hermes/config.yaml`:
```yaml
security:
  tirith:
    enabled: false
```

### Windows Portable: GBK/UnicodeEncodeError in Python output
**Symptom:** `UnicodeEncodeError: 'gbk' codec can't encode character '\ufffd'` when Python scripts call `print()`.

**Cause:** Chinese Windows defaults to GBK encoding for stdout. UTF-8 characters in tool output cause crashes.

**Fix:** Set `PYTHONIOENCODING=utf-8` in `~/.hermes/.env`:
```
PYTHONIOENCODING=utf-8
```

### Windows Portable: read_file returns "File not found" for existing files
**Symptom:** `read_file()` returns `"File not found"` for files confirmed to exist via `os.walk()` or `Python open()`.

**Cause:** Likely path encoding mismatch or file lock contention on Windows. Python's `open()` with raw paths (bypassing read_file's path resolution) works as a workaround.

**Workaround:** Use `execute_code` with Python's built-in `open()` to read files instead:
```python
from hermes_tools import terminal
# Or use execute_code with direct Python file I/O
```
The `read_file` tool itself works correctly when invoked directly (the error in logs was from diagnostic code, not the tool itself).

### Windows Portable: Key file paths
- Hermes install: `E:\hema-fix\` (or wherever you unzipped the portable)
- User config: `C:\Users\<username>\.hermes\`
- Config: `~/.hermes/config.yaml`
- API keys: `~/.hermes/.env`
- Memory: `~/.hermes/memories/USER.md`
- SOUL: `~/.hermes/SOUL.md` (or `E:\hema-fix\assets\SOUL.md`)
- Skills: `~/.hermes/skills/`
- Sessions (JSON): `~/.hermes/sessions/`
- Session DB: `~/.hermes/sessions.db` (may be 0 bytes — JSON files are primary)
- State DB: `~/.hermes/state.db` (SQLite, working)
- Logs: `~/.hermes/logs/hermes.log`, `~/.hermes/logs/errors.log`, `~/.hermes/logs/gateway.log`
- Python: `E:\hema-fix\python_embedded\python.exe`
- Node: `E:\hema-fix\node_embedded\node.exe`

### Voice messages not working
1. Check stt.enabled is true in config.yaml
2. Check a provider is available (faster-whisper installed, or API key set)
3. Restart gateway after config changes (/restart)

### Tool not available
1. Run `hermes tools` to check if the toolset is enabled for your platform
2. Some tools need env vars — check the env file
3. Use /reset after enabling tools

### Model/provider issues
1. Run `hermes doctor` to check configuration
2. Run `hermes login` to re-authenticate
3. Check the env file has the right API key

### Changes not taking effect
- Gateway: /reset for tool changes, /restart for config changes
- CLI: start a new session

### Skills not showing up
1. Check `hermes skills list` shows the skill
2. Check `hermes skills config` has it enabled for your platform
3. Load explicitly with `/skill name` or `hermes -s name`
