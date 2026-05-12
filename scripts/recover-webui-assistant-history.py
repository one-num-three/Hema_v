"""
Recover historical assistant messages into hermes-web-ui's local SQLite DB.

Older hermes-web-ui builds persisted user messages but could lose assistant
messages after a page refresh. Hermes itself keeps richer session JSON files in
~/.hermes/sessions, so this script backfills non-empty assistant replies by
matching each Web UI user message to the Hermes session whose last user message
has the same content.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AssistantReply:
    content: str
    reasoning: str | None
    finish_reason: str | None
    source_file: str
    source_mtime: float


def normalize_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item.get("output") or ""))
            else:
                parts.append(str(item))
        return "".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def clean_match_text(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split())


def load_hermes_replies(sessions_dir: Path) -> dict[str, AssistantReply]:
    replies: dict[str, AssistantReply] = {}
    if not sessions_dir.exists():
        return replies

    for path in sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        messages = data.get("messages") if isinstance(data, dict) else None
        if not isinstance(messages, list):
            continue

        last_user_index = -1
        last_user_text = ""
        for index, message in enumerate(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                text = normalize_content(message.get("content")).strip()
                if text:
                    last_user_index = index
                    last_user_text = text
        if last_user_index < 0:
            continue

        assistant_chunks: list[str] = []
        reasoning_chunks: list[str] = []
        finish_reason: str | None = None
        for message in messages[last_user_index + 1 :]:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            content = normalize_content(message.get("content")).strip()
            if content:
                assistant_chunks.append(content)
            reasoning = normalize_content(message.get("reasoning")).strip()
            if reasoning:
                reasoning_chunks.append(reasoning)
            if message.get("finish_reason"):
                finish_reason = str(message.get("finish_reason"))

        content = "\n\n".join(assistant_chunks).strip()
        if not content:
            continue

        key = clean_match_text(last_user_text)
        candidate = AssistantReply(
            content=content,
            reasoning="\n\n".join(reasoning_chunks).strip() or None,
            finish_reason=finish_reason,
            source_file=path.name,
            source_mtime=path.stat().st_mtime,
        )
        old = replies.get(key)
        if old is None or candidate.source_mtime > old.source_mtime:
            replies[key] = candidate

    return replies


def recover(db_path: Path, sessions_dir: Path, dry_run: bool) -> tuple[int, int, int]:
    replies = load_hermes_replies(sessions_dir)
    if not db_path.exists() or not replies:
        return (0, 0, 0)

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 5000")
    try:
        user_rows = con.execute(
            "SELECT id, session_id, content, timestamp FROM messages WHERE role = 'user' ORDER BY id"
        ).fetchall()
        matched = 0
        inserted = 0

        for row in user_rows:
            reply = replies.get(clean_match_text(str(row["content"])))
            if not reply:
                continue
            matched += 1

            exists = con.execute(
                """
                SELECT 1 FROM messages
                WHERE session_id = ? AND role = 'assistant' AND content = ?
                LIMIT 1
                """,
                (row["session_id"], reply.content),
            ).fetchone()
            if exists:
                continue

            if dry_run:
                inserted += 1
                continue

            con.execute(
                """
                INSERT INTO messages
                    (session_id, role, content, timestamp, finish_reason, reasoning)
                VALUES (?, 'assistant', ?, ?, ?, ?)
                """,
                (
                    row["session_id"],
                    reply.content,
                    int(row["timestamp"]) + 1,
                    reply.finish_reason,
                    reply.reasoning,
                ),
            )
            inserted += 1

        if not dry_run and inserted:
            con.execute(
                """
                UPDATE sessions
                SET message_count = (
                    SELECT COUNT(*) FROM messages WHERE messages.session_id = sessions.id
                )
                """,
            )
            reorder_messages(con)
            con.commit()
        elif not dry_run:
            reorder_messages(con)
            con.commit()

        return (len(user_rows), matched, inserted)
    finally:
        con.close()


def reorder_messages(con: sqlite3.Connection) -> None:
    rows = con.execute(
        """
        SELECT
            session_id, role, content, tool_call_id, tool_calls, tool_name,
            timestamp, token_count, finish_reason, reasoning, reasoning_details,
            reasoning_content
        FROM messages
        ORDER BY
            session_id,
            timestamp,
            CASE role
                WHEN 'user' THEN 0
                WHEN 'assistant' THEN 1
                WHEN 'tool' THEN 2
                ELSE 3
            END,
            id
        """
    ).fetchall()
    if not rows:
        return

    con.execute("DELETE FROM messages")
    con.execute("DELETE FROM sqlite_sequence WHERE name = 'messages'")
    con.executemany(
        """
        INSERT INTO messages
            (
                session_id, role, content, tool_call_id, tool_calls, tool_name,
                timestamp, token_count, finish_reason, reasoning, reasoning_details,
                reasoning_content
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [tuple(row) for row in rows],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover missing hermes-web-ui assistant history.")
    parser.add_argument("--db", type=Path, default=Path.home() / ".hermes-web-ui" / "hermes-web-ui.db")
    parser.add_argument("--sessions-dir", type=Path, default=Path.home() / ".hermes" / "sessions")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total, matched, inserted = recover(args.db, args.sessions_dir, args.dry_run)
    action = "would insert" if args.dry_run else "inserted"
    print(f"Checked {total} Web UI user messages; matched {matched}; {action} {inserted} assistant replies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
