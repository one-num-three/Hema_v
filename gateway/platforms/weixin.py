"""Weixin iLink platform adapter.

Minimal long-polling adapter for Tencent iLink bot accounts:
- Reads WEIXIN_ACCOUNT_ID / WEIXIN_TOKEN / WEIXIN_BASE_URL from config/env
- Polls getupdates for inbound messages
- Sends text replies via sendmessage with context_token
- Persists latest status to HERMES_HOME/weixin_status.json
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

_VERIFY_CODE_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")
DEDUP_WINDOW_SECONDS = 300  # seconds to remember seen message IDs
DEDUP_MAX_SIZE = 500        # max entries before pruning


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def check_weixin_requirements() -> bool:
    return bool(
        os.getenv("WEIXIN_ACCOUNT_ID", "").strip()
        and os.getenv("WEIXIN_TOKEN", "").strip()
    )


def write_weixin_status(
    status_path: Path,
    *,
    status: str,
    message: str,
    verification_code: str = "",
    account_id: str = "",
    last_error: str = "",
) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "message": message,
        "verification_code": verification_code,
        "last_event_at": _utc_now_iso(),
        "account_id": account_id,
        "last_error": last_error,
    }
    status_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class WeixinAdapter(BasePlatformAdapter):
    platform = Platform.WEIXIN

    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.WEIXIN)
        extra = config.extra or {}
        self._account_id = str(extra.get("account_id") or os.getenv("WEIXIN_ACCOUNT_ID", "")).strip()
        self._token = str(config.token or os.getenv("WEIXIN_TOKEN", "")).strip()
        self._base_url = str(
            extra.get("base_url") or os.getenv("WEIXIN_BASE_URL", "https://ilinkai.weixin.qq.com")
        ).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._context_tokens: Dict[str, str] = {}
        self._seen_messages: Dict[str, float] = {}
        self._cursor: Optional[str] = None
        home = get_hermes_home()
        self._status_path = home / "weixin_status.json"
        self._log_path = home / "logs" / "weixin.log"

    def _append_log(self, message: str) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        line = f"{_utc_now_iso()} {message}\n"
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def _set_status(
        self,
        *,
        status: str,
        message: str,
        verification_code: str = "",
        last_error: str = "",
    ) -> None:
        write_weixin_status(
            self._status_path,
            status=status,
            message=message,
            verification_code=verification_code,
            account_id=self._account_id,
            last_error=last_error,
        )

    def _extract_text(self, payload: Dict[str, Any]) -> str:
        item_list = payload.get("item_list") or payload.get("msg", {}).get("item_list") or []
        parts: List[str] = []
        for item in item_list:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == 1:
                text = (
                    item.get("text_item", {}).get("text")
                    or item.get("text")
                    or ""
                )
                if text:
                    parts.append(str(text))
        return "\n".join(part.strip() for part in parts if str(part).strip()).strip()

    def _extract_message_id(self, payload: Dict[str, Any]) -> Optional[str]:
        for key in ("msg_id", "message_id", "id", "seq"):
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)
        return None

    def _build_message_event(self, payload: Dict[str, Any]) -> MessageEvent:
        from_user_id = (
            payload.get("from_user_id")
            or payload.get("from", {}).get("user_id")
            or payload.get("sender", {}).get("user_id")
            or ""
        )
        text = self._extract_text(payload)
        source = self.build_source(
            chat_id=from_user_id,
            chat_name=from_user_id,
            chat_type="dm",
            user_id=from_user_id,
            user_name=from_user_id,
        )
        return MessageEvent(
            text=text,
            message_type=MessageType.TEXT,
            source=source,
            raw_message=payload,
            message_id=self._extract_message_id(payload),
        )

    def note_verification_code(self, code: str, message: str = "Verification code received") -> None:
        self._append_log(f"verification_code {code} {message}")
        self._set_status(
            status="verification_code",
            message=message,
            verification_code=code,
        )

    async def _post_json(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("Weixin client is not connected")
        headers = self._build_api_headers()
        response = await asyncio.wait_for(
            self._client.post(path, json=body, headers=headers),
            timeout=65.0,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("ret") not in (None, 0):
            raise RuntimeError(data.get("msg") or data.get("errmsg") or f"Weixin API error: {data.get('ret')}")
        return data

    def _build_api_headers(self) -> Dict[str, str]:
        rand_uin = str(random.randint(1, 2**31 - 1)).encode("utf-8")
        return {
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self._token}",
            "X-WECHAT-UIN": base64.b64encode(rand_uin).decode("ascii"),
            "Content-Type": "application/json",
        }

    def _build_getupdates_body(self) -> Dict[str, Any]:
        return {
            "get_updates_buf": self._cursor or "",
            "base_info": {
                "channel_version": "2.0.0",
            },
        }

    def _extract_updates(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nested_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        candidates = [
            data.get("msgs"),           # iLink actual key
            data.get("update_list"),
            data.get("updates"),
            data.get("items"),
            data.get("msg_list"),
            nested_data.get("msgs"),
            nested_data.get("update_list"),
            nested_data.get("updates"),
            nested_data.get("items"),
            nested_data.get("msg_list"),
        ]
        for candidate in candidates:
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return []


    def _update_cursor_from_response(self, data: Dict[str, Any], updates: List[Dict[str, Any]]) -> None:
        for key in ("get_updates_buf", "next_cursor", "cursor", "next_key"):
            value = data.get(key)
            if value:
                self._cursor = str(value)
                return
            nested = data.get("data")
            if isinstance(nested, dict) and nested.get(key):
                self._cursor = str(nested[key])
                return
        if updates:
            last = updates[-1]
            for key in ("seq", "cursor", "id", "msg_id"):
                value = last.get(key)
                if value not in (None, ""):
                    self._cursor = str(value)
                    return

    def _is_duplicate(self, msg_id: str) -> bool:
        now = time.time()
        if len(self._seen_messages) > DEDUP_MAX_SIZE:
            cutoff = now - DEDUP_WINDOW_SECONDS
            self._seen_messages = {k: v for k, v in self._seen_messages.items() if v > cutoff}
        if msg_id in self._seen_messages:
            return True
        self._seen_messages[msg_id] = now
        return False

    def _unwrap_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        msg = payload.get("msg")
        if isinstance(msg, dict):
            merged = dict(payload)
            merged.update(msg)
            return merged
        return payload

    async def handle_inbound_payload(self, payload: Dict[str, Any]) -> Optional[MessageEvent]:
        raw_keys = list(payload.keys())
        payload = self._unwrap_payload(payload)
        msg_id = self._extract_message_id(payload)
        if msg_id and self._is_duplicate(msg_id):
            self._append_log(f"dedup_skipped msg_id={msg_id}")
            return None
        from_user_id = (
            payload.get("from_user_id")
            or payload.get("from", {}).get("user_id")
            or payload.get("sender", {}).get("user_id")
            or ""
        )
        context_token = payload.get("context_token") or payload.get("msg", {}).get("context_token")
        if from_user_id and context_token:
            self._context_tokens[str(from_user_id)] = str(context_token)
            self._append_log(f"context_token_cached from={from_user_id}")
        event = self._build_message_event(payload)
        if not event.text:
            self._append_log(
                f"skipped_empty_text from={from_user_id} raw_keys={raw_keys} keys={list(payload.keys())}"
            )
            return None
        match = _VERIFY_CODE_RE.search(event.text)
        lowered_text = event.text.lower()
        if match and (
            "code" in lowered_text
            or "verify" in lowered_text
            or "验证码" in event.text
            or "驗證碼" in event.text
        ):
            self.note_verification_code(match.group(1), event.text)
        self._append_log(
            f"inbound from={from_user_id} msg_id={event.message_id or ''} "
            f"has_context={bool(context_token)} text={event.text[:300]}"
        )
        self._set_status(status="connected", message="Received inbound Weixin message")
        return event

    async def _get_updates_once(self) -> List[Dict[str, Any]]:
        data = await self._post_json("/ilink/bot/getupdates", self._build_getupdates_body())
        updates = self._extract_updates(data)
        self._update_cursor_from_response(data, updates)
        if updates:
            first_keys = list(updates[0].keys()) if isinstance(updates[0], dict) else []
            self._append_log(
                f"poll_updates count={len(updates)} keys={list(data.keys())} "
                f"first_keys={first_keys}"
            )
        else:
            nested = data.get("data") if isinstance(data.get("data"), dict) else {}
            self._append_log(
                f"poll_empty keys={list(data.keys())} nested_keys={list(nested.keys())} "
                f"cursor_set={bool(self._cursor)}"
            )
        return updates


    async def _poll_loop(self) -> None:
        while self._running:
            try:
                updates = await self._get_updates_once()
                for payload in updates:
                    event = await self.handle_inbound_payload(payload)
                    if event:
                        await self.handle_message(event)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Weixin polling error: %s", exc)
                self._append_log(f"poll_error {exc}")
                self._set_status(
                    status="error",
                    message="Weixin polling failed",
                    last_error=str(exc),
                )
                await asyncio.sleep(3)

    async def connect(self) -> bool:
        if not self._account_id or not self._token:
            self._set_status(
                status="not_configured",
                message="Weixin account_id or token missing",
                last_error="WEIXIN_ACCOUNT_ID or WEIXIN_TOKEN missing",
            )
            return False
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=60.0,
        )
        self._mark_connected()
        self._set_status(status="connected", message="Weixin gateway connected")
        self._append_log(f"connected base_url={self._base_url} account_id={self._account_id}")
        self._poll_task = asyncio.create_task(self._poll_loop())
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        self._mark_disconnected()
        self._set_status(status="disconnected", message="Weixin gateway disconnected")

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        context_token = self._context_tokens.get(str(chat_id))
        if not context_token:
            self._append_log(f"send_error to={chat_id} error=missing_context_token")
            return SendResult(success=False, error="Missing Weixin context token")
        body = {
            "msg": {
                "to_user_id": str(chat_id),
                "client_id": f"hermes-weixin:{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "message_type": 2,
                "message_state": 2,
                "context_token": context_token,
                "item_list": [
                    {
                        "type": 1,
                        "text_item": {
                            "text": content,
                        },
                    }
                ],
            },
            "base_info": {
                "channel_version": "2.0.0",
            },
        }
        try:
            data = await self._post_json("/ilink/bot/sendmessage", body)
            self._append_log(
                f"outbound to={chat_id} response_keys={list(data.keys())} text={content[:300]}"
            )
            self._set_status(status="connected", message="Sent outbound Weixin reply")
            return SendResult(
                success=True,
                message_id=str(data.get("msg_id") or data.get("message_id") or ""),
                raw_response=data,
            )
        except Exception as exc:
            self._append_log(f"send_error to={chat_id} error={exc}")
            self._set_status(
                status="error",
                message="Failed to send Weixin reply",
                last_error=str(exc),
            )
            return SendResult(success=False, error=str(exc), retryable=True)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {
            "name": str(chat_id),
            "type": "dm",
            "chat_id": str(chat_id),
        }
