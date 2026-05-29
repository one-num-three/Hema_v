from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
PATCH_SCRIPT = ROOT / "scripts" / "patch-webui-persistence.py"


def load_patch_module():
    spec = importlib.util.spec_from_file_location("patch_webui_persistence", PATCH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class PatchWebuiPersistenceTests(unittest.TestCase):
    def test_patch_install_updates_dist_and_node_modules_bundles(self):
        module = load_patch_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            server_snippet = (
                'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id});'
                'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
                'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0},'
                'readProfilePort(G){let l=(0,Ml.join)(this.profileDir(G),"config.yaml"),c=Sp==="container"?"hermes-agent":"127.0.0.1";if(!(0,yI.existsSync)(l))return{port:8642,host:c};try{let b=(0,yI.readFileSync)(l,"utf-8"),W=(_I.load(b)||{})?.platforms?.api_server?.extra,d=W?.port||8642,m=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}catch{return{port:8642,host:c}}}'
                'writeProfilePort(G,l,c){let b=(0,Ml.join)(this.profileDir(G),"config.yaml");try{let Z=(0,yI.existsSync)(b)?(0,yI.readFileSync)(b,"utf-8"):"",W=_I.load(Z)||{};W.platforms||(W.platforms={}),W.platforms.api_server||(W.platforms.api_server={}),W.platforms.api_server.extra||(W.platforms.api_server.extra={}),W.platforms.api_server.enabled=!0,W.platforms.api_server.key="",W.platforms.api_server.cors_origins="*",W.platforms.api_server.extra.port=l,W.platforms.api_server.extra.host=c,W.platforms.api_server.port!==void 0&&delete W.platforms.api_server.port,W.platforms.api_server.host!==void 0&&delete W.platforms.api_server.host,(0,yI.writeFileSync)(b,_I.dump(W,{lineWidth:-1}),"utf-8"),s.debug("Updated %s: api_server.extra.port = %d",b,l)}catch(Z){s.error(Z,\'Failed to write config for profile "%s"\',G)}}'
                'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G),b=new Set(this.allocatedPorts);for(let Z of Array.from(this.gateways.values()))Z.host===c&&this.isProcessAlive(Z.pid)&&b.add(Z.port);if(b.has(l)){let Z=await this.findFreePort(l,c,b);s.info(\'Port %d is in use for profile "%s", reassigning to %d\',l,G,Z),this.writeProfilePort(G,Z,c),l=Z}else if(await this.checkPortAvailable(l,c))this.writeProfilePort(G,l,c);else{let W=await this.findFreePort(l,c,b);s.info(\'Port %d is occupied by another process for profile "%s", reassigning to %d\',l,G,W),this.writeProfilePort(G,W,c),l=W}return this.allocatedPorts.add(l),{port:l,host:c}}'
                'async listProfiles(){let G=["default"],l=(0,Ml.join)(Op,"profiles");if((0,yI.existsSync)(l))for(let c of(0,yI.readdirSync)(l,{withFileTypes:!0}))c.isDirectory()&&G.push(c.name);return Array.from(new Set(G)).sort((c,b)=>c==="default"?-1:b==="default"?1:c.localeCompare(b))}'
                'async detectStatus(G){let l=this.readPidFile(G),{port:c,host:b}=this.readProfilePort(G),Z=oY(b,c);return l&&this.isProcessAlive(l)&&await this.checkHealth(Z)?(this.gateways.set(G,{pid:l,port:c,host:b,url:Z}),{profile:G,port:c,host:b,url:Z,running:!0,pid:l}):(this.gateways.delete(G),{profile:G,port:c,host:b,url:Z,running:!1})}'
                'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);return this.waitForReady(G,0,l,c,Z)}'
                'async stop(G,l=1e4){let c=this.gateways.get(G),b=c?.url||(()=>{let{port:W,host:d}=this.readProfilePort(G);return oY(d,W)})();this.gateways.delete(G)}'
                'async function Ar(){try{return[]}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
                'async function Lr(I="agent",G=100,l,c,b){try{return ""}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
                'async function kr(){try{let{stdout:I}=await UI(rI,["profile","list"],{timeout:1e4,...BI}),G=I.trim().split(`\\r\\n`).filter(Boolean),l=[];for(let c of G){if(c.startsWith(" Profile")||c.match(/^ ─/))continue;let b=c.match(/^\\s+(◆)?(.+?)\\s+(\\S+)\\s{2,}(\\S+)\\s{2,}(.*)$/);b&&l.push({name:b[2],active:!!b[1],model:b[3],gateway:b[4],alias:b[5].trim()==="\\u2014"?"":b[5].trim()})}return l}catch(I){throw s.error(I,"Hermes CLI: profile list failed"),new Error(`Failed to list profiles: ${I.message}`)}}'
                'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);'
            )

            for bundle in [
                root / "dist" / "server" / "index.js",
                root / "node_modules" / "hermes-web-ui" / "dist" / "server" / "index.js",
            ]:
                bundle.parent.mkdir(parents=True, exist_ok=True)
                bundle.write_text(server_snippet, encoding="utf-8")

            self.assertTrue(module.patch_install(root))

            for bundle in [
                root / "dist" / "server" / "index.js",
                root / "node_modules" / "hermes-web-ui" / "dist" / "server" / "index.js",
            ]:
                patched = bundle.read_text(encoding="utf-8")
                self.assertIn('async listProfiles(){if(process.env.UPSTREAM?.trim())return[this.activeProfile||"default"];', patched)
                self.assertIn('if(process.env.UPSTREAM?.trim()){if(G!==Z)return this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1};', patched)
                self.assertIn('gateway:await N(b,"default")', patched)

    def test_patch_webui_prevents_upstream_port_rewrite(self):
        module = load_patch_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "index.js"
            bundle.write_text(
                (
                    'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id});'
                    'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
                    'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0},'
                    'readProfilePort(G){let l=(0,Ml.join)(this.profileDir(G),"config.yaml"),c=Sp==="container"?"hermes-agent":"127.0.0.1";'
                    'if(!(0,yI.existsSync)(l))return{port:8642,host:c};'
                    'try{let b=(0,yI.readFileSync)(l,"utf-8"),W=(_I.load(b)||{})?.platforms?.api_server?.extra,d=W?.port||8642,'
                    'm=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}'
                    'catch{return{port:8642,host:c}}}'
                    'writeProfilePort(G,l,c){let b=(0,Ml.join)(this.profileDir(G),"config.yaml");'
                    'try{let Z=(0,yI.existsSync)(b)?(0,yI.readFileSync)(b,"utf-8"):"",W=_I.load(Z)||{};'
                    'W.platforms||(W.platforms={}),W.platforms.api_server||(W.platforms.api_server={}),'
                    'W.platforms.api_server.extra||(W.platforms.api_server.extra={}),W.platforms.api_server.enabled=!0,'
                    'W.platforms.api_server.key="",W.platforms.api_server.cors_origins="*",W.platforms.api_server.extra.port=l,'
                    'W.platforms.api_server.extra.host=c,W.platforms.api_server.port!==void 0&&delete W.platforms.api_server.port,'
                    'W.platforms.api_server.host!==void 0&&delete W.platforms.api_server.host,'
                    '(0,yI.writeFileSync)(b,_I.dump(W,{lineWidth:-1}),"utf-8"),s.debug("Updated %s: api_server.extra.port = %d",b,l)}'
                    'catch(Z){s.error(Z,\'Failed to write config for profile "%s"\',G)}}'
                    'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G),b=new Set(this.allocatedPorts);'
                    'for(let Z of Array.from(this.gateways.values()))Z.host===c&&this.isProcessAlive(Z.pid)&&b.add(Z.port);'
                    'if(b.has(l)){let Z=await this.findFreePort(l,c,b);s.info(\'Port %d is in use for profile "%s", reassigning to %d\',l,G,Z),this.writeProfilePort(G,Z,c),l=Z}'
                    'else if(await this.checkPortAvailable(l,c))this.writeProfilePort(G,l,c);'
                    'else{let W=await this.findFreePort(l,c,b);s.info(\'Port %d is occupied by another process for profile "%s", reassigning to %d\',l,G,W),this.writeProfilePort(G,W,c),l=W}'
                    'return this.allocatedPorts.add(l),{port:l,host:c}}'
                    'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);'
                    'if(jp)return new Promise((d,m)=>{let N={...process.env,HERMES_HOME:b},a=(0,S1.spawn)($d,["gateway","run","--replace"],{detached:!0,stdio:"ignore",windowsHide:!0,env:N});'
                    'a.unref();let Y=a.pid??0;s.info(\'Starting gateway for profile "%s" (run mode, PID: %d, port: %d)\',G,Y,l),this.waitForReady(G,Y,l,c,Z).then(d).catch(m)});'
                    's.info(\'Starting gateway for profile "%s" (start mode, port: %d)\',G,l);'
                    'let W={...process.env,HERMES_HOME:b};'
                    'try{let{stdout:d}=await vY($d,["gateway","start"],{timeout:3e4,env:W,windowsHide:!0});s.debug("gateway start output: %s",d?.trim())}'
                    'catch{try{let{stdout:d}=await vY($d,["gateway","restart"],{timeout:3e4,env:W,windowsHide:!0});s.debug("gateway restart output: %s",d?.trim())}catch(d){s.warn(d,"gateway start/restart (non-fatal)")}}'
                    'return this.waitForReady(G,0,l,c,Z)}'
                    'async stop(G,l=1e4){let c=this.gateways.get(G),b=c?.url||(()=>{let{port:W,host:d}=this.readProfilePort(G);return oY(d,W)})();'
                    'if(jp){let W=c?.pid;if(W||(W=this.readPidFile(G)??void 0),W)try{process.kill(-W,"SIGTERM")}catch{try{process.kill(W,"SIGTERM")}catch{}}}'
                    'else try{let W=this.profileDir(G),d={...process.env,HERMES_HOME:W};await vY($d,["gateway","stop"],{timeout:1e4,env:d,windowsHide:!0})}catch{}'
                    'let Z=Date.now()+l;for(;Date.now()<Z;){if(!await this.checkHealth(b,1e3)){this.gateways.delete(G),s.info(\'Stopped gateway for profile "%s"\',G);return}await new Promise(W=>setTimeout(W,300))}'
                    'this.gateways.delete(G),s.warn(\'Stopped gateway for profile "%s" (timeout)\',G)}'
                    'async function Ar(){try{return[]}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
                    'async function Lr(I="agent",G=100,l,c,b){try{return ""}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
                    'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);'
                ),
                encoding="utf-8",
            )

            self.assertTrue(module.patch_webui(str(bundle)))
            patched = bundle.read_text(encoding="utf-8")

            self.assertIn('process.env.UPSTREAM?.trim()', patched)
            self.assertIn(
                'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;',
                patched,
            )
            self.assertIn(
                'if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c};',
                patched,
            )
            self.assertIn(
                'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);if(process.env.UPSTREAM?.trim()){s.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);return this.waitForReady(G,0,l,c,Z)}',
                patched,
            )
            self.assertIn(
                'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;',
                patched,
            )
            self.assertEqual(patched.count("Skipping gateway auto-start"), 1)
            self.assertEqual(patched.count('if(process.env.UPSTREAM?.trim())return;'), 2)

    def test_patch_webui_upgrades_profile_status_to_pid_plus_health(self):
        module = load_patch_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "index.js"
            bundle.write_text(
                (
                    'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id});'
                    'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
                    'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0,env:{...process.env,PYTHONIOENCODING:"utf-8",PYTHONUTF8:"1"}},'
                    'readProfilePort(G){let l=process.env.UPSTREAM?.trim(),c=Sp==="container"?"hermes-agent":"127.0.0.1";if(l)try{let b=new URL(l),Z=parseInt(b.port,10)||8642,W=b.hostname||c;return{port:Z>0&&Z<=65535?Z:8642,host:W||c}}catch{}return{port:8642,host:c}}'
                    'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;}'
                    'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G);if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c};return this.allocatedPorts.add(l),{port:l,host:c}}'
                    'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);if(process.env.UPSTREAM?.trim()){s.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);return this.waitForReady(G,0,l,c,Z)}return this.waitForReady(G,0,l,c,Z)}'
                    'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;}'
                    'async function Ar(){try{return[]}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
                    'async function Lr(I="agent",G=100,l,c,b){try{return ""}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
                    'async function kr(){try{let{stdout:I}=await UI(rI,["profile","list"],{timeout:1e4,...BI}),G=I.trim().split(`\\r\\n`).filter(Boolean),l=[];for(let c of G){if(c.startsWith(" Profile")||c.match(/^ ─/))continue;let b=c.match(/^\\s+(◆)?(.+?)\\s+(\\S+)\\s{2,}(\\S+)\\s{2,}(.*)$/);b&&l.push({name:b[2],active:!!b[1],model:b[3],gateway:b[4],alias:b[5].trim()==="\\u2014"?"":b[5].trim()})}return l}catch(I){throw s.error(I,"Hermes CLI: profile list failed"),new Error(`Failed to list profiles: ${I.message}`)}}'
                    'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);'
                ),
                encoding="utf-8",
            )

            self.assertTrue(module.patch_webui(str(bundle)))
            patched = bundle.read_text(encoding="utf-8")
            self.assertIn('gateway:await N(b,"default")', patched)
            self.assertIn('H=await fetch(`http://${F}:${h}/health`', patched)
            self.assertIn('return H.ok?"running":"stopped"', patched)
            self.assertIn('if(r){if(Y!==d)return"stopped";', patched)
            self.assertIn('gateway:await N(Y,a.name)', patched)

    def test_patch_webui_limits_upstream_gateway_manager_to_active_profile(self):
        module = load_patch_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "index.js"
            bundle.write_text(
                (
                    'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id});'
                    'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
                    'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0,env:{...process.env,PYTHONIOENCODING:"utf-8",PYTHONUTF8:"1"}},'
                    'readProfilePort(G){let l=(0,Ml.join)(this.profileDir(G),"config.yaml"),c=Sp==="container"?"hermes-agent":"127.0.0.1";if(!(0,yI.existsSync)(l))return{port:8642,host:c};try{let b=(0,yI.readFileSync)(l,"utf-8"),W=(_I.load(b)||{})?.platforms?.api_server?.extra,d=W?.port||8642,m=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}catch{return{port:8642,host:c}}}'
                    'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;}'
                    'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G);if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c};return this.allocatedPorts.add(l),{port:l,host:c}}'
                    'async listProfiles(){let G=["default"],l=(0,Ml.join)(Op,"profiles");if((0,yI.existsSync)(l))for(let c of(0,yI.readdirSync)(l,{withFileTypes:!0}))c.isDirectory()&&G.push(c.name);return Array.from(new Set(G)).sort((c,b)=>c==="default"?-1:b==="default"?1:c.localeCompare(b))}'
                    'async detectStatus(G){let l=this.readPidFile(G),{port:c,host:b}=this.readProfilePort(G),Z=oY(b,c);return l&&this.isProcessAlive(l)&&await this.checkHealth(Z)?(this.gateways.set(G,{pid:l,port:c,host:b,url:Z}),{profile:G,port:c,host:b,url:Z,running:!0,pid:l}):(this.gateways.delete(G),{profile:G,port:c,host:b,url:Z,running:!1})}'
                    'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);if(process.env.UPSTREAM?.trim()){s.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);return this.waitForReady(G,0,l,c,Z)}return this.waitForReady(G,0,l,c,Z)}'
                    'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;}'
                    'async function Ar(){try{return[]}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
                    'async function Lr(I="agent",G=100,l,c,b){try{return ""}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
                    'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);'
                ),
                encoding="utf-8",
            )

            self.assertTrue(module.patch_webui(str(bundle)))
            patched = bundle.read_text(encoding="utf-8")
            self.assertIn(
                'async listProfiles(){if(process.env.UPSTREAM?.trim())return[this.activeProfile||"default"];',
                patched,
            )
            self.assertIn(
                'if(process.env.UPSTREAM?.trim()){if(G!==Z)return this.gateways.delete(G),{profile:G,port:l,host:c,url:b,running:!1};',
                patched,
            )
            self.assertIn(
                'return await this.checkHealth(b)?(this.gateways.set(G,{pid:0,port:l,host:c,url:b}),{profile:G,port:l,host:c,url:b,running:!0}):',
                patched,
            )

    def test_patch_webui_deduplicates_existing_upstream_guard(self):
        module = load_patch_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "index.js"
            guard = (
                'if(process.env.UPSTREAM?.trim()){'
                's.info(\'Skipping gateway auto-start for profile "%s" (external UPSTREAM on %s:%d)\',G,c,l);'
                'return this.waitForReady(G,0,l,c,Z)}'
            )
            bundle.write_text(
                (
                    'W&&await this.markCompleted(G,W,{event:w.event,run_id:w.run_id});'
                    'let p=await fetch(`${N}/v1/responses`,{method:"POST",headers:h,body:JSON.stringify(e),signal:t.signal});'
                    'UI=(0,Jr.promisify)(PY.execFile),BI={windowsHide:!0,env:{...process.env,PYTHONIOENCODING:"utf-8",PYTHONUTF8:"1"}},'
                    'readProfilePort(G){let l=process.env.UPSTREAM?.trim(),c=Sp==="container"?"hermes-agent":"127.0.0.1";if(l)try{let b=new URL(l),Z=parseInt(b.port,10)||8642,W=b.hostname||c;return{port:Z>0&&Z<=65535?Z:8642,host:W||c}}catch{}return{port:8642,host:c}}'
                    'writeProfilePort(G,l,c){if(process.env.UPSTREAM?.trim())return;}'
                    'async resolvePort(G){let{port:l,host:c}=this.readProfilePort(G);if(process.env.UPSTREAM?.trim())return this.allocatedPorts.add(l),{port:l,host:c};return this.allocatedPorts.add(l),{port:l,host:c}}'
                    'async start(G){let{port:l,host:c}=await this.resolvePort(G),b=this.profileDir(G),Z=oY(c,l);'
                    + guard + guard +
                    'return this.waitForReady(G,0,l,c,Z)}'
                    'async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;if(process.env.UPSTREAM?.trim())return;}'
                    'async function Ar(){try{return[]}catch(I){return s.error(I,"Direct log file listing failed"),[]}}'
                    'async function Lr(I="agent",G=100,l,c,b){try{return ""}catch(Z){throw s.error(Z,"Direct log file read failed"),new Error(`Failed to read logs: ${Z.message}`)}}'
                    'var An=new O;An.get("/api/hermes/logs",xg);An.get("/api/hermes/logs/:name",Ug);An.post("/__hema/shutdown-all",BgI);'
                ),
                encoding="utf-8",
            )

            self.assertTrue(module.patch_webui(str(bundle)))
            patched = bundle.read_text(encoding="utf-8")
            self.assertEqual(patched.count("Skipping gateway auto-start"), 1)
            self.assertEqual(
                patched.count('async stop(G,l=1e4){if(process.env.UPSTREAM?.trim())return;'),
                1,
            )


if __name__ == "__main__":
    unittest.main()
