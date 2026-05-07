# Hermes Agent — Windows 便携版

AI 助手客户端，一键安装，无需管理员权限，不写注册表，删文件夹即卸载。

---

## 下载

| 版本 | 大小 | 适合人群 |
|------|------|----------|
| **完整版 Full**（推荐） | ~350MB | 想用浏览器界面的用户 |
| **轻量版 Lite** | ~150MB | 只用桌面 GUI 或命令行的用户 |

> 下载地址：[Releases](../../releases)

---

## 安装步骤

### 1. 解压

右键压缩包 → **解压到当前文件夹**

建议解压到路径较短的位置，例如 `D:\Hermes\`（避免路径过长导致问题）

### 2. 运行安装脚本

双击 `install.bat`

> 如果弹出蓝色安全警告，点击 **"更多信息"** → **"仍要运行"**

出现选择界面：

```
[1] 轻量版 Lite  (~150MB)
[2] 完整版 Full  (~350MB，推荐)

请输入 1 或 2：
```

输入 `2` 后回车，等待安装完成（约 10-20 分钟，取决于网速）。

### 3. 填写 API Key

双击 `HermesSetup.exe`，首次启动会引导填写 AI 服务的 API Key（如 Claude、GPT 等）。

---

## 启动 Web UI（仅完整版）

安装完成后有两种方式打开 Web UI：

**方式 A：** 双击 `start_webui.bat`

**方式 B：** 打开 `HermesSetup.exe` → 点击顶部 **"Web UI"** 标签 → **"启动 Web UI"** → **"打开浏览器"**

浏览器将自动打开 `http://localhost:8648`

---

## 功能一览

| 功能 | 轻量版 | 完整版 |
|------|--------|--------|
| Python 3.13 嵌入式运行时 | ✅ | ✅ |
| Tkinter 桌面 GUI | ✅ | ✅ |
| 100+ AI 工具 | ✅ | ✅ |
| 89+ 技能（Skills） | ✅ | ✅ |
| LM Studio 本地模型支持 | ✅ | ✅ |
| 浏览器自动化（Puppeteer） | ✅ | ✅ |
| **Web UI 浏览器界面** | ❌ | ✅ |
| **多会话聊天管理** | ❌ | ✅ |
| **Gateway（Telegram/Discord/Slack 等）** | ❌ | ✅ |
| **用量分析 / 定时任务** | ❌ | ✅ |

---

## 目录结构

```
安装目录/
├── install.bat              # 安装脚本（首次运行）
├── HermesSetup.exe          # 主界面（日常使用）
├── hermes_gui.bat           # 桌面 GUI 启动
├── hermes.bat               # 命令行启动
├── start_webui.bat          # 启动 Web UI（完整版）
├── stop_webui.bat           # 停止 Web UI
├── start_hermes_gateway.bat # 启动 API 网关
├── python_embedded/         # Python 3.13（便携）
├── node_embedded/           # Node.js 23（完整版）
└── webui/                   # Web UI 文件（完整版）
```

用户数据保存在：
- `%USERPROFILE%\.hermes\` — Agent 配置、技能、权限
- `%USERPROFILE%\.hermes-web-ui\` — Web UI 数据、认证 token

---

## 常见问题

**Q: 安装时提示"下载失败"**  
A: 检查网络连接，重新双击 `install.bat`，脚本会自动跳过已完成的步骤。

**Q: 浏览器打开是空白页**  
A: 等待 30 秒后刷新。若仍无效，查看日志：`%USERPROFILE%\.hermes-web-ui\server.log`

**Q: 提示端口 8648 被占用**  
A: 脚本会自动尝试释放端口。若失败，重启电脑后再试。

**Q: 杀毒软件报警**  
A: 属于误报。`HermesSetup.exe` 是用 MinGW 编译的 C 程序，可将安装目录加入杀毒软件白名单。

**Q: 如何卸载**  
A: 直接删除安装目录即可。如需清理用户数据，同时删除 `%USERPROFILE%\.hermes\` 和 `%USERPROFILE%\.hermes-web-ui\`。

**Q: 轻量版能升级到完整版吗**  
A: 可以。在安装目录下运行：
```
install.bat full
```

---

## 升级

```bat
:: 轻量版升级为完整版（只补充下载 Node.js 和 Web UI）
install.bat full

:: 重新安装（已有组件自动跳过）
install.bat
```

---

## 技术信息

- Python: 3.13.12 embedded（嵌入式，不影响系统 Python）
- Node.js: v23.11.0 portable（完整版，嵌入在 node_embedded/）
- Web UI: [hermes-web-ui](https://github.com/EKKOLearnAI/hermes-web-ui) v0.5.13
- 端口: Gateway 8642，Web UI 8648
- 协议: MIT

---

## 相关项目

- [hermes-web-ui](https://github.com/EKKOLearnAI/hermes-web-ui) — Web 界面原始项目
- [portable-hermes-agent](https://github.com/aivrar/portable-hermes-agent) — 原始安装脚本
