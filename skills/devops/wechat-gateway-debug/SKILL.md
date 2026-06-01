---
name: wechat-gateway-debug
description: Debug and fix WeChat (iLinkAI) messaging integration for Hermes Agent — diagnose why the agent isn't replying on WeChat after QR code binding
version: 1.0.0
metadata:
  hermes:
    tags: [wechat, weixin, gateway, messaging, iLinkAI, troubleshooting]
---

# WeChat Gateway Debug

Debug why Hermes Agent isn't replying on WeChat after QR code binding via iLinkAI (ilinkai.weixin.qq.com).

## Common Misconception

**扫码绑定 ≠ 自动回复。** 用户在微信上扫码绑定 Hermes Agent 后，通常会以为马上就能对话。但实际上绑定只是完成了微信端的身份认证，真正的消息收发依赖 **Hermes Gateway** 进程在后台运行。

## Quick Diagnostic Checklist

### 1. Check if Gateway is running

```bash
hermes gateway status
```

If it says `✗ Gateway is not running`, that's the root cause — start it with:

```bash
hermes gateway
```

### 2. Check .env for WeChat credentials

```bash
cat ~/.hermes/.env | grep -i weixin
```

Look for:
- `WEIXIN_ACCOUNT_ID=xxx@im.bot` (iLinkAI 账号 ID)
- `WEIXIN_TOKEN=xxx` (iLinkAI Token)
- `WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com`

If these are missing, the user hasn't completed `hermes setup` or manually configured WeChat.

### 3. Check gateway_state.json for past failures

```bash
cat ~/.hermes/gateway_state.json
```

Common exit reasons:
- `api_server: failed to connect` — API server (port 8642) was down when gateway tried to start
- Missing WeChat platform — gateway may not have loaded the WeChat adapter

### 4. Check channel_directory.json

```bash
cat ~/.hermes/channel_directory.json
```

Note: WeChat may NOT appear in channel_directory.json even when configured. This is normal — iLinkAI/WeChat isn't listed as a channel the same way Telegram/WhatsApp are. The `.env` variables are what matter.

### 5. Check gateway logs for WeChat-related errors

```bash
grep -i "weixin\|wechat\|ilinkai\|微信" ~/.hermes/gateway.log | tail -30
```

### 6. Check platforms directory

```bash
ls -la ~/.hermes/platforms/
ls -la ~/.hermes/platforms/pairing/  # usually empty on Windows
```

### 7. Check plugins (WeChat may need a plugin)

```bash
hermes plugins list
```

## Resolution

Most cases are solved by simply starting the gateway:

```bash
# Foreground (for testing):
hermes gateway

# Or as service:
hermes gateway install  # then start
```

If the gateway starts but WeChat still doesn't work:
1. Verify the iLinkAI bot is active (check iLinkAI dashboard)
2. Check firewall doesn't block outbound connections to `ilinkai.weixin.qq.com`
3. Try restarting the gateway with `hermes gateway restart` (if installed as service)

## Pitfalls

- **Gateway crash loop**: If gateway exits immediately, check `gateway_state.json` for `exit_reason`. Common: API server port conflict (8642), missing env vars.
- **No `hermes wechat` CLI command**: Unlike `hermes whatsapp`, there's no dedicated `hermes wechat` subcommand. WeChat is configured via `.env` variables only.
- **Channel directory doesn't show WeChat**: This is expected — don't rely on `channel_directory.json` for WeChat diagnostics.
- **`hermes doctor` may time out on Windows**: Skip it and use the manual checks above instead.
- **Gateway runs but user still gets no reply**: Check if the user's WeChat ID is paired/authorized via `hermes pairing list`.
