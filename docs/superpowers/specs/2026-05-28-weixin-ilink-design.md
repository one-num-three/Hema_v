# Weixin iLink Minimal Viable Integration Design

## Goal

Build a minimal viable Weixin integration around the existing Tencent iLink QR-login flow so that:

- WebUI QR login remains the entrypoint
- Hermes gateway actually consumes `WEIXIN_*` credentials
- Weixin can receive inbound messages and send agent replies
- WebUI Channels page shows live login and verification status
- Failures are visible to users instead of silently disappearing

This design targets the current Hermes codebase in `E:\hema-fix` and preserves existing entry conventions.

## Scope

In scope:

- Reuse the current WebUI iLink QR routes
- Add a gateway-level Weixin platform adapter
- Add a small status persistence layer for WebUI visibility
- Show status, verification code, last error, and last activity in WebUI
- Support a minimal inbound message -> agent reply -> outbound message loop

Out of scope for this phase:

- Personal WeChat account reverse-engineering flows
- Multi-account management beyond the existing profile isolation model
- Rich media message handling
- Historical message sync
- Deep admin tooling beyond status visibility and basic logs

## Current State

The existing WebUI route already talks to Tencent iLink:

- `webui/node_modules/hermes-web-ui/dist/server/routes/hermes/weixin.js`

That route currently:

- fetches a QR code from iLink
- polls QR scan status
- saves `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, and `WEIXIN_BASE_URL`
- restarts the gateway

What is missing today:

- no `Platform.WEIXIN` in gateway config
- no `gateway/platforms/weixin.py`
- no gateway startup branch for Weixin
- no runtime state file for WebUI to read
- no message receive/send implementation

Result: QR login can appear to work, but Hermes has no backend channel to receive login events, verification codes, or user messages.

## Architecture

The integration should be split into three layers.

### 1. WebUI QR Login Layer

Keep the current WebUI iLink routes as the login entrypoint.

Responsibilities:

- fetch QR code
- poll QR status
- persist `WEIXIN_*` credentials into the active profile env
- restart the gateway after credentials change

This layer should stay intentionally small and not own long-lived runtime state beyond login initiation.

### 2. Gateway Platform Layer

Add a true Weixin platform adapter in the gateway.

Responsibilities:

- initialize using `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, and optional `WEIXIN_BASE_URL`
- connect to iLink runtime APIs or callbacks
- normalize inbound Weixin messages into Hermes `MessageEvent`
- send outbound agent replies back to Weixin
- write operational status updates for WebUI and logs

This layer is the authoritative runtime source for connection state.

### 3. WebUI Status Layer

Expose gateway-maintained Weixin runtime status in the Channels page.

Responsibilities:

- read latest Weixin status from a small state file
- render human-readable connection and verification state
- show recent errors without requiring log inspection

This layer must be read-only with respect to runtime state.

## Required Backend Changes

### Gateway Config

Update gateway configuration to recognize Weixin as a supported platform.

Changes:

- add `WEIXIN` to `Platform` enum in [gateway/config.py](/E:/hema-fix/gateway/config.py)
- add env parsing for:
  - `WEIXIN_ACCOUNT_ID`
  - `WEIXIN_TOKEN`
  - `WEIXIN_BASE_URL`
- create a `PlatformConfig` entry when the required variables are present

Configuration should remain profile-safe and continue to rely on the active `HERMES_HOME`.

### Platform Adapter

Create [gateway/platforms/weixin.py](/E:/hema-fix/gateway/platforms/weixin.py).

The adapter should provide:

- `check_weixin_requirements()`
- connect/start lifecycle
- disconnect/stop lifecycle
- inbound event normalization
- outbound send method
- status persistence hooks

The implementation should follow the same structural pattern as other adapters in `gateway/platforms/`, but stay intentionally narrower than Feishu or Slack in the first phase.

### Gateway Runner Wiring

Update [gateway/run.py](/E:/hema-fix/gateway/run.py) to:

- start Weixin when credentials are configured
- isolate Weixin startup failure from other platforms
- include Weixin in adapter registration and lifecycle management

Failure to connect Weixin must not bring down the whole gateway process.

## Status Persistence Design

Add a small status file under the active profile home:

- `HERMES_HOME/weixin_status.json`

Detailed logs should go to:

- `HERMES_HOME/logs/weixin.log`

### Status File Shape

The file should contain only the latest snapshot, for example:

```json
{
  "status": "connected",
  "message": "Logged in successfully",
  "verification_code": "123456",
  "last_event_at": "2026-05-28T14:20:31Z",
  "account_id": "60f485c615e2@im.bot",
  "last_error": ""
}
```

Recommended status values:

- `not_configured`
- `waiting_confirm`
- `connected`
- `verification_code`
- `disconnected`
- `send_failed`
- `auth_invalid`

### Update Rules

The adapter should update the status file whenever one of these occurs:

- credentials loaded
- login confirmed
- verification code received
- inbound message received
- outbound send succeeded or failed
- reconnect attempt started
- auth failure or transport failure detected

The status file should always be best-effort and overwrite the previous snapshot.

## WebUI Integration

Add a small local BFF endpoint in the WebUI server that reads `weixin_status.json`.

The endpoint should return:

- current status
- last message
- latest verification code
- last activity timestamp
- last error

The Channels page should show on the Weixin card:

- current state
- recent verification code
- human-readable status message
- last activity time
- latest error when present

The page should not require the user to inspect raw logs for common issues.

## Message Flow

Minimal message loop:

1. User scans QR in WebUI
2. WebUI saves `WEIXIN_*` and restarts gateway
3. Gateway starts Weixin adapter
4. Adapter connects to iLink
5. Inbound Weixin message arrives
6. Adapter converts it to Hermes `MessageEvent`
7. Hermes agent runs normally
8. Adapter sends reply back through iLink
9. Adapter writes state and logs for visibility

Verification codes should be treated as system state, not as normal chat content.

## Error Handling

The first implementation should explicitly surface these cases:

- invalid token -> `auth_invalid`
- transport timeout -> `disconnected`
- reconnect in progress -> `message` should indicate reconnecting
- inbound processing failure -> log error and update `last_error`
- outbound send failure -> `send_failed`

The WebUI should show the latest meaningful failure without flooding the user with raw stack traces.

## Testing Strategy

Minimum acceptance checks:

1. QR login updates the Weixin card from unconfigured to waiting/connected.
2. When iLink returns a verification code, the code is visible in WebUI.
3. A Weixin inbound message reaches Hermes and creates a normal conversation turn.
4. Hermes reply is delivered back to Weixin.
5. Invalid credentials or transport failure show a clear error state in WebUI.

Implementation-level verification should include:

- unit tests for config/env parsing
- adapter-level tests for status snapshot updates
- server route test for WebUI status endpoint
- smoke verification on a real configured profile

## Risks

- iLink runtime APIs may differ from the assumptions implied by QR login endpoints
- verification events may arrive through a separate callback or polling API
- partial success states may be easy to misreport if transport semantics are unclear
- WebUI currently runs off patched dist output, so persistence hooks must remain durable across reinstalls

## Recommendation

Proceed with the minimal viable integration in this order:

1. add gateway config support for Weixin
2. build `weixin.py` with status persistence first
3. wire gateway startup and failure isolation
4. expose WebUI status endpoint
5. render status in the Weixin card
6. validate real inbound/outbound messaging

This order gives user-visible progress early while keeping runtime responsibilities well separated.
