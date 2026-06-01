"""
Post-build patch for hermes-web-ui bundled files.

The upstream Web UI can finish a run without persisting assistant messages to
the local SQLite store. This patch injects persistence before markCompleted()
is called in the bundled server file.

It also forwards the Web UI session_id to the Hermes gateway when the bundled
server calls /v1/responses. Without this, each browser turn can become a fresh
backend session even though the visible Web UI session is the same.

Finally, it patches the bundled client sidebar "API relay" / "中转站" external
link to Hema's current relay login URL.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys


RELAY_LOGIN_URL = "https://ai.opcstore.com/login?expired=true"
OLD_RELAY_URLS = (
    "https://apikey.fun/register?aff=LIBAPI",
)
HEMA_APPS_SCRIPT_NAME = "hema-apps.js"
HEMA_APPS_SCRIPT_VERSION = "20260529-app-backgrounds-v3"
HEMA_APPS_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "hema-app-backgrounds"
ENABLE_HEMA_APPS = True


HEMA_APPS_SCRIPT = Path(__file__).with_name("hema_apps_runtime.js").read_text(encoding="utf-8").strip()


def patch_webui(filepath: str) -> bool:
    with open(filepath, "rb") as f:
        content = f.read().decode("utf-8", errors="replace")

    changed = False
    original_size = len(content)

    if "failed to persist assistant message to local DB" in content:
        print("Persistence patch already applied")
    elif "flushResponseRunToDb" in content:
        print("Upstream already persists response runs")
    else:
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
        changed = True

    if "W&&(e.session_id=W);let p=await fetch(`${N}/v1/responses`" in content:
        print("Session forwarding patch already applied")
    else:
        responses_marker = 'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
        if responses_marker not in content:
            print("ERROR: Could not find /v1/responses fetch call site")
            return False
        content = content.replace(responses_marker, "W&&(e.session_id=W);" + responses_marker, 1)
        changed = True

    if 'PYTHONIOENCODING:"utf-8"' in content and 'PYTHONUTF8:"1"' in content:
        print("UTF-8 child process patch already applied")
    else:
        old_exec_opts = 'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0},'
        new_exec_opts = 'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0,env:{...process.env,PYTHONIOENCODING:"utf-8",PYTHONUTF8:"1"}},'
        if old_exec_opts in content:
            content = content.replace(old_exec_opts, new_exec_opts, 1)
            changed = True
            print("Patched UTF-8 child process env")
        else:
            print("ERROR: Could not find child process exec options")
            return False

    # Upgrade pass: older builds guarded the UPSTREAM short-circuit with the
    # active profile only (".. && (G||'default')===(this.activeProfile||'default')").
    # That let *non-active* profiles fall through to findFreePort, so the WebUI
    # auto-start loop still spawned a second gateway for every other local
    # profile and drifted the port (8642 -> 8643/8665/...). Strip the condition
    # so EVERY profile short-circuits to the external UPSTREAM gateway -
    # start_webui.bat is the single gateway owner; no profile may spawn its own.
    legacy_active_guard = '&&(G||"default")===(this.activeProfile' + '||"default")'
    if legacy_active_guard in content:
        content = content.replace(legacy_active_guard, "")
        changed = True
        print("Broadened UPSTREAM guard from active-profile-only to all profiles")

    upstream_read_patch = 'process.env.UPSTREAM?.trim()' in content and 'new URL(l)' in content
    upstream_resolve_patch = 'if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c}' in content
    upstream_write_patch = 'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;' in content
    upstream_start_patch = "Skipping gateway auto-start" in content
    upstream_stop_patch = 'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;' in content
    duplicate_start_guard = (
        'if(process.env.UPSTREAM?.trim()){'
        's.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);'
        'return this.waitForReady(G,0,l,c,Z)}'
        'if(process.env.UPSTREAM?.trim()){'
        's.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);'
        'return this.waitForReady(G,0,l,c,Z)}'
    )
    if upstream_read_patch and upstream_resolve_patch and upstream_write_patch and upstream_start_patch and upstream_stop_patch and duplicate_start_guard not in content:
        print("Gateway UPSTREAM patch already applied")
    else:
        old_gateway_port_logic = (
            'readProfilePort(G){let l=(0,Ml.join)(this.profileDir(G),"config.yaml"),c=Sp==="container"?"hermes-agent":"127.0.0.1";'
            'if(!(0,yI.existsSync)(l))return{port:8642,host:c};'
            'try{let b=(0,yI.readFileSync)(l,"utf-8"),W=(_I.load(b)||{})?.platforms?.api_server?.extra,d=W?.port||8642,'
            'm=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}'
            'catch{return{port:8642,host:c}}}'
        )
        new_gateway_port_logic = (
            'readProfilePort(G){let l=process.env.UPSTREAM?.trim(),c=Sp==="container"?"hermes-agent":"127.0.0.1";'
            'if(l)try{let b=new URL(l),Z=parseInt(b.port,10)||8642,W=b.hostname||c;'
            'return{port:Z>0&&Z<=65535?Z:8642,host:W||c}}catch{}'
            'let b=(0,Ml.join)(this.profileDir(G),"config.yaml");if(!(0,yI.existsSync)(b))return{port:8642,host:c};'
            'try{let Z=(0,yI.readFileSync)(b,"utf-8"),W=(_I.load(Z)||{})?.platforms?.api_server?.extra,d=W?.port||8642,'
            'm=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}'
            'catch{return{port:8642,host:c}}}'
        )
        if old_gateway_port_logic not in content:
            if not upstream_read_patch:
                print("ERROR: Could not find GatewayManager readProfilePort() call site")
                return False
        else:
            content = content.replace(old_gateway_port_logic, new_gateway_port_logic, 1)
            changed = True

        old_write_profile_port = (
            'writeProfilePort(G,l,c){let b=(0,Ml.join)(this.profileDir(G),"config.yaml");'
            'try{let Z=(0,yI.existsSync)(b)?(0,yI.readFileSync)(b,"utf-8"):"",W=_I.load(Z)||{};'
            'W.platforms||(W.platforms={}),W.platforms.api_server||(W.platforms.api_server={}),'
            'W.platforms.api_server.extra||(W.platforms.api_server.extra={}),W.platforms.api_server.enabled=!0,'
            'W.platforms.api_server.key="",W.platforms.api_server.cors_origins="*",W.platforms.api_server.extra.port=l,'
            'W.platforms.api_server.extra.host=c,W.platforms.api_server.port!==void 0&&delete W.platforms.api_server.port,'
            'W.platforms.api_server.host!==void 0&&delete W.platforms.api_server.host,'
            '(0,yI.writeFileSync)(b,_I.dump(W,{lineWidth:-1}),"utf-8"),s.debug("Updated %s: api_server.extra.port = %d",b,l)}'
            'catch(Z){s.error(Z,\'Failed to write config for profile "%s"\',G)}}'
        )
        new_write_profile_port = (
            'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;'
            'let b=(0,Ml.join)(this.profileDir(G),"config.yaml");'
            'try{let Z=(0,yI.existsSync)(b)?(0,yI.readFileSync)(b,"utf-8"):"",W=_I.load(Z)||{};'
            'W.platforms||(W.platforms={}),W.platforms.api_server||(W.platforms.api_server={}),'
            'W.platforms.api_server.extra||(W.platforms.api_server.extra={}),W.platforms.api_server.enabled=!0,'
            'W.platforms.api_server.key="",W.platforms.api_server.cors_origins="*",W.platforms.api_server.extra.port=l,'
            'W.platforms.api_server.extra.host=c,W.platforms.api_server.port!==void 0&&delete W.platforms.api_server.port,'
            'W.platforms.api_server.host!==void 0&&delete W.platforms.api_server.host,'
            '(0,yI.writeFileSync)(b,_I.dump(W,{lineWidth:-1}),"utf-8"),s.debug("Updated %s: api_server.extra.port = %d",b,l)}'
            'catch(Z){s.error(Z,\'Failed to write config for profile "%s"\',G)}}'
        )
        if old_write_profile_port not in content:
            if not upstream_write_patch:
                print("ERROR: Could not find GatewayManager writeProfilePort() call site")
                return False
        else:
            content = content.replace(old_write_profile_port, new_write_profile_port, 1)
            changed = True

        old_resolve_port = (
            'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G),b=new Set(this.allocatedPorts);'
            'for(let Z of Array.from(this.gateways.values()))Z.host===c&&this.isProcessAlive(Z.pid)&&b.add(Z.port);'
            'if(b.has(l)){let Z=await this.findFreePort(l,c,b);s.info(\'Port %d is in use for profile "%s", reassigning to %d\',l,G,Z),this.writeProfilePort(G,Z,c),l=Z}'
            'else if(await this.checkPortAvailable(l,c))this.writeProfilePort(G,l,c);'
            'else{let W=await this.findFreePort(l,c,b);s.info(\'Port %d is occupied by another process for profile "%s", reassigning to %d\',l,G,W),this.writeProfilePort(G,W,c),l=W}'
            'return this.allocatedPorts.add(l),{port:l,host:c}}'
        )
        new_resolve_port = (
            'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G);'
            'if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c};'
            'let b=new Set(this.allocatedPorts);'
            'for(let Z of Array.from(this.gateways.values()))Z.host===c&&this.isProcessAlive(Z.pid)&&b.add(Z.port);'
            'if(b.has(l)){let Z=await this.findFreePort(l,c,b);s.info(\'Port %d is in use for profile "%s", reassigning to %d\',l,G,Z),this.writeProfilePort(G,Z,c),l=Z}'
            'else if(await this.checkPortAvailable(l,c))this.writeProfilePort(G,l,c);'
            'else{let W=await this.findFreePort(l,c,b);s.info(\'Port %d is occupied by another process for profile "%s", reassigning to %d\',l,G,W),this.writeProfilePort(G,W,c),l=W}'
            'return this.allocatedPorts.add(l),{port:l,host:c}}'
        )
        if old_resolve_port not in content:
            if not upstream_resolve_patch:
                print("ERROR: Could not find GatewayManager resolvePort() call site")
                return False
        else:
            content = content.replace(old_resolve_port, new_resolve_port, 1)
            changed = True

        # start() must also become a no-op under UPSTREAM for ANY profile.
        # resolvePort() no longer drifts the port, but start() would still
        # spawn its own gateway ("gateway run --replace" / "gateway start"),
        # replacing the one start_webui.bat already owns. The auto-start loop
        # calls start() for every local profile, so the guard must not be
        # restricted to the active profile. We keep only the readiness wait
        # (pid=0) so the WebUI tracks the external gateway without ever
        # spawning a second owner.
        old_start_prefix = (
            'async start(G){let{port:l,host:c}=await this.resolvePort(G),'
            'b=this.profileDir(G),Z=oY(c,l);'
        )
        new_start_prefix = (
            'async start(G){let{port:l,host:c}=await this.resolvePort(G),'
            'b=this.profileDir(G),Z=oY(c,l);'
            'if(process.env.UPSTREAM?.trim()){'
            's.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);'
            'return this.waitForReady(G,0,l,c,Z)}'
        )
        if old_start_prefix not in content:
            if not upstream_start_patch:
                print("ERROR: Could not find GatewayManager start() call site")
                return False
        else:
            content = content.replace(old_start_prefix, new_start_prefix, 1)
            changed = True

        start_guard = (
            'if(process.env.UPSTREAM?.trim()){'
            's.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);'
            'return this.waitForReady(G,0,l,c,Z)}'
        )
        duplicate_guard = start_guard + start_guard
        while duplicate_guard in content:
            content = content.replace(duplicate_guard, start_guard, 1)
            changed = True

        old_stop_prefix = 'async stop(G,l=1e4){'
        new_stop_prefix = (
            'async stop(G,l=1e4){'
            'if(process.env.UPSTREAM?.trim())return;'
        )
        if old_stop_prefix not in content:
            if not upstream_stop_patch:
                print("ERROR: Could not find GatewayManager stop() call site")
                return False
        else:
            content = content.replace(old_stop_prefix, new_stop_prefix, 1)
            changed = True

    malformed_direct_logs = 'split(/\n?\n/)' in content

    if (
        "Direct log file listing failed" in content
        and "Direct log file read failed" in content
        and not malformed_direct_logs
    ):
        print("Direct log file patch already applied")
    else:
        new_logs = (
            'async function Ar(){try{let I=(0,Ml.join)(tI(),"logs"),G={agent:"hermes.log",gateway:"gateway.log",errors:"errors.log"},l=[];if(!(0,yI.existsSync)(I))return l;for(let[c,b]of Object.entries(G)){let Z=(0,Ml.join)(I,b);if(!(0,yI.existsSync)(Z))continue;let W=(0,yI.statSync)(Z),d=W.size<1024?`${W.size}B`:W.size<1024*1024?`${Math.round(W.size/1024)}KB`:`${(W.size/1024/1024).toFixed(1)}MB`;l.push({name:c,size:d,modified:new Date(W.mtimeMs).toISOString().replace("T"," ").slice(0,19)})}return l}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
            'async function Lr(I="agent",G=100,l,c,b){try{let Z={agent:"hermes.log",gateway:"gateway.log",errors:"errors.log"},W=Z[I]||`${I}.log`,d=(0,Ml.join)(tI(),"logs",W);if(!(0,yI.existsSync)(d))throw new Error(`Log file not found: ${d}`);let m=(0,yI.readFileSync)(d,"utf-8").split(/\\r?\\n/);if(l){let N=String(l).toLowerCase();m=m.filter(a=>a.toLowerCase().includes(N))}c&&(m=m.filter(N=>N.includes(c))),b&&(m=m.filter(N=>N.includes(b)));let Y=Math.max(1,Number(G)||100);return m.slice(-Y).join(`\\n`)}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
        )
        logs_pattern = re.compile(
            r'async function Ar\(\)\{try\{let\{stdout:I\}=await UI\(rI,\["logs","list"\],\{timeout:1e4,\.\.\.BI\}\),G=\[\],l=I\.trim\(\)\.split\(`.*?`\)\.filter\(c=>c\.includes\("\.log"\)\);for\(let c of l\)\{let b=c\.match\(/\^\\s\+\(\\S\+\)\\s\+\(\[\\d\.\]\+\\w\+\)\\s\+\(\.\+\)\$/\);if\(b\)\{let W=b\[1\]\.replace\(/\\\.log\$/,""\);\["agent","errors","gateway"\]\.includes\(W\)&&G\.push\(\{name:W,size:b\[2\],modified:b\[3\]\.trim\(\)\}\)\}\}return G\}catch\(I\)\{return s\.error\(I,"Hermes CLI: logs list failed"\),\[\]\}\}async function Lr\(I="agent",G=100,l,c,b\)\{let Z=\["logs",I,"-n",String\(G\)\];l&&Z\.push\("--level",l\),c&&Z\.push\("--session",c\),b&&Z\.push\("--since",b\);try\{let\{stdout:W\}=await UI\(rI,Z,\{maxBuffer:10485760,timeout:15e3,\.\.\.BI\}\);return W\}catch\(W\)\{throw s\.error\(W,"Hermes CLI: logs read failed"\),new Error\(`Failed to read logs: \$\{W\.message\}`\)\}\}',
            re.DOTALL,
        )
        if logs_pattern.search(content):
            content = logs_pattern.sub(lambda _m: new_logs, content, count=1)
        elif malformed_direct_logs:
            content = content.replace('split(/\n?\n/)', 'split(/\\r?\\n/)', 1)
        else:
            print("ERROR: Could not repair Hermes logs patch")
            return False
        changed = True

    old_profile_list_bundle = (
        'async function kr(){try{let{stdout:I}=await UI(rI,["profile","list"],{timeout:1e4,...BI}),G=I.trim().split(`\\r\\n`).filter(Boolean),l=[];for(let c of G){if(c.startsWith(" Profile")||c.match(/^ ─/))continue;let b=c.match(/^\\s+(◆)?(.+?)\\s+(\\S+)\\s{2,}(\\S+)\\s{2,}(.*)$/);b&&l.push({name:b[2],active:!!b[1],model:b[3],gateway:b[4],alias:b[5].trim()==="\\u2014"?"":b[5].trim()})}return l}catch(I){throw s.error(I,"Hermes CLI: profile list failed"),new Error(`Failed to list profiles: ${I.message}`)}}'
    )
    profile_list_bundle = (
        'async function kr(){try{let I=require("fs"),G=require("path"),l=require("os"),'
        'b=G.resolve(l.homedir(),".hermes"),Z=G.join(b,"active_profile"),W=G.join(b,"profiles"),d=I.existsSync(Z)?I.readFileSync(Z,"utf-8").trim()||"default":"default",r=process.env.UPSTREAM?.trim()||"",'
        'm=a=>{let Y=G.join(a,"config.yaml");if(!I.existsSync(Y))return"";try{let n=I.readFileSync(Y,"utf-8"),V=n.match(/(?:^|\\r?\\n)model:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+default:\\s*["\\\']?([^"\\\'#\\r\\n]+)["\\\']?/m);if(V?.[1])return V[1].trim();let e=n.match(/^model:\\s*["\\\']?([^"\\\'#\\r\\n]+)["\\\']?/m);return e?.[1]?e[1].trim():""}catch{return""}},'
        'N=async(a,Y)=>{if(r){if(Y!==d)return"stopped";try{return(await fetch(`${r.replace(/\\/$/,"")}/health`,{signal:AbortSignal.timeout(1500)})).ok?"running":"stopped"}catch{return"stopped"}}let n=G.join(a,"gateway.pid"),V=G.join(a,"config.yaml"),e="127.0.0.1",h=8642;if(I.existsSync(V))try{let t=I.readFileSync(V,"utf-8"),p=t.match(/(?:^|\\r?\\n)platforms:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+api_server:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+extra:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+port:\\s*(\\d+)/m),F=t.match(/(?:^|\\r?\\n)platforms:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+api_server:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+extra:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+host:\\s*([^\\r\\n#]+)/m);p?.[1]&&(h=parseInt(p[1],10)||8642),F?.[1]&&(e=F[1].trim().replace(/^["\\\']|["\\\']$/g,"")||e)}catch{}if(!I.existsSync(n))return"stopped";try{let t=I.readFileSync(n,"utf-8").trim(),p=null;if(/^\\d+$/.test(t))p=parseInt(t,10);else try{p=JSON.parse(t)?.pid??null}catch{}if(!(typeof p=="number"&&p>0))return"stopped";try{process.kill(p,0)}catch{return"stopped"}let F=e.includes(":")&&!e.startsWith("[")?`[${e}]`:e,H=await fetch(`http://${F}:${h}/health`,{signal:AbortSignal.timeout(1500)});return H.ok?"running":"stopped"}catch{return"stopped"}},V=[{name:"default",active:d==="default",model:m(b),gateway:await N(b,"default"),alias:""}];'
        'if(I.existsSync(W))for(let a of I.readdirSync(W,{withFileTypes:!0}))if(a.isDirectory()){let Y=G.join(W,a.name);V.push({name:a.name,active:d===a.name,model:m(Y),gateway:await N(Y,a.name),alias:a.name})}'
        'return V.sort((a,Y)=>a.name==="default"?-1:Y.name==="default"?1:a.name.localeCompare(Y.name))}catch(I){throw s.error(I,"Hermes CLI: profile list failed"),new Error(`Failed to list profiles: ${I.message}`)}}'
    )
    if old_profile_list_bundle in content:
        content = content.replace(old_profile_list_bundle, profile_list_bundle, 1)
        changed = True
        print("Patched bundled profile list reader")
    elif 'async function kr(){try{let I=require("fs"),G=require("path"),l=require("os"),' in content and 'gateway:await N(b,"default")' not in content:
        legacy_profile_list_bundle = (
            'async function kr(){try{let I=require("fs"),G=require("path"),l=require("os"),'
            'b=G.resolve(l.homedir(),".hermes"),Z=G.join(b,"active_profile"),W=G.join(b,"profiles"),d=I.existsSync(Z)?I.readFileSync(Z,"utf-8").trim()||"default":"default",'
            'm=a=>{let Y=G.join(a,"config.yaml");if(!I.existsSync(Y))return"";try{let n=I.readFileSync(Y,"utf-8"),V=n.match(/(?:^|\\r?\\n)model:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+default:\\s*["\\\']?([^"\\\'#\\r\\n]+)["\\\']?/m);if(V?.[1])return V[1].trim();let e=n.match(/^model:\\s*["\\\']?([^"\\\'#\\r\\n]+)["\\\']?/m);return e?.[1]?e[1].trim():""}catch{return""}},'
            'N=async a=>{let Y=G.join(a,"gateway.pid"),n=G.join(a,"config.yaml"),V="127.0.0.1",e=8642;if(I.existsSync(n))try{let h=I.readFileSync(n,"utf-8"),t=h.match(/(?:^|\\r?\\n)platforms:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+api_server:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+extra:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+port:\\s*(\\d+)/m),p=h.match(/(?:^|\\r?\\n)platforms:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+api_server:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+extra:\\s*(?:\\r?\\n(?:[ \\t]+.*)*)?\\r?\\n[ \\t]+host:\\s*([^\\r\\n#]+)/m);t?.[1]&&(e=parseInt(t[1],10)||8642),p?.[1]&&(V=p[1].trim().replace(/^["\\\']|["\\\']$/g,"")||V)}catch{}if(!I.existsSync(Y))return"stopped";try{let h=I.readFileSync(Y,"utf-8").trim(),t=null;if(/^\\d+$/.test(h))t=parseInt(h,10);else try{t=JSON.parse(h)?.pid??null}catch{}if(!(typeof t=="number"&&t>0))return"stopped";try{process.kill(t,0)}catch{return"stopped"}let p=V.includes(":")&&!V.startsWith("[")?`[${V}]`:V,F=await fetch(`http://${p}:${e}/health`,{signal:AbortSignal.timeout(1500)});return F.ok?"running":"stopped"}catch{return"stopped"}},V=[{name:"default",active:d==="default",model:m(b),gateway:await N(b),alias:""}];'
            'if(I.existsSync(W))for(let a of I.readdirSync(W,{withFileTypes:!0}))if(a.isDirectory()){let Y=G.join(W,a.name);V.push({name:a.name,active:d===a.name,model:m(Y),gateway:await N(Y),alias:a.name})}'
            'return V.sort((a,Y)=>a.name==="default"?-1:Y.name==="default"?1:a.name.localeCompare(Y.name))}catch(I){throw s.error(I,"Hermes CLI: profile list failed"),new Error(`Failed to list profiles: ${I.message}`)}}'
        )
        if legacy_profile_list_bundle in content:
            content = content.replace(legacy_profile_list_bundle, profile_list_bundle, 1)
            changed = True
            print("Upgraded bundled profile list reader for single-UPSTREAM ownership")
        elif 'r=process.env.UPSTREAM?.trim()||""' not in content:
            profile_list_pattern = re.compile(
                r'async function kr\(\)\{try\{let I=require\("fs"\),G=require\("path"\),l=require\("os"\),.*?throw s\.error\(I,"Hermes CLI: profile list failed"\),new Error\(`Failed to list profiles: \$\{I\.message\}`\)\}\}',
                re.DOTALL,
            )
            content, replacements = profile_list_pattern.subn(lambda _m: profile_list_bundle, content, count=1)
            if replacements:
                changed = True
                print("Regex-upgraded bundled profile list reader for single-UPSTREAM ownership")
    gateway_profiles_bundle = (
        'async listProfiles(){if(process.env.UPSTREAM?.trim())return[this.activeProfile||"default"];let G=["default"],l=(0,Ml.join)(Op,"profiles");'
        'if((0,yI.existsSync)(l))for(let c of(0,yI.readdirSync)(l,{withFileTypes:!0}))c.isDirectory()&&G.push(c.name);'
        'return Array.from(new Set(G)).sort((c,b)=>c==="default"?-1:b==="default"?1:c.localeCompare(b))}'
    )
    gateway_profiles_pattern = re.compile(
        r'async listProfiles\(\)\{try\{let\{stdout:G\}=await vY\(\$d,\["profile","list"\],\{timeout:1e4,windowsHide:!0\}\),l=\[\];for\(let c of G\.trim\(\)\.split\(`.*?`\)\)\{if\(c\.startsWith\(" Profile"\)\|\|c\.match\(/\^ .*?/\)\)continue;let b=c\.match\(/.*?/\);b&&l\.push\(b\[1\]\)\}return l\}catch\{.*?return G\}\}',
        re.DOTALL,
    )
    if 'await vY($d,["profile","list"]' in content:
        content, replacements = gateway_profiles_pattern.subn(lambda _m: gateway_profiles_bundle, content, count=1)
        if replacements:
            changed = True
            print("Patched bundled GatewayManager profile discovery")
    elif 'async listProfiles(){let G=["default"],l=(0,Ml.join)(Op,"profiles");' in content and gateway_profiles_bundle not in content:
        content = content.replace(
            'async listProfiles(){let G=["default"],l=(0,Ml.join)(Op,"profiles");'
            'if((0,yI.existsSync)(l))for(let c of(0,yI.readdirSync)(l,{withFileTypes:!0}))c.isDirectory()&&G.push(c.name);'
            'return Array.from(new Set(G)).sort((c,b)=>c==="default"?-1:b==="default"?1:c.localeCompare(b))}',
            gateway_profiles_bundle,
            1,
        )
        changed = True
        print("Upgraded bundled GatewayManager profile discovery")

    old_gateway_detect_status = (
        'async detectStatus(G){let l=this.readPidFile(G),{port:c,host:b}=this.readProfilePort(G),Z=oY(b,c);'
        'return l&&this.isProcessAlive(l)&&await this.checkHealth(Z)?'
        '(this.gateways.set(G,{pid:l,port:c,host:b,url:Z}),{profile:G,port:c,host:b,url:Z,running:!0,pid:l}):'
        '(this.gateways.delete(G),{profile:G,port:c,host:b,url:Z,running:!1})}'
    )
    new_gateway_detect_status = (
        'async detectStatus(G){let{port:l,host:c}=this.readProfilePort(G),b=oY(c,l),Z=this.activeProfile||"default";'
        'if(process.env.UPSTREAM?.trim()){if(G!==Z)return this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1};'
        'return await this.checkHealth(b)?(this.gateways.set(G,{pid:0,port:l,host:c,url:b}),{profile:G,port:l,host:c,url:b,running:!0}):'
        '(this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1})}'
        'let W=this.readPidFile(G);return W&&this.isProcessAlive(W)&&await this.checkHealth(b)?'
        '(this.gateways.set(G,{pid:W,port:l,host:c,url:b}),{profile:G,port:l,host:c,url:b,running:!0,pid:W}):'
        '(this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1})}'
    )
    if old_gateway_detect_status in content:
        content = content.replace(old_gateway_detect_status, new_gateway_detect_status, 1)
        changed = True
        print("Patched bundled GatewayManager detectStatus for single-UPSTREAM ownership")

    if '"/__hema/shutdown-all"' in content and "Shutting down Web UI and gateway" in content:
        print("Shutdown-all route patch already applied")
    else:
        old_shutdown_router = 'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);'
        legacy_shutdown_router = 'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);An.post("/api/hermes/shutdown-all",BgI);'
        new_shutdown_router = (
            'async function BgI(I){try{let G=String(I.ip||I.request?.ip||"").replace(/^::ffff:/,"");'
            'if(G&&G!=="127.0.0.1"&&G!=="::1"&&G!=="localhost"){I.status=403,I.body={error:"Localhost only"};return}'
            'let l=require("child_process"),c=process.env.ComSpec||"cmd.exe",b=String(process.pid),Z=["ping 127.0.0.1 -n 3 >nul"],W=(0,Ml.join)(tI(),"gateway.pid");'
            'try{let d=(0,yI.readFileSync)(W,"utf-8").trim();/^\\d+$/.test(d)&&Z.push(`taskkill /F /PID ${d} >nul 2>&1`)}catch{}'
            'Z.push(`taskkill /F /PID ${b} >nul 2>&1`),l.spawn(c,["/d","/s","/c",Z.join(" & ")],{detached:!0,windowsHide:!0,stdio:"ignore"}).unref(),I.body={success:!0,message:"Shutting down Web UI and gateway"}}catch(G){I.status=500,I.body={error:G.message}}}'
            'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);An.post("/__hema/shutdown-all",BgI);'
        )
        if legacy_shutdown_router in content:
            content = content.replace(legacy_shutdown_router, new_shutdown_router, 1)
        elif old_shutdown_router in content:
            content = content.replace(old_shutdown_router, new_shutdown_router, 1)
        else:
            print("ERROR: Could not find logs router for shutdown-all patch")
            return False
        changed = True

    duplicate_shutdown = re.compile(r'(async function BgI\(I\)\{.*?\})(async function BgI\(I\)\{.*?\})(var An=new O;An\.get\("/api/hermes/logs",xg\);An\.get\("/api/hermes/logs/:name",Ug\);An\.post\("/__hema/shutdown-all",BgI\);)', re.DOTALL)
    if duplicate_shutdown.search(content):
        content = duplicate_shutdown.sub(r"\2\3", content, count=1)
        changed = True
        print("Removed duplicate shutdown-all handler")

    shutdown_impl_pattern = re.compile(r'async function BgI\(I\)\{.*?\}var An=new O;An\.get\("/api/hermes/logs",xg\);An\.get\("/api/hermes/logs/:name",Ug\);An\.post\("/__hema/shutdown-all",BgI\);', re.DOTALL)
    desired_shutdown_impl = (
        'async function BgI(I){try{let G=String(I.ip||I.request?.ip||"").replace(/^::ffff:/,"");'
        'if(G&&G!=="127.0.0.1"&&G!=="::1"&&G!=="localhost"){I.status=403,I.body={error:"Localhost only"};return}'
        'let l=require("child_process"),c=process.env.ComSpec||"cmd.exe",b=String(process.pid),Z=["ping 127.0.0.1 -n 3 >nul"],W=(0,Ml.join)(tI(),"gateway.pid");'
        'try{let d=(0,yI.readFileSync)(W,"utf-8").trim();/^\\d+$/.test(d)&&Z.push(`taskkill /F /PID ${d} >nul 2>&1`)}catch{}'
        'Z.push(`taskkill /F /PID ${b} >nul 2>&1`),l.spawn(c,["/d","/s","/c",Z.join(" & ")],{detached:!0,windowsHide:!0,stdio:"ignore"}).unref(),I.body={success:!0,message:"Shutting down Web UI and gateway"}}catch(G){I.status=500,I.body={error:G.message}}}'
        'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);An.post("/__hema/shutdown-all",BgI);'
    )
    if '"/__hema/shutdown-all"' in content and ("stop_webui.bat" in content or "gateway stop >nul 2>&1" in content or "gateway.pid" not in content):
        content, replacements = shutdown_impl_pattern.subn(lambda _m: desired_shutdown_impl, content, count=1)
        if replacements:
            changed = True
            print("Normalized shutdown-all handler implementation")

    duplicate_stop_guard = 'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;if(process.env.UPSTREAM?.trim())return;'
    if duplicate_stop_guard in content:
        content = content.replace(
            duplicate_stop_guard,
            'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;',
            1,
        )
        changed = True
        print("Removed duplicate gateway stop guard")

    if not changed:
        malformed_count = content.count('split(/\n?\n/)')
        if malformed_count:
            content = content.replace('split(/\n?\n/)', 'split(/\\r?\\n/)')
            changed = True
            print(f"Normalized malformed log regex: {malformed_count}")

    if not changed:
        print("Already patched; no change needed")
        return True

    if len(content) == original_size:
        print("WARNING: Patch changed text without changing file size")
        return False

    with open(filepath, "wb") as f:
        f.write(content.encode("utf-8"))

    print(f"Patched: {original_size} -> {len(content)} bytes ({len(content) - original_size:+d})")
    return True


def patch_client(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        print(f"Client bundle not found, skipping: {path}")
        return True

    content = path.read_text(encoding="utf-8", errors="replace")
    changed = False

    if RELAY_LOGIN_URL in content:
        print("Relay link patch already applied")
    else:
        for old_url in OLD_RELAY_URLS:
            if old_url in content:
                content = content.replace(old_url, RELAY_LOGIN_URL)
                changed = True

    if RELAY_LOGIN_URL not in content:
        print("ERROR: Could not find sidebar relay link in client bundle")
        return False

    if changed:
        path.write_text(content, encoding="utf-8")
        print(f"Patched relay link: {path}")

    ok = patch_hema_apps(path.parents[2])
    return ok


def patch_app_bundle(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        print(f"App bundle not found, skipping: {path}")
        return True

    content = path.read_text(encoding="utf-8", errors="replace")
    old_poll = (
        'function V(e=3e4){w(),c(),l.value=setInterval(c,e)}'
    )
    new_poll = (
        'function V(e){w(),c();let I=typeof e=="number"&&e>0?e:null,'
        'm=()=>I??(typeof document<"u"&&document.visibilityState==="hidden"?1e4:3e3),'
        'N=()=>{l.value&&(w(),l.value=setInterval(c,m()))};'
        'l.value=setInterval(c,m()),typeof document<"u"&&!document.__hermesHealthPollVisibilityBound&&'
        '(document.__hermesHealthPollVisibilityBound=!0,document.addEventListener("visibilitychange",N))}'
    )

    if new_poll in content:
        print("App health polling patch already applied")
        return True

    if old_poll not in content:
        print("ERROR: Could not find app health polling call site")
        return False

    content = content.replace(old_poll, new_poll, 1)
    path.write_text(content, encoding="utf-8")
    print(f"Patched app health polling: {path}")
    return True


def patch_router_bundle(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        print(f"Router bundle not found, skipping: {path}")
        return True

    content = path.read_text(encoding="utf-8", errors="replace")
    changed = False

    old_profile_header = (
        'const l=ee();l&&l!=="default"&&(n["X-Hermes-Profile"]=l);'
    )
    new_profile_header = (
        'const l=ee();l&&l!=="default"&&!e.startsWith("/api/hermes/profiles")&&(n["X-Hermes-Profile"]=l);'
    )
    if new_profile_header in content:
        print("Router profile header patch already applied")
    elif old_profile_header in content:
        content = content.replace(old_profile_header, new_profile_header, 1)
        changed = True
        print("Patched router profile header handling")
    else:
        print("ERROR: Could not find router profile header call site")
        return False

    old_delete_store = (
        'async function O(r){const s=await W(r);return s&&(delete n.value[r],await i()),s}'
    )
    new_delete_store = (
        'async function O(r){let s=await W(r);'
        'if(s){delete n.value[r],e.value=e.value.filter(m=>m.name!==r),t.value?.name===r&&(t.value=e.value.find(m=>m.active)??null),'
        'a.value===r&&(a.value="default",localStorage.removeItem(p)),await i();return!0}'
        'return await i(),!e.value.some(m=>m.name===r)}'
    )
    if new_delete_store in content:
        print("Router delete profile patch already applied")
    elif old_delete_store in content:
        content = content.replace(old_delete_store, new_delete_store, 1)
        changed = True
        print("Patched router delete profile flow")
    else:
        print("ERROR: Could not find router delete profile call site")
        return False

    if not changed:
        return True

    path.write_text(content, encoding="utf-8")
    print(f"Patched router bundle: {path}")
    return True


def patch_hema_apps(client_root: Path) -> bool:
    script_path = client_root / HEMA_APPS_SCRIPT_NAME
    index_path = client_root / "index.html"
    asset_target_dir = client_root / "hema-app-backgrounds"

    if HEMA_APPS_ASSET_DIR.exists():
        asset_target_dir.mkdir(parents=True, exist_ok=True)
        for source in HEMA_APPS_ASSET_DIR.glob("*.png"):
            target = asset_target_dir / source.name
            if not target.exists() or source.read_bytes() != target.read_bytes():
                shutil.copy2(source, target)
                print(f"Patched Hema app background: {target}")
    else:
        print(f"ERROR: Hema app background assets not found: {HEMA_APPS_ASSET_DIR}")
        return False

    current_script = script_path.read_text(encoding="utf-8", errors="replace") if script_path.exists() else ""
    if current_script != HEMA_APPS_SCRIPT.strip() + "\n":
        script_path.write_text(HEMA_APPS_SCRIPT.strip() + "\n", encoding="utf-8")
        print(f"Patched Hema apps script: {script_path}")
    else:
        print("Hema apps script already applied")

    if not index_path.exists():
        print(f"ERROR: client index.html not found: {index_path}")
        return False

    index = index_path.read_text(encoding="utf-8", errors="replace")
    script_tag = (
        '<script id="hema-apps-loader">'
        '(function(){function load(){'
        'if(document.getElementById("hema-apps-runtime"))return;'
        'var s=document.createElement("script");'
        's.id="hema-apps-runtime";s.defer=true;'
        f's.src="/{HEMA_APPS_SCRIPT_NAME}?v={HEMA_APPS_SCRIPT_VERSION}";'
        's.onerror=function(){console.warn("Hema apps failed to load")};'
        'document.body.appendChild(s)}'
        'if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",load,{once:true});'
        'else load();'
        '})();</script>'
    )
    index, removed = re.subn(
        rf'\s*<script\s+defer\s+src="/{re.escape(HEMA_APPS_SCRIPT_NAME)}(?:\?v=[^"]*)?"></script>',
        "",
        index,
        count=1,
    )
    index, removed_loader = re.subn(
        r'\s*<script id="hema-apps-loader">.*?</script>',
        "",
        index,
        count=1,
        flags=re.DOTALL,
    )
    if not ENABLE_HEMA_APPS:
        if removed or removed_loader:
            index_path.write_text(index, encoding="utf-8")
            print(f"Disabled Hema apps index hook: {index_path}")
        else:
            print("Hema apps index hook disabled")
        return True

    if "</body>" not in index:
        print("ERROR: Could not find </body> in client index.html")
        return False

    index = index.replace("</body>", f"  {script_tag}\n</body>", 1)
    index_path.write_text(index, encoding="utf-8")
    print(f"Patched Hema apps index hook: {index_path}")
    return True


def patch_weixin_route(server_root: Path) -> bool:
    route_path = server_root / "routes" / "hermes" / "weixin.js"
    if not route_path.exists():
        print(f"Weixin route not found, skipping: {route_path}")
        return True

    content = route_path.read_text(encoding="utf-8", errors="replace")
    if "/api/hermes/weixin/status" in content:
        print("Weixin status route already applied")
        return True

    marker = "exports.weixinRoutes.post('/api/hermes/weixin/save', async (ctx) => {"
    if marker not in content:
        print("ERROR: Could not find Weixin save route call site")
        return False

    inject = (
        "exports.weixinRoutes.get('/api/hermes/weixin/status', async (ctx) => {\n"
        "    try {\n"
        "        const profileDir = (0, hermes_profile_1.getActiveProfileDir)();\n"
        "        const statusPath = require('path').join(profileDir, 'weixin_status.json');\n"
        "        const raw = await (0, promises_1.readFile)(statusPath, 'utf-8');\n"
        "        ctx.body = JSON.parse(raw);\n"
        "    }\n"
        "    catch (err) {\n"
        "        if ((err === null || err === void 0 ? void 0 : err.code) === 'ENOENT') {\n"
        "            ctx.body = {\n"
        "                status: 'not_configured',\n"
        "                message: 'Weixin not configured',\n"
        "                verification_code: '',\n"
        "                last_event_at: '',\n"
        "                account_id: '',\n"
        "                last_error: '',\n"
        "            };\n"
        "            return;\n"
        "        }\n"
        "        ctx.status = 500;\n"
        "        ctx.body = { error: (err === null || err === void 0 ? void 0 : err.message) || 'Failed to read Weixin status' };\n"
        "    }\n"
        "});\n"
    )

    content = content.replace(marker, inject + marker, 1)
    route_path.write_text(content, encoding="utf-8")
    print(f"Patched Weixin status route: {route_path}")
    return True


def patch_install(root: Path) -> bool:
    candidates = [
        root / "dist" / "server" / "index.js",
        root / "node_modules" / "hermes-web-ui" / "dist" / "server" / "index.js",
    ]
    server_targets = [path for path in candidates if path.exists()]
    if not server_targets:
        print("ERROR: Could not find hermes-web-ui server bundle")
        return False

    ok = True
    for server_target in server_targets:
        ok = patch_webui(str(server_target)) and ok
        ok = patch_weixin_route(server_target.parent) and ok
        client_root = server_target.parents[1] / "client" / "assets" / "js"
        for router_target in client_root.glob("router-*.js"):
            ok = patch_router_bundle(str(router_target)) and ok
        for client_target in client_root.glob("index-*.js"):
            ok = patch_client(str(client_target)) and ok
        for app_target in client_root.glob("app-*.js"):
            ok = patch_app_bundle(str(app_target)) and ok
    return ok


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/server/index.js")
    if target.is_dir():
        ok = patch_install(target)
    else:
        ok = patch_webui(str(target))
        client_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        if client_arg is not None:
            ok = patch_client(str(client_arg)) and ok
    sys.exit(0 if ok else 1)
