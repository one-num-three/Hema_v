---
name: hermes-webui-message-persistence-debug
description: Debug why assistant messages disappear from Hermes Web UI after page refresh — only user messages persist to DB.
---

# Debugging Hermes Web UI Message Persistence

Use this skill when a user reports that assistant (AI) replies disappear after refreshing/closing the Web UI, while their own messages remain visible.

## Architecture Background

Hermes Web UI uses a **two-path message storage** model:

1. **User messages** → written directly to local SQLite DB (`~/.hermes-web-ui/hermes-web-ui.db`) immediately on send
2. **Assistant messages** → accumulated in memory during SSE streaming, then saved via `syncFromHermes()` which fetches completed conversation from the Hermes API server (port 8642) on `run.completed` event

If the API server is unreachable during sync, assistant messages are lost silently.

## Investigation Steps

### 1. Check the Web UI Database

```bash
# Path on Windows
C:\Users\<USER>\.hermes-web-ui\hermes-web-ui.db

# Inspect messages table
sqlite3.exe hermes-web-ui.db "SELECT id, session_id, role, substr(content,1,80), timestamp FROM messages ORDER BY session_id, id;"
```

**Look for:** If ALL messages have `role='user'` and NONE have `role='assistant'`, the sync step is failing.

### 2. Check Gateway State

```bash
# Read the gateway state file
cat ~/.hermes/gateway_state.json
```

**Look for:** `"exit_reason": "api_server: failed to connect"` — this indicates the API server the Web UI syncs from is not healthy.

### 3. Check Gateway Log

```bash
cat ~/.hermes/gateway.log
```

### 4. Trace the Code Path

The Web UI server code is at:
```
<hermes_root>\webui\dist\server\index.js
```

Key search patterns in the bundled JS (use `search_files` or `grep`):
- `message.delta` — SSE event handler that accumulates assistant content in memory
- `run.completed` — triggers `markCompleted()` → `syncFromHermes()`
- `syncFromHermes` — fetches from Hermes API and writes to local DB via `Jp()` (the `addMessages` function)
- `Sc()` — the function that fetches session detail from Hermes API
- `api_server: failed to connect` — the error string from gateway

### 5. Verify API Server Health

```bash
# Direct health check
curl http://127.0.0.1:8642/health
# Or from Web UI startup script logic
Invoke-WebRequest 'http://127.0.0.1:8642/health' -TimeoutSec 2 -UseBasicParsing
```

## Root Cause

The Web UI **does not write assistant messages to the local database during streaming**. It accumulates them in memory, and only persists them after `run.completed` by calling back to the Hermes API server (`GET /v1/sessions/{id}`). If the API server is down or the fetch fails, assistant messages are silently discarded.

## Fix Options

### Short-term (restart gateway):
```bash
# Kill all Hermes processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe
# Restart from installation root
cd <hermes_root>
start_hermes_gateway.bat
start_webui.bat
```

### Long-term (code fix — modify Web UI server):
In `dist/server/index.js`, find the `message.delta` SSE handler and add immediate DB writes for assistant messages instead of only accumulating in the events array:

```javascript
// Before (bug): only push to memory array
case "message.delta": {
  let delta = w.delta || "";
  // ... content processing ...
  E.push({role: "assistant", content: delta, ...});  // only in memory
  break;
}

// After (fix): also write to DB immediately
case "message.delta": {
  let delta = w.delta || "";
  // ... content processing ...
  // Write to local DB immediately, not just memory
  pW({session_id: W, role: "assistant", content: delta, timestamp: ...});
  break;
}
```

## Pitfalls

- The Web UI's `.hermes-web-ui` data directory is separate from Hermes' `~/.hermes/` — don't confuse them
- `syncFromHermes` failure is completely silent — no browser console error, no server log warning
- The Web UI (port 8648) and API server (port 8642) are different processes — one can be up while the other is down
- `gateway_state.json` can show `"running"` even when the API server inside the gateway has failed — check `exit_reason` field specifically
- The database path is `~/.hermes-web-ui/hermes-web-ui.db` (the web UI's own DB), NOT `~/.hermes/sessions.db` (Hermes' session DB)
