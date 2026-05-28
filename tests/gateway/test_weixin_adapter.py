import json

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.base import MessageType
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
            "from_user_id": "wx-user-1@im.wechat",
            "context_token": "ctx-1",
            "item_list": [{"type": 1, "text_item": {"text": "hello"}}],
        }
    )

    assert event.source.platform.value == "weixin"
    assert event.source.chat_id == "wx-user-1@im.wechat"
    assert event.source.user_id == "wx-user-1@im.wechat"
    assert event.text == "hello"
    assert event.message_type == MessageType.TEXT


def test_extract_updates_accepts_nested_data_msgs(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)

    updates = adapter._extract_updates(
        {
            "ret": 0,
            "data": {
                "msgs": [
                    {
                        "from_user_id": "wx-user-1@im.wechat",
                        "item_list": [{"type": 1, "text_item": {"text": "hello"}}],
                    }
                ]
            },
        }
    )

    assert len(updates) == 1
    assert updates[0]["from_user_id"] == "wx-user-1@im.wechat"


def test_note_verification_code_updates_status_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)

    adapter.note_verification_code("654321", "验证码：654321")

    status = json.loads((tmp_path / "weixin_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "verification_code"
    assert status["verification_code"] == "654321"


@pytest.mark.asyncio
async def test_handle_inbound_payload_updates_status_and_returns_event(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)

    event = await adapter.handle_inbound_payload(
        {
            "from_user_id": "wx-user-1@im.wechat",
            "context_token": "ctx-1",
            "item_list": [{"type": 1, "text_item": {"text": "hello"}}],
        }
    )

    assert event.text == "hello"
    status = json.loads((tmp_path / "weixin_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "connected"
    assert status["message"] == "Received inbound Weixin message"


@pytest.mark.asyncio
async def test_send_uses_cached_context_token(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config = PlatformConfig(enabled=True, token="tok", extra={"account_id": "acct"})
    adapter = WeixinAdapter(config)
    adapter._context_tokens["wx-user-1@im.wechat"] = "ctx-1"

    calls = []

    async def fake_post(path, body):
        calls.append((path, body))
        return {"ret": 0, "msg_id": "123"}

    adapter._post_json = fake_post
    result = await adapter.send("wx-user-1@im.wechat", "reply text")

    assert result.success is True
    assert calls[0][0] == "/ilink/bot/sendmessage"
    assert calls[0][1]["msg"]["to_user_id"] == "wx-user-1@im.wechat"
    assert calls[0][1]["msg"]["context_token"] == "ctx-1"
