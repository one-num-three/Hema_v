"""
Patch hermes-web-ui's compiled gateway-manager.js.

Fixes three Windows-specific bugs that prevent the WebUI from detecting a
gateway that was started externally (e.g. by start_hermes_gateway.bat) or that
is already running on the configured port:

1. detectStatus — gateway was only detected if a PID file existed AND the
   process was alive.  Externally-started gateways have no PID file, so they
   were never registered, which caused startAll to try (and fail) to start a
   new gateway.  Now: if the health check passes, register regardless of PID.
   Bonus: if config.yaml port was corrupted to a wrong value, try the default
   port 8642 and self-heal the file.

2. resolvePort — if the configured port was occupied (by the running gateway),
   it was reassigned to port+1 and config.yaml was overwritten.  This broke
   the gateway on the next startup.  Now: skip reassignment if health check
   passes on the occupied port.

3. startAll — even when detectStatus registered the gateway with pid=0,
   isProcessAlive(0) returns false on Windows, causing startAll to attempt a
   re-launch.  Now: also skip if health check passes.
"""
from __future__ import annotations

from pathlib import Path
import sys


SENTINEL = "// [hema-patch-gateway-manager-applied]"


# ---------------------------------------------------------------------------
# Patch 1 — detectStatus
# ---------------------------------------------------------------------------
DETECT_OLD = """\
    async detectStatus(name) {
        const pid = this.readPidFile(name);
        const { port, host } = this.readProfilePort(name);
        const url = `http://${host}:${port}`;
        if (pid && this.isProcessAlive(pid) && await this.checkHealth(url)) {
            this.gateways.set(name, { pid, port, host, url });
            return { profile: name, port, host, url, running: true, pid };
        }
        // 未运行或端口不匹配
        this.gateways.delete(name);
        return { profile: name, port, host, url, running: false };
    }"""

DETECT_NEW = """\
    async detectStatus(name) {
        const pid = this.readPidFile(name);
        const { port, host } = this.readProfilePort(name);
        const url = `http://${host}:${port}`;
        if (await this.checkHealth(url)) {
            // Healthy — register even without a PID file (externally started gateway)
            const alive = pid && this.isProcessAlive(pid);
            const actualPid = alive ? pid : 0;
            this.gateways.set(name, { pid: actualPid, port, host, url });
            return { profile: name, port, host, url, running: true, pid: actualPid || undefined };
        }
        // Fallback: config.yaml may have been corrupted to the wrong port.
        // Try the default port 8642 and self-heal the config if found.
        const DEFAULT_PORT = 8642;
        if (port !== DEFAULT_PORT) {
            const fallbackUrl = `http://${host}:${DEFAULT_PORT}`;
            if (await this.checkHealth(fallbackUrl)) {
                console.log(`[GatewayManager] Gateway found on port ${DEFAULT_PORT} but config says ${port} for "${name}" — repairing config.yaml`);
                this.writeProfilePort(name, DEFAULT_PORT, host);
                this.gateways.set(name, { pid: 0, port: DEFAULT_PORT, host, url: fallbackUrl });
                return { profile: name, port: DEFAULT_PORT, host, url: fallbackUrl, running: true, pid: undefined };
            }
        }
        this.gateways.delete(name);
        return { profile: name, port, host, url, running: false };
    }"""


# ---------------------------------------------------------------------------
# Patch 2 — startAll: also check health when isProcessAlive fails (pid=0)
# ---------------------------------------------------------------------------
START_ALL_OLD = """\
            const existing = this.gateways.get(name);
            if (existing && this.isProcessAlive(existing.pid)) {
                console.log(`[GatewayManager] ${name}: already running (PID: ${existing.pid})`);
                continue;
            }"""

START_ALL_NEW = """\
            const existing = this.gateways.get(name);
            if (existing && (this.isProcessAlive(existing.pid) || await this.checkHealth(existing.url))) {
                console.log(`[GatewayManager] ${name}: already running (PID: ${existing.pid})`);
                continue;
            }"""


# ---------------------------------------------------------------------------
# Patch 3 — resolvePort: don't reassign an occupied port that passes health check
# ---------------------------------------------------------------------------
RESOLVE_OLD = """\
            const available = await this.checkPortAvailable(port, host);
            if (!available) {
                const newPort = await this.findFreePort(port, host);
                console.log(`[GatewayManager] Port ${port} is occupied by another process for profile "${name}", reassigning to ${newPort}`);
                this.writeProfilePort(name, newPort, host);
                port = newPort;
            }
            else {
                // 端口空闲，写入完整配置（确保 api_server 配置齐全）
                this.writeProfilePort(name, port, host);
            }"""

RESOLVE_NEW = """\
            const available = await this.checkPortAvailable(port, host);
            if (!available) {
                // Occupied — check if it's our gateway before reassigning (preserves config.yaml)
                if (await this.checkHealth(`http://${host}:${port}`)) {
                    console.log(`[GatewayManager] Port ${port} has a healthy gateway for profile "${name}", reusing it`);
                    this.allocatedPorts.add(port);
                    return { port, host };
                }
                const newPort = await this.findFreePort(port, host);
                console.log(`[GatewayManager] Port ${port} is occupied by another process for profile "${name}", reassigning to ${newPort}`);
                this.writeProfilePort(name, newPort, host);
                port = newPort;
            }
            else {
                // 端口空闲，写入完整配置（确保 api_server 配置齐全）
                this.writeProfilePort(name, port, host);
            }"""


def patch_gateway_manager(webui_dir: str) -> bool:
    candidates = [
        Path(webui_dir) / "node_modules" / "hermes-web-ui" / "dist" / "server" / "services" / "hermes" / "gateway-manager.js",
    ]
    target: Path | None = None
    for c in candidates:
        if c.exists():
            target = c
            break

    if target is None:
        print(f"gateway-manager.js not found under {webui_dir}")
        return False

    content = target.read_text(encoding="utf-8")

    if SENTINEL in content:
        print("gateway-manager patch already applied")
        return True

    changed = False

    for old, new, label in [
        (DETECT_OLD, DETECT_NEW, "detectStatus"),
        (START_ALL_OLD, START_ALL_NEW, "startAll"),
        (RESOLVE_OLD, RESOLVE_NEW, "resolvePort"),
    ]:
        if old in content:
            content = content.replace(old, new, 1)
            changed = True
            print(f"  Applied patch: {label}")
        else:
            print(f"  Skipped (already patched or marker not found): {label}")

    if changed:
        content += f"\n{SENTINEL}\n"
        target.write_text(content, encoding="utf-8")
        print(f"gateway-manager.js patched at {target}")
    else:
        print("No changes made to gateway-manager.js")

    return True


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <webui_dir>")
        return 1
    return 0 if patch_gateway_manager(sys.argv[1]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
