# Hema v0.5.16-hema.5

This build includes the v0.5.16-hema.4 local package fixes, plus a Web UI
streaming compatibility fix.

## Fixed

- `/v1/responses` now supports `stream: true` with OpenAI Responses-style SSE
  events.
- hermes-web-ui 0.5.16 can now receive `response.output_text.delta` and
  `response.completed`, so assistant replies are displayed and persisted
  instead of only appearing in backend session files.
- The SSE `response.created` and `response.completed` events share the same
  response id.

## Validation

- `python_embedded\python.exe -m py_compile gateway\platforms\api_server.py tests\gateway\test_api_server.py`
  passed.
- A temporary local `/v1/responses` server returned `text/event-stream` with
  `response.output_text.delta`, `response.completed`, and `data: [DONE]`.
