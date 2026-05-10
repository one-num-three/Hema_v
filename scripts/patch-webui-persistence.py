"""
Post-build patch for hermes-web-ui dist/server/index.js

Fixes: Assistant messages lost on page refresh — 
addMessage() is never called for AI responses, only for user messages.
This patch adds local SQLite persistence for assistant messages in the
run.completed handler, before markCompleted/syncFromHermes is called.
"""
import sys, re

def patch_webui(filepath: str) -> bool:
    with open(filepath, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    
    original_size = len(content)
    
    # Target: inject addMessage() persistence right before markCompleted is called
    # Find: W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id})
    marker = 'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id})'
    
    if marker not in content:
        # Try alternative pattern (may differ between versions)
        alt = 'this.markCompleted(G,W,{event:w.event,run_id:w.run_id})'
        if alt in content:
            marker = alt
        else:
            print("ERROR: Could not find markCompleted call site")
            return False
    
    # Find the 'this' context variable - it's 'this' in the class method
    # The storage reference should be available as this.storage
    
    # Inject before markCompleted: persist assistant messages to local DB
    inject = (
        # Get all assistant messages for this session and persist them
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
        print("WARNING: No change made — marker replacement had no effect")
        return False
    
    with open(filepath, 'wb') as f:
        f.write(content.encode('utf-8'))
    
    print(f"Patched: {original_size} -> {len(content)} bytes ({len(content)-original_size:+d})")
    return True

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'dist/server/index.js'
    ok = patch_webui(target)
    sys.exit(0 if ok else 1)
