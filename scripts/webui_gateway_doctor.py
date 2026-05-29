from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOME = Path.home() / ".hermes"
DEFAULT_WEBUI_HOME = Path.home() / ".hermes-web-ui"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"<read failed: {exc}>"


def _tail_text(path: Path, lines: int = 80) -> str:
    if not path.exists():
        return "<missing>"
    text = _read_text(path)
    return "\n".join(text.splitlines()[-lines:])


def _run(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            shell=False,
        )
    except Exception as exc:
        return f"<command failed: {exc}>"
    output = proc.stdout.strip()
    err = proc.stderr.strip()
    if err:
        output = f"{output}\n[stderr]\n{err}".strip()
    return output or "<no output>"


def _http_probe(url: str, timeout: float = 3.0) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "webui-gateway-doctor/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload: object
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = body[:4000]
            return {"ok": True, "status": getattr(response, "status", 200), "body": payload}
    except URLError as exc:
        return {"ok": False, "error": str(exc.reason or exc)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def _resolve_active_profile(home: Path) -> tuple[str, Path]:
    active_profile_file = home / "active_profile"
    active = "default"
    if active_profile_file.exists():
        raw = _read_text(active_profile_file).strip()
        if raw:
            active = raw
    if active != "default":
        profile_home = home / "profiles" / active
        if (profile_home / "config.yaml").exists():
            return active, profile_home
    return "default", home


def _find_gateway_ports(home: Path) -> list[int]:
    ports = {8642, 8648}
    candidates = [home / "config.yaml"]
    profiles_root = home / "profiles"
    if profiles_root.exists():
        candidates.extend(path / "config.yaml" for path in profiles_root.iterdir() if path.is_dir())
    for cfg in candidates:
        if not cfg.exists():
            continue
        text = _read_text(cfg)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("port:"):
                value = stripped.split(":", 1)[1].strip().strip("'\"")
                if value.isdigit():
                    ports.add(int(value))
    return sorted(ports)


def _collect_pid_files(home: Path) -> list[Path]:
    pid_files = []
    default_pid = home / "gateway.pid"
    if default_pid.exists():
        pid_files.append(default_pid)
    profiles_root = home / "profiles"
    if profiles_root.exists():
        for profile in sorted(p for p in profiles_root.iterdir() if p.is_dir()):
            candidate = profile / "gateway.pid"
            if candidate.exists():
                pid_files.append(candidate)
    return pid_files


def _collect_bundle_markers(bundle: Path) -> dict[str, bool]:
    if not bundle.exists():
        return {"bundle_exists": False}
    text = _read_text(bundle)
    return {
        "bundle_exists": True,
        "upstream_single_profile_list": 'async listProfiles(){if(process.env.UPSTREAM?.trim())return[this.activeProfile||"default"];' in text,
        "upstream_single_profile_detect_status": 'if(process.env.UPSTREAM?.trim()){if(G!==Z)return this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1};' in text,
        "profile_page_upstream_status": 'if(r){if(Y!==d)return"stopped";' in text,
        "profile_page_default_probe": 'gateway:await N(b,"default")' in text,
    }


def build_report(home: Path, webui_home: Path) -> str:
    active_profile, active_home = _resolve_active_profile(home)
    ports = _find_gateway_ports(home)
    bundle = PROJECT_ROOT / "webui" / "node_modules" / "hermes-web-ui" / "dist" / "server" / "index.js"
    report: list[str] = []

    def section(title: str, body: str) -> None:
        report.append(f"\n=== {title} ===\n{body.rstrip()}\n")

    section(
        "Meta",
        textwrap.dedent(
            f"""\
            timestamp: {datetime.now().isoformat(timespec="seconds")}
            project_root: {PROJECT_ROOT}
            python: {sys.executable}
            hermes_home: {home}
            webui_home: {webui_home}
            active_profile: {active_profile}
            active_profile_home: {active_home}
            cwd: {Path.cwd()}
            """
        ),
    )

    section(
        "Config Files",
        textwrap.dedent(
            f"""\
            default_config: {home / "config.yaml"}
            active_profile_file: {home / "active_profile"}
            server_mode: {webui_home / "server.mode"}
            server_pid: {webui_home / "server.pid"}
            """
        ),
    )

    config_dump = []
    for cfg in [home / "config.yaml", active_home / "config.yaml"]:
        config_dump.append(f"[{cfg}]\n{_read_text(cfg)}")
    section("Config Dump", "\n\n".join(config_dump))

    pid_chunks = []
    for pid_file in _collect_pid_files(home):
        raw = _read_text(pid_file).strip()
        pid_chunks.append(f"[{pid_file}]\n{raw}")
    section("Gateway PID Files", "\n\n".join(pid_chunks) if pid_chunks else "<none>")

    port_chunks = []
    for port in ports:
        port_chunks.append(
            f"port {port}: open={_port_open('127.0.0.1', port)} health={json.dumps(_http_probe(f'http://127.0.0.1:{port}/health'), ensure_ascii=False)}"
        )
    section("Port Probes", "\n".join(port_chunks))

    webui_api_chunks = []
    for path in [
        "http://127.0.0.1:8648/health",
        "http://127.0.0.1:8648/api/hermes/gateways",
        "http://127.0.0.1:8648/api/hermes/profiles",
    ]:
        webui_api_chunks.append(f"{path}\n{json.dumps(_http_probe(path), ensure_ascii=False, indent=2)}")
    section("WebUI API Probes", "\n\n".join(webui_api_chunks))

    section(
        "Bundle Markers",
        json.dumps(_collect_bundle_markers(bundle), ensure_ascii=False, indent=2),
    )

    powershell = os.environ.get("SystemRoot", r"C:\Windows") + r"\System32\WindowsPowerShell\v1.0\powershell.exe"
    section(
        "PowerShell Process Snapshot",
        _run(
            [
                powershell,
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('node.exe','python.exe','pythonw.exe','Claude.exe') } | "
                "Select-Object ProcessId,Name,CreationDate,ExecutablePath,CommandLine | Format-List",
            ]
        ),
    )
    section(
        "Port Ownership Snapshot",
        _run(
            [
                powershell,
                "-NoProfile",
                "-Command",
                "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
                "Where-Object { $_.LocalPort -in @(8642,8648,8665,8692,8693) } | "
                "Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize",
            ]
        ),
    )

    section("WebUI Root Log Tail", _tail_text(webui_home / "server.log"))
    section("WebUI Structured Log Tail", _tail_text(webui_home / "logs" / "server.log"))
    section("Gateway Log Tail", _tail_text(home / "logs" / "gateway.log"))
    section("Gateway Err Log Tail", _tail_text(home / "gateway.err.log"))
    section("Weixin Log Tail", _tail_text(home / "logs" / "weixin.log"))

    return "\n".join(report).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect WebUI/Gateway diagnostics for Hermes on Windows.")
    parser.add_argument("--home", type=Path, default=DEFAULT_HOME, help="Hermes home directory")
    parser.add_argument("--webui-home", type=Path, default=DEFAULT_WEBUI_HOME, help="Hermes WebUI home directory")
    parser.add_argument("--output", type=Path, help="Output file path")
    args = parser.parse_args()

    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = args.home / "logs" / f"webui_gateway_doctor_{stamp}.txt"
    output.parent.mkdir(parents=True, exist_ok=True)

    report = build_report(args.home, args.webui_home)
    output.write_text(report, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
