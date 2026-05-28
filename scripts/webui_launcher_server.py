from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROBE_TIMEOUT = 1.5


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _file_response(handler: BaseHTTPRequestHandler, path: Path) -> None:
    if not path.exists() or not path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND)
        return
    data = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", (mime or "text/plain") + "; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)


def make_handler(root: Path):
    class LauncherHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.startswith("/__probe__"):
                self.handle_probe()
                return

            rel = self.path.split("?", 1)[0]
            if rel in ("", "/"):
                rel = "/index.html"
            target = (root / rel.lstrip("/")).resolve()
            if root not in target.parents and target != root:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            _file_response(self, target)

        def handle_probe(self) -> None:
            from urllib.parse import parse_qs, urlsplit

            query = parse_qs(urlsplit(self.path).query)
            try:
                port = int((query.get("targetPort") or ["8648"])[0])
            except ValueError:
                port = 8648
            try:
                gateway_port = int((query.get("gatewayPort") or ["8642"])[0])
            except ValueError:
                gateway_port = 8642

            health_url = f"http://127.0.0.1:{port}/health"
            root_url = f"http://127.0.0.1:{port}/"
            result = {
                "webui_up": False,
                "gateway_running": False,
                "gateway_direct": False,
                "health": None,
                "webui_source": None,
                "gateway_port": gateway_port,
            }
            errors: list[str] = []
            try:
                with urlopen(health_url, timeout=PROBE_TIMEOUT) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    result["webui_up"] = True
                    result["webui_source"] = "health"
                    try:
                        result["health"] = json.loads(body)
                    except json.JSONDecodeError:
                        result["health"] = {"raw": body}
                    result["gateway_running"] = result["health"].get("gateway") == "running"
            except URLError as exc:
                errors.append(str(exc.reason or exc))
            except Exception as exc:
                errors.append(str(exc))

            if not result["webui_up"]:
                try:
                    with urlopen(root_url, timeout=PROBE_TIMEOUT) as response:
                        _ = response.status
                        result["webui_up"] = True
                        result["webui_source"] = "root"
                except URLError as exc:
                    errors.append(str(exc.reason or exc))
                except Exception as exc:
                    errors.append(str(exc))

            # Probe the gateway directly so the launcher page can report its
            # status even before the Web UI server is ready.
            try:
                with urlopen(f"http://127.0.0.1:{gateway_port}/health", timeout=PROBE_TIMEOUT) as _:
                    result["gateway_direct"] = True
            except Exception:
                pass

            if errors:
                result["error"] = errors[-1]
                result["recent_errors"] = errors[-3:]

            _json_response(self, result)

        def log_message(self, format: str, *args) -> None:
            return

    return LauncherHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    handler = make_handler(root)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
