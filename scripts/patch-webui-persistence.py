"""
Post-build patch for hermes-web-ui dist/server/index.js.

The upstream Web UI can finish a run without persisting assistant messages to
the local SQLite store. This patch injects persistence before markCompleted()
is called in the bundled server file.
"""
import sys


def patch_webui(filepath: str) -> bool:
    with open(filepath, "rb") as f:
        content = f.read().decode("utf-8", errors="replace")

    if "failed to persist assistant message to local DB" in content:
        print("Already patched; no change needed")
        return True

    if "flushResponseRunToDb" in content:
        print("Upstream already persists response runs; no patch needed")
        return True

    original_size = len(content)
    marker = "W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id})"

    if marker not in content:
        alt = "this.markCompleted(G,W,{event:w.event,run_id:w.run_id})"
        if alt in content:
            marker = alt
        else:
            print("ERROR: Could not find markCompleted call site")
            return False

    inject = (
        'let P=E.filter(b=>b.hermesSessionId===Y&&b.role==="assistant"&&b.content&&!b._dbPersisted)'
        ';for(let b of P){try{this.storage.addMessage({'
        'id:b.id||("a"+Date.now()+Math.random().toString(36).slice(2)),'
        'roomId:W,senderId:"assistant",senderName:"Hermes",'
        'content:b.content,timestamp:b.timestamp||Math.floor(Date.now()/1e3)'
        '});b._dbPersisted=!0}catch(e){'
        's.warn(e,"[chat-run-socket] failed to persist assistant message to local DB")'
        '}};'
    )

    content = content.replace(marker, inject + marker)

    if len(content) == original_size:
        print("WARNING: No change made; marker replacement had no effect")
        return False

    with open(filepath, "wb") as f:
        f.write(content.encode("utf-8"))

    print(f"Patched: {original_size} -> {len(content)} bytes ({len(content) - original_size:+d})")
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "dist/server/index.js"
    sys.exit(0 if patch_webui(target) else 1)
