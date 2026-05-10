# Hermes Agent - Windows 便携版 (Hema_v)

> **分支:** `fix/install-bat-path-issues`  
> **基于:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT)  
> **CDN:** http://121.40.165.216/hermes-cdn/files/  
> **下载:** http://121.40.165.216/hermes-cdn/files/hema-fix.zip

---

## 目录

- [架构概览](#架构概览)
- [安装流程](#安装流程)
- [已知问题与修复](#已知问题与修复)
  - [CDN & 部署](#cdn--部署)
  - [install.bat 修复](#installbat-修复)
  - [Web UI 修复](#web-ui-修复)
  - [Gateway 修复](#gateway-修复)
  - [会话持久化](#会话持久化)
  - [安装器 GUI](#安装器-gui)
- [待解决问题](#待解决问题)
- [版本历史](#版本历史)
- [开发计划](#开发计划)

---

## 架构概览

```
用户 Windows 机器
├── hema-fix/
│   ├── install.bat           ← 命令行安装
│   ├── installer_gui.bat     ← GUI 安装器入口
│   ├── installer_gui.ps1     ← PowerShell GUI 安装器
│   ├── hermes.bat            ← CLI 模式启动
│   ├── hermes_gui.bat        ← 桌面 GUI 启动
│   ├── start_webui.bat       ← Web UI 启动 (自动拉起网关)
│   ├── start_hermes_gateway.bat ← 网关启动
│   ├── python_embedded/      ← Python 3.13.12 嵌入式
│   │   ├── Lib/site-packages/  ← pip + 所有依赖
│   │   └── Scripts/hermes.exe  ← Windows exe 入口
│   ├── node_embedded/        ← Node.js 23.11.0 便携包
│   ├── webui/                ← hermes-web-ui v0.5.13
│   └── node_modules/         ← Node.js 依赖
│
├── C:\Users\<用户>\.hermes\   ← Hermes 数据目录
│   ├── config.yaml           ← 配置文件
│   ├── .env                  ← API Key 等环境变量
│   ├── state.db              ← SQLite 会话数据库
│   ├── sessions/             ← JSON 会话文件
│   └── ...
│
└── CDN (121.40.165.216)
    └── /hermes-cdn/files/
        ├── node-v23.11.0-win-x64.zip
        ├── 7za.exe
        ├── hermes-webui-bundle-v0.5.13-win-x64.7z
        ├── HermesSetup.exe
        └── hema-fix.zip
```

---

## 安装流程

### 1. 下载并解压

```
下载: http://121.40.165.216/hermes-cdn/files/hema-fix.zip
解压: 7za.exe x hema-fix.zip -oF:\hema-fix
```

⚠️ 确保解压后路径是 `F:\hema-fix\install.bat`，不是 `F:\hema-fix\hema-fix\install.bat`。

⚠️ 解压目录名不要包含括号（如 `(13)`），CMD 会把 `)` 当成代码块结束符。

### 2. 安装

```batch
:: GUI 方式（推荐）
F:\hema-fix\installer_gui.bat

:: 命令行方式
F:\hema-fix\install.bat full
```

### 3. 配置 API Key

安装完成后编辑 `C:\Users\<用户名>\.hermes\.env`：

```
OPENROUTER_API_KEY=sk-or-xxxxxxxx
```

### 4. 启动

双击桌面快捷方式 **Hema Web 管理界面**，浏览器自动打开 `http://localhost:8648`。

---

## 已知问题与修复

### CDN & 部署

| 日期 | 问题 | 修复 | 状态 |
|------|------|------|------|
| 2026-05-07 | CDN 缺少 Node.js & 7za | 手动下载 node-v23.11.0-win-x64.zip (npmmirror) + 7za.exe | ✅ |
| 2026-05-07 | CDN 路径 `/var/www/hermes-cdn/` 不存在 | 宝塔，实际路径 `/www/wwwroot/hermes-cdn/`，建软链接 | ✅ |
| 2026-05-07 | GitHub Actions 上传失败 | 建 SSH deploy key，配置 Secrets (CDN_HOST, CDN_USER, CDN_SSH_KEY) | ✅ |
| 2026-05-07 | GitHub 直连超时 | CDN 服务器在中国大陆，GitHub 间歇性不可达 | ⚠️ |

#### GitHub Secrets 配置

在 Hema_v 仓库 Settings → Secrets → Actions 中设置：

| Secret | 值 |
|--------|-----|
| `CDN_HOST` | `121.40.165.216` |
| `CDN_USER` | `root` |
| `CDN_SSH_KEY` | deploy key 私钥内容 |

### install.bat 修复

#### Bug 1: LF 换行导致 CMD 闪退

**症状:** 双击 .bat 文件，CMD 窗口闪一下立即关闭，无任何输出。

**根因:** GitHub API 下载的文件使用 Unix 换行 (`\n` LF)，Windows CMD 需要 `\r\n` (CRLF)。LF 导致 CMD 解析混乱。

**修复:** 所有 .bat 文件统一转换为 CRLF。

```python
# 修复前: @echo off\x0a  (LF only)
# 修复后: @echo off\x0d\x0a  (CRLF)
text = text.replace('\r\n', '\n').replace('\r', '\n')
text = text.replace('\n', '\r\n')
```

**影响文件:** install.bat, hermes.bat, start_webui.bat, start_hermes_gateway.bat, installer_gui.bat 等共 12 个 .bat 文件。

---

#### Bug 2: `::` 注释在 `if ()` 块中导致语法错误

**症状:** `... was unexpected at this time`

**根因:** CMD 中 `::` 本质是标签，放在 `if (...) else (...)` 括号块内会导致解析器崩溃。

**修复:** 所有括号块内的 `::` 改为 `rem`。

```batch
:: 修复前（崩溃）
if %errorlevel% neq 0 (
    :: Python 3.13+ embedded must use ensurepip
    "%PYTHON_EXE%" -m ensurepip --upgrade --default-pip
)

:: 修复后
if %errorlevel% neq 0 (
    rem Python 3.13+ embedded must use ensurepip
    "%PYTHON_EXE%" -m ensurepip --upgrade --default-pip
)
```

---

#### Bug 3: `goto` 在 `if ()` 块中导致语法错误

**症状:** `skipping. was unexpected at this time`

**根因:** CMD 不允许 `goto` 出现在 `()` 块内（与 Bug 2 同类问题）。

**修复:** 所有 `goto` 改为平铺式 (`if not exist ... goto`)。

```batch
:: 修复前（崩溃）
if exist "%WEBUI_NPM_SERVER%" (
    echo [OK] hermes-web-ui already installed (npm mode), skipping.
    goto :skip_webui
)

:: 修复后
if not exist "%WEBUI_NPM_SERVER%" goto :webui_check_bundle
echo [OK] hermes-web-ui already installed (npm mode), skipping.
goto :skip_webui
:webui_check_bundle
```

---

#### Bug 4: `%~dp0` 尾部 `\` 与重定向冲突

**症状:** `\hema-repo\ was unexpected at this time`

**根因:** `%~dp0` 自带尾部反斜杠（如 `C:\path\hema-repo\`）。与 `>` 重定向符连在一起时 CMD 误解析（如 `C:\path\hema-repo\>` 中的 `\>` 被当成转义序列）。

**修复:** 脚本开头去掉尾部 `\`，所有路径拼接显式加 `\`。

```batch
:: 修复
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PYTHON_DIR=%SCRIPT_DIR%\python_embedded"
```

⚠️ **教训:** 必须确保所有后续引用 `%SCRIPT_DIR%` 的地方都显式加了 `\`，遗漏会导致路径拼接错误（如 `D:\HermesAgentnode_tmp` 而不是 `D:\HermesAgent\node_tmp`）。

---

#### Bug 5: Python 3.13 嵌入式 `get-pip.py` 失败

**症状:**
```
ModuleNotFoundError: No module named 'distutils'
ERROR: Failed to install pip.
```

**根因:** Python 3.12+ 移除了 `distutils`，旧版 `get-pip.py` 依赖它。

**尝试的修复路径:**
1. `ensurepip` → 嵌入式 Python 不包含此模块 ❌
2. `get-pip.py` + 预装 setuptools → 下载超时 ❌
3. `python -m zipfile -e` 解压 wheel → 引号问题 ❌
4. 写临时 .py 文件 → 括号问题 ❌

**最终方案:** 预先在 python_embedded/ 中解压好 pip + 依赖，安装时直接跳过。

```python
# 预装 pip-26.1.1.whl 到 python_embedded/Lib/site-packages/
zipfile.ZipFile('pip-latest.whl').extractall('python_embedded/Lib/site-packages')
```

---

#### Bug 6: 文件夹名包含括号

**症状:** 
```
C:\Users\...\HermesAgent-Complete-Offline-v0.5.13 (13)\hema-repo
                                                ↑ 这个 ) 炸了所有 if 块
```

**根因:** Windows 下载同名文件自动加 `(13)` 后缀。CMD 把路径中的 `)` 当成代码块结束符。

**修复方案:**
1. 教育用户不要用含括号的文件夹名 ⚠️
2. 脚本中所有含路径变量的 `if ()` 块改为 `if exist ... goto` 平铺模式 ✅

---

#### Bug 7: 缺少 PyPI 镜像

**症状:** `pip install` 极慢（国内直连 PyPI）。

**修复:** 所有 `pip install` 命令添加清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

---

#### Bug 8: Gateway 启动缺少 config.yaml

**症状:**
```
API Error 500: {"error":"ENOENT: no such file or directory, 
copyfile 'C:\\Users\\xxx\\.hermes\\config.yaml' -> '...config.yaml.bak'"}
```

**修复:** `install.bat` 安装时自动从 `cli-config.yaml.example` 创建 `~/.hermes/config.yaml`。

```batch
if not exist "%USERPROFILE%\.hermes\config.yaml" (
    copy "%SCRIPT_DIR%\cli-config.yaml.example" "%USERPROFILE%\.hermes\config.yaml" >nul
)
```

---

#### Bug 9: `echo %SCRIPT_DIR%>` 重定向前后顺序

**症状:** CMD 把 `\>` 当转义。

**修复:** 重定向放到命令前面：`> "!PTH_FILE!" echo %SCRIPT_DIR%`。

---

### Web UI 修复

#### Bug 10: Gateway 启动时 OSError

**症状:**
```
OSError: [WinError 11] 试图加载格式不正确的程序。
at gateway/status.py:370 os.kill(pid, 0)
```

**根因:** Unix 用 `os.kill(pid, 0)` 检测进程是否存在。Windows 上信号 0 不存在，抛 `OSError` 而非 `ProcessLookupError`。

**修复:** 
```python
# gateway/status.py 第 371 行
- except (ProcessLookupError, PermissionError):
+ except (ProcessLookupError, PermissionError, OSError):
```

---

#### Bug 11: API Server 不写 session_db

**症状:** Web UI 对话不保存到 SQLite（`sessions export` 返回空）。

**根因:** `gateway/platforms/api_server.py` 创建 AIAgent 时没传 `session_db` 参数，导致 assistant 消息不入库。

**修复:**
1. `APIServerAdapter.__init__` 添加 `session_db` 参数
2. `_create_agent` 方法中 `AIAgent(session_db=self._session_db, ...)`
3. `gateway/run.py` 中 `APIServerAdapter(config, session_db=self._session_db)`

---

#### Bug 12: 平台描述误导 LLM

**症状:** Hermes Agent 使用 bash 语法（`ls`、`/` 路径），Windows CMD 不支持。

**根因:** `tools/terminal_tool.py` 第 369 行:
```python
_PLATFORM_DESC = "Windows (Git Bash)"  
```

**修复:** 改为 `"Windows (CMD)"`，反映实际的 local backend。

---

#### Bug 13: GBK 编码冲突

**症状:** `UnicodeEncodeError: 'gbk' codec can't encode character`

**根因:** 中文 Windows 系统 locale 是 GBK，Python stdout 默认使用系统编码。

**修复:** 启动脚本添加 `PYTHONIOENCODING=utf-8`。

---

#### Bug 14: tirith 安全模块报错

**症状:** `WARNING: tirith spawn failed: [WinError 2] 系统找不到指定的文件。`

**根因:** tirith 没有 Windows 二进制。

**修复:** 安装时创建 `~/.hermes/.tirith-disabled` 标记文件，脚本静默跳过。

---

#### Bug 15: `npm.cmd` 调用导致脚本挂起

**症状:** 安装过程中 `npm install` 步骤卡住。

**修复:** 所有 npm 调用添加 `call` 前缀。

---

#### Bug 16: Node.js CVE 安全限制

**症状:** Node 23 禁止通过 `execFile` 启动 `.bat` 文件。

**修复:** 优先使用 `python_embedded/Scripts/hermes.exe` 而非 `hermes.bat`。

---

#### Bug 17: npm 模式 bundle 解压路径兼容

**症状:** Web UI npm 安装后路径为 `webui/node_modules/hermes-web-ui/dist/...`，与 bundle 模式路径不同。

**修复:** 自动检测两种路径模式，都支持。

---

#### Bug 18: 中文注释导致 GBK/UTF-8 乱码

**症状:** CMD 窗口显示乱码。

**修复:** 所有注释改为 ASCII。

---

### Gateway 修复

#### Bug 19: Web UI 健康检查超时

**症状:** `health: ERR_CONNECTION_REFUSED`，WebSocket 连接失败。

**根因:** Gateway 没有 API key 无法启动 LLM，但启动流程不依赖 LLM。实际问题是 `os.kill()` 崩溃（详见 Bug 10）。

**修复:** Bug 10 修复后自动解决。

---

#### Bug 20: 端口 8648 冲突

**症状:** Web UI 无法启动，端口被占用。

**修复:** `start_webui.bat` 添加 `netstat` 检测并 `taskkill` 清理。

---

### 会话持久化

#### Bug 21: 两套存储系统不互通

**架构问题:**

| 存储 | 写入方 | 读取方 | 格式 |
|------|--------|--------|------|
| `sessions/*.jsonl` | Gateway SessionStore | (无人) | JSON |
| `state.db` | Agent SessionDB | CLI, session_search | SQLite |

**症状:** `hermes sessions export` 返回空，`session_search` 查不到历史。

**根因:** Gateway 写 JSON 文件，CLI 读 SQLite，互不相通。

**修复:** Bug 11（API Server 接上 session_db）让 Gateway 也写 SQLite，两条线打通。

---

#### Bug 22: Web UI 翻页后 AI 回复消失（上游 Bug）

**症状:** 关闭网页再打开，只能看到用户消息，Hermes 回复全部消失。

**根因:** `hermes-web-ui` (EKKOLearnAI) 的 `handleRun()` 函数：
- 用户消息：`handleMessage()` → `addMessage()` → 直接写本地 SQLite ✅
- AI 回复：`message.delta` → 只存内存 `sessionMap` ❌  
  → `run.completed` → `syncFromHermes()` → 调 Gateway API 获取消息
  → API 成功 → `addMessages()` → 写入 ✅  
  → API 失败 → 静默丢弃 ❌

**影响:** 如果 Gateway API 在 `run.completed` 时刻不稳定（启动慢、崩溃、端口冲突），assistant 消息永久丢失。

**上游 Issue:** https://github.com/EKKOLearnAI/hermes-web-ui/issues （2026-05-09 提交）

**我们的缓解措施:**
- 确保 Gateway 稳定（Bug 10-14 修复）
- `start_webui.bat` 15 秒健康检查，确认 Gateway 就绪再开浏览器
- 安装时自动创建 `config.yaml`

**根本修复:** 需要 `hermes-web-ui` 源码在 `message.delta` 或 `run.completed` 中直接写本地 SQLite，不依赖远程 API 回调。

---

### 安装器 GUI

#### Bug 23: 快捷方式图标为空白

**症状:** 桌面快捷方式显示空白文档图标，而非河马图标。

**根因:** 
1. 快捷方式指向 `cmd /c` → Windows 强制使用 CMD 图标
2. `IconLocation` 设置时机问题

**修复:**
1. 快捷方式直接指向 `.bat` 文件（去掉 `cmd /c`）
2. 先保存快捷方式，再设置图标

---

#### Bug 24: 启动等待期间无反馈

**症状:** Web UI 启动等待 15-30 秒没有任何输出，感觉卡死。

**修复:** 添加进度点 (`<nul set /p =""`) 和启动提示。

---

## 待解决问题

### 1. Web UI assistant 消息持久化 (上游)

**状态:** 已提 Issue，等待 EKKOLearnAI 修复。

**临时方案:** 确保 Gateway 在 `syncFromHermes()` 调用时健康。我们的修复已大幅提高稳定性。

**理想方案:** 在 GitHub Actions 编译 `hermes-web-ui` 前打 patch，
在 `message.delta` 或 `run.completed` 中调用 `addMessage()`。

### 2. 中文系统路径编码

**状态:** 部分修复（PYTHONIOENCODING=utf-8）。

**遗留:** `read_file` 工具在中文路径下可能返回 "File not found"。需要更深入的路径编码兼容。

### 3. 旧对话迁移

**状态:** 不可迁移。

`C:\Users\<用户>\.hermes\sessions\` 中的 JSON 文件是 Gateway 用旧方式存的（Bug 21），包含未写入 SQLite 的 assistant 消息。没有工具能从 JSON 迁移到 SQLite。

### 4. 安装器 .exe 编译

**状态:** 已创建 Actions workflow (`build-installer-exe.yml`)。

**待办:** 触发 workflow 编译 `安装Hermes.exe`。

### 5. Web UI 升级到 v0.5.16

**日期:** 2026-05-10

v0.5.16 修复了"中断时消息丢失"问题，与我们的持久化补丁互补。
- `cdn/version.json` → `webui_version: "0.5.16"`
- `install.bat` → `BUNDLE_VER=0.5.16`
- 需触发 workflow 编译新 bundle

### 6. Windows 终端 Shell 依赖问题

**日期:** 2026-05-10

`tools/environments/local.py` 的 `_find_bash()` 硬依赖 Git Bash，未安装时**直接崩溃**，
所有 terminal 工具不可用。原版 aivrar/portable-hermes-agent 存在同样问题。

**评估的解决方案:**

| 方案 | 复杂度 | 体积 | 说明 |
|------|--------|------|------|
| A: 完整 Git | 低 | +66MB | CDN 已有 Git-2.46.0-64-bit.exe，install.bat 静默安装 |
| B: 提取 bash 最小集 | 高 | +5MB | 从 Git 包提取 bash.exe + msys-2.0.dll，维护成本高 |
| C: busybox-w32 | 中 | +600KB | 单文件 exe，ash shell (bash 兼容子集) |
| D: cmd.exe 兜底 | 低 | 0 | 改一行代码，没 bash 就用 cmd |

**推荐:** A + D 组合 — 优先 Git Bash，没装降级 cmd.exe。用户可选装 Git 获得完整 bash。

**待办:** 实装 cmd.exe 兜底方案。

---

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v0.5.13 | 2026-05-07 | 初始版本，基于 hermes-web-ui v0.5.13 |
| v6.0.1 | 2026-05-08 | install.bat CRLF + goto/:: 修复 |
| v6.0.2 | 2026-05-08 | HermesSetup.exe 集成 |
| v6.0.3 | 2026-05-09 | fix 分支完整打包 |
| v6.0.4 | 2026-05-09 | gateway status.py OSError 修复 |
| v7.0.0 | 2026-05-09 | Windows gateway + Web UI 启动修复 |
| — | 2026-05-10 | Web UI v0.5.16 bump + 持久化 workflow patch + cmd.exe 方案评估 |

---

## 开发计划

### 短期

- [ ] 编译 `安装Hermes.exe` (触发 build-installer-exe workflow)
- [ ] 触发 build-webui-bundle workflow (v0.5.16 + 持久化 patch)
- [ ] **实装 cmd.exe 兜底方案**（`_find_bash()` 降级逻辑）
- [ ] 评估是否需要 bundle Git Bash / busybox

### 中期

- [ ] 安装日志收集（便于远程诊断）
- [ ] 旧 session JSON → SQLite 迁移工具
- [ ] 中文路径兼容性修复
- [ ] 自动更新机制（检测 CDN 新版本）

### 长期

- [ ] NSIS/Inno Setup 完整安装包
- [ ] 多语言安装界面
- [ ] 模块化安装（可以选择不装 Web UI / TTS / ComfyUI）
- [ ] 解决上游 hermes-web-ui 持久化 Bug（等 EKKOLearnAI 合并后移除我们的 patch）
