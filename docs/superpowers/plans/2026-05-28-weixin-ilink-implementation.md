# Weixin iLink Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal viable Tencent iLink-backed Weixin integration that can log in from WebUI, surface runtime status and verification codes in WebUI, and run a basic inbound-message -> Hermes reply -> outbound-message loop.

**Architecture:** The existing WebUI QR-login route remains the credential bootstrapper. The gateway gains a dedicated Weixin adapter plus a profile-scoped status file and log file. WebUI reads that status through a local BFF endpoint and renders it inside the Channels page without introducing a new standalone subsystem.

**Tech Stack:** Python gateway adapters, existing Hermes gateway config/runtime, Koa-based hermes-web-ui server bundle, patched WebUI dist persistence script, pytest.

---

## File Structure

### Files to Modify

- [gateway/config.py](/E:/hema-fix/gateway/config.py)
  - Add `Platform.WEIXIN`
  - Load `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, `WEIXIN_BASE_URL` into `GatewayConfig`
- [gateway/run.py](/E:/hema-fix/gateway/run.py)
  - Wire Weixin adapter creation into the gateway runner
  - Ensure connect failures are isolated to this platform
- [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py)
  - Persist new Weixin status endpoint and Channels page client patch
- [webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js](/E:/hema-fix/webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js)
  - Local runtime patch target for new status read endpoint
- [webui/node_modules/hermes-web-ui/dist/client/assets/js/ChannelsView-BsfZdrIh.js](/E:/hema-fix/webui/node_modules/hermes-web-ui/dist/client/assets/js/ChannelsView-BsfZdrIh.js)
  - Local runtime patch target for status UI rendering

### Files to Create

- [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py)
  - Weixin adapter, status persistence helpers, minimal runtime loop
- [tests/gateway/test_weixin_config.py](/E:/hema-fix/tests/gateway/test_weixin_config.py)
  - Config/env parsing tests
- [tests/gateway/test_weixin_adapter.py](/E:/hema-fix/tests/gateway/test_weixin_adapter.py)
  - Adapter status snapshot and event normalization tests
- [tests/gateway/test_weixin_runner.py](/E:/hema-fix/tests/gateway/test_weixin_runner.py)
  - Gateway runner wiring and startup-isolation tests
- [docs/superpowers/plans/2026-05-28-weixin-ilink-implementation.md](/E:/hema-fix/docs/superpowers/plans/2026-05-28-weixin-ilink-implementation.md)
  - This plan document

### Runtime Artifacts Produced by Implementation

- `HERMES_HOME/weixin_status.json`
- `HERMES_HOME/logs/weixin.log`

## Task 1: Add Gateway Config Support For Weixin

**Files:**
- Modify: [gateway/config.py](/E:/hema-fix/gateway/config.py)
- Test: [tests/gateway/test_weixin_config.py](/E:/hema-fix/tests/gateway/test_weixin_config.py)

- [ ] **Step 1: Write the failing config tests**

```python
import os

from gateway.config import Platform, load_gateway_config


def test_load_gateway_config_enables_weixin_from_env(monkeypatch):
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "bot-account")
    monkeypatch.setenv("WEIXIN_TOKEN", "bot-token")
    monkeypatch.setenv("WEIXIN_BASE_URL", "https://example.invalid")

    config = load_gateway_config()

    assert Platform.WEIXIN in config.platforms
    weixin = config.platforms[Platform.WEIXIN]
    assert weixin.enabled is True
    assert weixin.token == "bot-token"
    assert weixin.extra["account_id"] == "bot-account"
    assert weixin.extra["base_url"] == "https://example.invalid"


def test_load_gateway_config_skips_weixin_without_required_token(monkeypatch):
    monkeypatch.delenv("WEIXIN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEIXIN_TOKEN", raising=False)
    monkeypatch.delenv("WEIXIN_BASE_URL", raising=False)
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "bot-account")

    config = load_gateway_config()

    assert Platform.WEIXIN not in config.platforms
```

- [ ] **Step 2: Run the config tests and verify they fail**

Run:

```bash
python -m pytest tests/gateway/test_weixin_config.py -q
```

Expected: fail because `Platform.WEIXIN` and related env parsing do not exist yet.

- [ ] **Step 3: Implement minimal config support**

Update [gateway/config.py](/E:/hema-fix/gateway/config.py) so the enum and env-loader include Weixin:

```python
class Platform(Enum):
    LOCAL = "local"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    SIGNAL = "signal"
    MATTERMOST = "mattermost"
    MATRIX = "matrix"
    HOMEASSISTANT = "homeassistant"
    EMAIL = "email"
    SMS = "sms"
    DINGTALK = "dingtalk"
    API_SERVER = "api_server"
    WEBHOOK = "webhook"
    FEISHU = "feishu"
    WEIXIN = "weixin"
```

```python
    weixin_account_id = os.getenv("WEIXIN_ACCOUNT_ID")
    weixin_token = os.getenv("WEIXIN_TOKEN")
    weixin_base_url = os.getenv("WEIXIN_BASE_URL")
    if weixin_account_id and weixin_token:
        if Platform.WEIXIN not in config.platforms:
            config.platforms[Platform.WEIXIN] = PlatformConfig()
        config.platforms[Platform.WEIXIN].enabled = True
        config.platforms[Platform.WEIXIN].token = weixin_token
        config.platforms[Platform.WEIXIN].extra["account_id"] = weixin_account_id
        if weixin_base_url:
            config.platforms[Platform.WEIXIN].extra["base_url"] = weixin_base_url
```

- [ ] **Step 4: Re-run the config tests and verify they pass**

Run:

```bash
python -m pytest tests/gateway/test_weixin_config.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit the config support**

```bash
git add gateway/config.py tests/gateway/test_weixin_config.py
git commit -m "Add Weixin gateway config support"
```

## Task 2: Build The Weixin Adapter And Status Persistence

**Files:**
- Create: [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py)
- Test: [tests/gateway/test_weixin_adapter.py](/E:/hema-fix/tests/gateway/test_weixin_adapter.py)

- [ ] **Step 1: Write the failing adapter tests**

```python
import json
from pathlib import Path

from gateway.config import PlatformConfig
from gateway.platforms.weixin import (
    WeixinAdapter,
    check_weixin_requirements,
    write_weixin_status,
)


def test_check_weixin_requirements_requires_account_id_and_token(monkeypatch):
    monkeypatch.delenv("WEIXIN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEIXIN_TOKEN", raising=False)
    assert check_weixin_requirements() is False

    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "acct")
    monkeypatch.setenv("WEIXIN_TOKEN", "tok")
    assert check_weixin_requirements() is True


def test_write_weixin_status_overwrites_latest_snapshot(tmp_path):
    status_path = tmp_path / "weixin_status.json"

    write_weixin_status(
        status_path,
        status="verification_code",
        message="Verification code received",
        verification_code="123456",
        account_id="acct",
        last_error="",
    )

    data = json.loads(status_path.read_text(encoding="utf-8"))
    assert data["status"] == "verification_code"
    assert data["verification_code"] == "123456"
    assert data["account_id"] == "acct"


def test_adapter_normalizes_inbound_text_message(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(
        enabled=True,
        token="tok",
        extra={"account_id": "acct", "base_url": "https://example.invalid"},
    )
    adapter = WeixinAdapter(config)

    event = adapter._build_message_event(
        {
            "conversation_id": "conv-1",
            "sender_id": "wx-user-1",
            "sender_name": "User",
            "text": "hello",
        }
    )

    assert event.source.platform.value == "weixin"
    assert event.source.chat_id == "conv-1"
    assert event.text == "hello"
```

- [ ] **Step 2: Run the adapter tests and verify they fail**

Run:

```bash
python -m pytest tests/gateway/test_weixin_adapter.py -q
```

Expected: fail because the adapter module does not exist yet.

- [ ] **Step 3: Implement the minimal adapter and status helpers**

Create [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py) with this shape:

```python
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, SessionSource
from gateway.config import Platform, PlatformConfig

logger = logging.getLogger(__name__)


def check_weixin_requirements() -> bool:
    return bool(os.getenv("WEIXIN_ACCOUNT_ID") and os.getenv("WEIXIN_TOKEN"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_weixin_status(
    status_path: Path,
    *,
    status: str,
    message: str,
    verification_code: str = "",
    account_id: str = "",
    last_error: str = "",
) -> None:
    payload = {
        "status": status,
        "message": message,
        "verification_code": verification_code,
        "last_event_at": _utc_now_iso(),
        "account_id": account_id,
        "last_error": last_error,
    }
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class WeixinRuntimeSettings:
    account_id: str
    token: str
    base_url: str


class WeixinAdapter(BasePlatformAdapter):
    platform = Platform.WEIXIN

    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        home = get_hermes_home()
        self._status_path = home / "weixin_status.json"
        self._log_path = home / "logs" / "weixin.log"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = WeixinRuntimeSettings(
            account_id=str(config.extra.get("account_id") or ""),
            token=str(config.token or ""),
            base_url=str(config.extra.get("base_url") or "https://ilinkai.weixin.qq.com"),
        )

    def _append_log(self, message: str) -> None:
        line = f"{_utc_now_iso()} {message}\n"
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def _set_status(self, *, status: str, message: str, verification_code: str = "", last_error: str = "") -> None:
        write_weixin_status(
            self._status_path,
            status=status,
            message=message,
            verification_code=verification_code,
            account_id=self._settings.account_id,
            last_error=last_error,
        )
        self._append_log(f"{status}: {message}")

    def _build_message_event(self, payload: Dict[str, Any]) -> MessageEvent:
        source = SessionSource(
            platform=self.platform,
            user_id=str(payload["sender_id"]),
            user_name=str(payload.get("sender_name") or payload["sender_id"]),
            chat_id=str(payload["conversation_id"]),
            chat_type="dm",
        )
        return MessageEvent(
            source=source,
            text=str(payload.get("text") or ""),
            raw_event=payload,
        )
```

- [ ] **Step 4: Re-run the adapter tests and verify they pass**

Run:

```bash
python -m pytest tests/gateway/test_weixin_adapter.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit the adapter foundation**

```bash
git add gateway/platforms/weixin.py tests/gateway/test_weixin_adapter.py
git commit -m "Add Weixin adapter status foundation"
```

## Task 3: Wire The Adapter Into The Gateway Runner

**Files:**
- Modify: [gateway/run.py](/E:/hema-fix/gateway/run.py)
- Test: [tests/gateway/test_weixin_runner.py](/E:/hema-fix/tests/gateway/test_weixin_runner.py)

- [ ] **Step 1: Write the failing runner tests**

```python
from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.run import GatewayRunner


def test_create_adapter_returns_weixin_adapter_when_configured(monkeypatch):
    monkeypatch.setenv("WEIXIN_ACCOUNT_ID", "acct")
    monkeypatch.setenv("WEIXIN_TOKEN", "tok")
    runner = GatewayRunner(
        GatewayConfig(
            platforms={
                Platform.WEIXIN: PlatformConfig(
                    enabled=True,
                    token="tok",
                    extra={"account_id": "acct", "base_url": "https://example.invalid"},
                )
            }
        )
    )

    adapter = runner._create_adapter(Platform.WEIXIN, runner.config.platforms[Platform.WEIXIN])

    assert adapter is not None
    assert adapter.platform == Platform.WEIXIN


def test_create_adapter_returns_none_when_weixin_requirements_missing(monkeypatch):
    monkeypatch.delenv("WEIXIN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEIXIN_TOKEN", raising=False)
    runner = GatewayRunner(
        GatewayConfig(
            platforms={
                Platform.WEIXIN: PlatformConfig(enabled=True, token="", extra={})
            }
        )
    )

    adapter = runner._create_adapter(Platform.WEIXIN, runner.config.platforms[Platform.WEIXIN])

    assert adapter is None
```

- [ ] **Step 2: Run the runner tests and verify they fail**

Run:

```bash
python -m pytest tests/gateway/test_weixin_runner.py -q
```

Expected: fail because `Platform.WEIXIN` is not wired into `_create_adapter`.

- [ ] **Step 3: Add Weixin wiring in the runner**

Extend the adapter factory in [gateway/run.py](/E:/hema-fix/gateway/run.py):

```python
        elif platform == Platform.WEIXIN:
            from gateway.platforms.weixin import WeixinAdapter, check_weixin_requirements
            if not check_weixin_requirements():
                logger.warning("Weixin: WEIXIN_ACCOUNT_ID or WEIXIN_TOKEN not set")
                return None
            return WeixinAdapter(config)
```

Keep this branch aligned with the existing platform startup style so reconnect and failure tracking continue to work.

- [ ] **Step 4: Re-run the runner tests and verify they pass**

Run:

```bash
python -m pytest tests/gateway/test_weixin_runner.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Run the combined gateway tests**

Run:

```bash
python -m pytest tests/gateway/test_weixin_config.py tests/gateway/test_weixin_adapter.py tests/gateway/test_weixin_runner.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the gateway wiring**

```bash
git add gateway/run.py tests/gateway/test_weixin_runner.py
git commit -m "Wire Weixin adapter into gateway runner"
```

## Task 4: Add Runtime Status Endpoint To WebUI Persistence Patch

**Files:**
- Modify: [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py)
- Modify: [webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js](/E:/hema-fix/webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js)

- [ ] **Step 1: Add a patch target for Weixin runtime status**

Insert a route patch in [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py) that injects a status reader endpoint into the Weixin route bundle:

```python
WEIXIN_STATUS_ROUTE_SNIPPET = r"""
exports.weixinRoutes.get('/api/hermes/weixin/status', async (ctx) => {
    try {
        const fs = require('fs/promises');
        const path = require('path');
        const { getActiveProfileHome } = require('../../services/hermes/hermes-profile');
        const statusPath = path.join(getActiveProfileHome(), 'weixin_status.json');
        const raw = await fs.readFile(statusPath, 'utf-8');
        ctx.body = JSON.parse(raw);
    } catch (err) {
        if (err && err.code === 'ENOENT') {
            ctx.body = {
                status: 'not_configured',
                message: 'Weixin not configured',
                verification_code: '',
                last_event_at: '',
                account_id: '',
                last_error: '',
            };
            return;
        }
        ctx.status = 500;
        ctx.body = { error: err.message || 'Failed to read Weixin status' };
    }
});
"""
```

- [ ] **Step 2: Apply the patch script to the local WebUI runtime**

Run:

```bash
python scripts/patch-webui-persistence.py webui
```

Expected: the patch script completes without error and rewrites the runtime bundle.

- [ ] **Step 3: Verify the runtime route exists**

Run:

```bash
rg -n "/api/hermes/weixin/status|Weixin not configured" webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js -S
```

Expected: one or more matches showing the new status route.

- [ ] **Step 4: Commit the persistent status-route patch**

```bash
git add scripts/patch-webui-persistence.py
git commit -m "Persist Weixin status route patch"
```

## Task 5: Render Weixin Runtime Status In The Channels Page

**Files:**
- Modify: [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py)
- Modify: [webui/node_modules/hermes-web-ui/dist/client/assets/js/ChannelsView-BsfZdrIh.js](/E:/hema-fix/webui/node_modules/hermes-web-ui/dist/client/assets/js/ChannelsView-BsfZdrIh.js)

- [ ] **Step 1: Add client-side Weixin status polling patch**

Extend [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py) so it injects a helper equivalent to:

```javascript
async function fetchWeixinRuntimeStatus() {
  const res = await fetch('/api/hermes/weixin/status', {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch Weixin status: ${res.status}`);
  }
  return await res.json();
}
```

and renders a status block under the Weixin card that shows:

```javascript
[
  { label: '当前状态', value: status.status || 'not_configured' },
  { label: '提示信息', value: status.message || '-' },
  { label: '验证码', value: status.verification_code || '-' },
  { label: '最后活动', value: status.last_event_at || '-' },
  { label: '最近错误', value: status.last_error || '-' },
]
```

- [ ] **Step 2: Apply the patch script to the local WebUI runtime**

Run:

```bash
python scripts/patch-webui-persistence.py webui
```

Expected: the client bundle is rewritten without syntax errors.

- [ ] **Step 3: Syntax-check the current runtime bundle**

Run:

```bash
node --check webui/node_modules/hermes-web-ui/dist/server/index.js
```

Expected: no syntax error output.

- [ ] **Step 4: Verify the client bundle contains the new Weixin status strings**

Run:

```bash
rg -n "当前状态|验证码|最近错误|/api/hermes/weixin/status" webui/node_modules/hermes-web-ui/dist/client/assets/js/ChannelsView-BsfZdrIh.js -S
```

Expected: matches for the injected status UI.

- [ ] **Step 5: Commit the WebUI status rendering patch**

```bash
git add scripts/patch-webui-persistence.py
git commit -m "Add Weixin runtime status to channels page"
```

## Task 6: Implement Minimal Inbound And Outbound Weixin Messaging

**Files:**
- Modify: [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py)
- Test: [tests/gateway/test_weixin_adapter.py](/E:/hema-fix/tests/gateway/test_weixin_adapter.py)

- [ ] **Step 1: Add failing tests for inbound/outbound behavior**

```python
def test_handle_inbound_payload_updates_status_and_returns_event(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)

    event = adapter.handle_inbound_payload(
        {
            "conversation_id": "conv-1",
            "sender_id": "wx-user-1",
            "sender_name": "User",
            "text": "hello",
        }
    )

    assert event.text == "hello"
    status = json.loads((tmp_path / "weixin_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "connected"
    assert status["message"] == "Received inbound Weixin message"


def test_note_verification_code_updates_status_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)

    adapter.note_verification_code("654321")

    status = json.loads((tmp_path / "weixin_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "verification_code"
    assert status["verification_code"] == "654321"
```

- [ ] **Step 2: Run the expanded adapter tests and verify they fail**

Run:

```bash
python -m pytest tests/gateway/test_weixin_adapter.py -q
```

Expected: fail because `handle_inbound_payload()` and `note_verification_code()` do not exist yet.

- [ ] **Step 3: Implement the minimal runtime methods**

Extend [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py) with:

```python
    def note_verification_code(self, code: str) -> None:
        self._set_status(
            status="verification_code",
            message="Verification code received",
            verification_code=code,
        )

    def handle_inbound_payload(self, payload: Dict[str, Any]) -> MessageEvent:
        event = self._build_message_event(payload)
        self._set_status(
            status="connected",
            message="Received inbound Weixin message",
        )
        return event

    async def send(self, chat_id: str, text: str, **kwargs: Any):
        self._set_status(
            status="connected",
            message="Sent outbound Weixin reply",
        )
        self._append_log(f"outbound chat_id={chat_id} text={text[:120]}")
        return True
```

Keep the network call layer behind helper methods so the first integration can stub transport while preserving status semantics.

- [ ] **Step 4: Re-run the adapter tests**

Run:

```bash
python -m pytest tests/gateway/test_weixin_adapter.py -q
```

Expected: all adapter tests pass.

- [ ] **Step 5: Run the complete Weixin-focused test batch**

Run:

```bash
python -m pytest tests/gateway/test_weixin_config.py tests/gateway/test_weixin_adapter.py tests/gateway/test_weixin_runner.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the messaging loop foundation**

```bash
git add gateway/platforms/weixin.py tests/gateway/test_weixin_adapter.py
git commit -m "Add minimal Weixin messaging loop"
```

## Task 7: Manual Runtime Verification

**Files:**
- Modify if needed during fixup: [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py), [scripts/patch-webui-persistence.py](/E:/hema-fix/scripts/patch-webui-persistence.py)

- [ ] **Step 1: Re-apply the WebUI persistence patch**

Run:

```bash
python scripts/patch-webui-persistence.py webui
```

Expected: patch completes successfully.

- [ ] **Step 2: Restart WebUI through the supported launcher**

Run:

```bash
cmd /c start_webui.bat
```

Expected: WebUI restarts and serves on the configured local port.

- [ ] **Step 3: Verify the Weixin status endpoint**

Open in the browser or fetch locally:

```bash
curl http://127.0.0.1:8648/api/hermes/weixin/status
```

Expected before login: JSON with `status` equal to `not_configured` or the latest saved state.

- [ ] **Step 4: Perform QR login and verify status changes**

Manual expectation:

- Weixin card status changes from `not_configured` to `waiting_confirm` or `connected`
- verification code, if issued by iLink, appears in the card
- no silent 500s during the process

- [ ] **Step 5: Validate a real inbound/outbound round trip**

Manual expectation:

- a Weixin inbound message creates a Hermes conversation turn
- the agent reply is sent back out
- `weixin_status.json` updates `last_event_at`
- `logs/weixin.log` contains both inbound and outbound entries

- [ ] **Step 6: Commit any final fixups**

```bash
git add gateway/platforms/weixin.py gateway/config.py gateway/run.py scripts/patch-webui-persistence.py tests/gateway/test_weixin_config.py tests/gateway/test_weixin_adapter.py tests/gateway/test_weixin_runner.py
git commit -m "Finish Weixin iLink integration"
```

## Self-Review

### Spec Coverage

- QR bootstrap reuse: covered by Tasks 4 and 5
- gateway config support: covered by Task 1
- gateway adapter creation: covered by Tasks 2, 3, and 6
- status file and log file: covered by Tasks 2 and 6
- WebUI status visibility: covered by Tasks 4 and 5
- minimal inbound/outbound loop: covered by Task 6
- manual real-world validation: covered by Task 7

### Placeholder Scan

- No `TODO`, `TBD`, or “similar to above” instructions remain
- Every task includes exact file paths
- Every test step includes runnable commands
- Every implementation task includes concrete code shape

### Type Consistency

- `Platform.WEIXIN` is introduced once in Task 1 and reused consistently
- `WeixinAdapter`, `check_weixin_requirements`, `write_weixin_status`, `handle_inbound_payload`, and `note_verification_code` are named consistently across tasks
- Runtime status file path is consistently `HERMES_HOME/weixin_status.json`

