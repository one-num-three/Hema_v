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
import sys


RELAY_LOGIN_URL = "https://ai.opcstore.com/login?expired=true"
OLD_RELAY_URLS = (
    "https://apikey.fun/register?aff=LIBAPI",
)
HEMA_APPS_SCRIPT_NAME = "hema-apps.js"


HEMA_APPS_SCRIPT = r"""
(function () {
  const APPS_HASH = "#/hema/apps";
  const CHAT_HASH = "#/hermes/chat";
  const PROMPT_KEY = "hema.pendingAppPrompt";

  const apps = [
    {
      name: "制作/修改PPT",
      desc: "调用 ppt-master skill，先确认主题、页数、风格和素材。",
      accent: "#2563eb",
      action: "ppt"
    },
    { name: "文档整理", desc: "把长文、会议纪要或资料整理成清晰结构。", accent: "#0f766e" },
    { name: "表格分析", desc: "清洗数据、提炼结论，生成可读分析摘要。", accent: "#ca8a04" },
    { name: "图片理解", desc: "识别截图、界面和图片内容，输出说明。", accent: "#9333ea" },
    { name: "网页总结", desc: "读取网页信息并整理重点，适合快速调研。", accent: "#dc2626" },
    { name: "代码助手", desc: "解释、修改和排查代码问题。", accent: "#334155" },
    { name: "工作计划", desc: "把目标拆成任务清单和执行顺序。", accent: "#16a34a" },
    { name: "日报周报", desc: "根据素材生成简洁汇报文本。", accent: "#ea580c" },
    { name: "合同检查", desc: "提取风险点和待确认条款。", accent: "#7c3aed" },
    { name: "知识库问答", desc: "围绕已有资料做检索和问答。", accent: "#0891b2" },
    { name: "邮件润色", desc: "改写语气、结构和表达方式。", accent: "#be123c" },
    { name: "更多应用", desc: "占位功能，后续按你的业务继续补。", accent: "#64748b" }
  ];

  function ensureStyle() {
    if (document.getElementById("hema-apps-style")) return;
    const style = document.createElement("style");
    style.id = "hema-apps-style";
    style.textContent = `
      .app-main{position:relative}
      .hema-app-link{display:flex!important;align-items:center!important;gap:16px!important;height:44px!important;margin:2px 42px!important;padding:0!important;border-radius:9px!important;color:#666!important;text-decoration:none!important;font-size:16px!important;font-weight:400!important;box-sizing:border-box!important}
      .hema-app-link:hover,.hema-app-link.active{background:#e3e3e3!important;color:#222!important}
      .hema-app-link .nav-icon{width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;color:inherit;flex:0 0 22px}
      .hema-app-link svg{width:22px;height:22px;stroke-width:1.75}
      .hema-app-link .nav-label{line-height:1}
      .sidebar.collapsed .hema-app-link,.collapsed .hema-app-link{margin:4px auto!important;width:44px!important;justify-content:center!important}
      .sidebar.collapsed .hema-app-link .nav-label,.collapsed .hema-app-link .nav-label{display:none!important}
      .hema-apps-view{position:absolute;inset:0;z-index:40;background:#fff;display:none;overflow:auto}
      .hema-apps-view.is-open{display:block}
      .hema-apps-shell{max-width:none;margin:0;padding:42px 48px 56px}
      .hema-apps-kicker{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#9a9a9a;margin-bottom:8px}
      .hema-apps-title{font-size:30px;font-weight:700;color:#171717;margin:0}
      .hema-apps-subtitle{font-size:14px;color:#7a7a7a;margin:10px 0 26px;max-width:720px;line-height:1.7}
      .hema-apps-grid{display:grid;grid-template-columns:repeat(4,minmax(154px,1fr));gap:16px}
      .hema-app-card{height:208px;border:1px solid #e9e9e9;border-radius:16px;background:#fff;overflow:hidden;text-align:left;padding:0;cursor:pointer;box-shadow:0 6px 18px rgba(15,23,42,.045);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease,background .16s ease}
      .hema-app-card:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(15,23,42,.09);border-color:#dcdcdc;background:#fdfdfd}
      .hema-app-shot{height:62%;position:relative;background:linear-gradient(145deg,#f8fafc,#edf1f6);overflow:hidden}
      .hema-app-shot:before{content:"";position:absolute;left:17px;right:17px;top:18px;bottom:18px;border-radius:14px;background:#fff;border:1px solid rgba(15,23,42,.06);box-shadow:0 12px 28px rgba(15,23,42,.08)}
      .hema-app-shot:after{content:"";position:absolute;left:34px;right:34px;top:43px;height:9px;border-radius:99px;background:linear-gradient(90deg,var(--hema-accent),rgba(148,163,184,.26));box-shadow:0 26px 0 rgba(148,163,184,.15),0 52px 0 rgba(148,163,184,.10)}
      .hema-app-orb{position:absolute;right:30px;bottom:26px;width:54px;height:34px;border-radius:12px;background:color-mix(in srgb,var(--hema-accent) 72%,white);opacity:.86;box-shadow:0 10px 24px rgba(15,23,42,.12)}
      .hema-app-body{height:38%;border-top:1px solid #eeeeee;padding:13px 15px 12px;box-sizing:border-box}
      .hema-app-name{font-size:14px;font-weight:650;color:#202020;margin-bottom:5px}
      .hema-app-desc{font-size:12px;line-height:1.45;color:#8d8d8d;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
      .hema-app-modal-mask{position:fixed;inset:0;background:rgba(15,23,42,.28);z-index:90;display:none;align-items:center;justify-content:center}
      .hema-app-modal-mask.is-open{display:flex}
      .hema-app-modal{width:min(560px,calc(100vw - 32px));background:#fff;border-radius:20px;box-shadow:0 26px 80px rgba(15,23,42,.24);padding:24px}
      .hema-app-modal h3{font-size:20px;margin:0 0 8px;color:#171717}
      .hema-app-modal p{font-size:13px;color:#777;margin:0 0 14px;line-height:1.6}
      .hema-app-modal textarea{width:100%;height:148px;border:1px solid #ddd;border-radius:14px;padding:12px 14px;resize:vertical;font:14px/1.5 inherit;box-sizing:border-box;outline:none}
      .hema-app-modal textarea:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}
      .hema-app-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px}
      .hema-app-actions button{border:0;border-radius:12px;padding:10px 16px;font-size:14px;cursor:pointer}
      .hema-app-cancel{background:#f2f2f2;color:#444}
      .hema-app-send{background:#171717;color:#fff}
      .hema-app-toast{position:fixed;right:24px;bottom:24px;z-index:100;background:#171717;color:#fff;border-radius:12px;padding:10px 14px;font-size:13px;display:none}
      .hema-app-toast.is-open{display:block}
      @media (max-width:1100px){.hema-apps-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hema-apps-shell{padding:30px 22px 44px}}
      @media (max-width:640px){.hema-apps-grid{grid-template-columns:1fr}.hema-app-card{height:236px}}
    `;
    document.head.appendChild(style);
  }

  function icon() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>';
  }

  function ensureSidebarLink() {
    const relay = document.querySelector(".nav-item.fun-link");
    if (!relay || document.querySelector(".hema-app-link")) return;
    const link = document.createElement("a");
    link.className = "nav-item hema-app-link";
    link.href = APPS_HASH;
    link.innerHTML = `<span class="nav-icon">${icon()}</span><span class="nav-label">应用</span>`;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      window.location.hash = APPS_HASH;
      render();
    });
    relay.insertAdjacentElement("afterend", link);
  }

  function card(app, index) {
    return `
      <button class="hema-app-card" data-action="${app.action || "mock"}" style="--hema-accent:${app.accent}">
        <div class="hema-app-shot" aria-hidden="true"><span class="hema-app-orb"></span></div>
        <div class="hema-app-body">
          <div class="hema-app-name">${app.name}</div>
          <div class="hema-app-desc">${app.desc}</div>
        </div>
      </button>
    `;
  }

  function ensureView() {
    let view = document.querySelector(".hema-apps-view");
    const main = document.querySelector(".app-main") || document.body;
    if (view) return view;
    view = document.createElement("section");
    view.className = "hema-apps-view";
    view.innerHTML = `
      <div class="hema-apps-shell">
        <div class="hema-apps-kicker">Hema Apps</div>
        <h1 class="hema-apps-title">应用</h1>
        <p class="hema-apps-subtitle">把常用能力做成入口。先上线 PPT，其它功能先占位，后面按真实工作流补齐。</p>
        <div class="hema-apps-grid">${apps.map(card).join("")}</div>
      </div>
    `;
    main.appendChild(view);
    view.addEventListener("click", (event) => {
      const item = event.target.closest(".hema-app-card");
      if (!item) return;
      if (item.dataset.action === "ppt") openPptModal();
      else toast("这个应用还是占位，我们后面再一起定。");
    });
    return view;
  }

  function ensureModal() {
    let modal = document.querySelector(".hema-app-modal-mask");
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "hema-app-modal-mask";
    modal.innerHTML = `
      <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="制作或修改PPT">
        <h3>制作/修改PPT</h3>
        <p>告诉我主题、用途、页数、风格、是否已有素材。提交后会带着 ppt-master skill 提示打开聊天。</p>
        <textarea placeholder="例如：帮我做一个 10 页的产品介绍 PPT，风格科技感，受众是客户，重点讲功能、案例和报价。"></textarea>
        <div class="hema-app-actions">
          <button class="hema-app-cancel" type="button">取消</button>
          <button class="hema-app-send" type="button">发送给 Hermes</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    modal.querySelector(".hema-app-cancel").addEventListener("click", () => modal.classList.remove("is-open"));
    modal.addEventListener("click", (event) => {
      if (event.target === modal) modal.classList.remove("is-open");
    });
    modal.querySelector(".hema-app-send").addEventListener("click", () => {
      const need = modal.querySelector("textarea").value.trim();
      if (!need) {
        toast("先写一点 PPT 需求，我再帮你带到聊天里。");
        return;
      }
      const prompt = `请使用 ppt-master skill 帮我制作/修改PPT。我的需求是：\n${need}\n\n请先追问缺失信息，再给出制作方案。`;
      localStorage.setItem(PROMPT_KEY, prompt);
      modal.classList.remove("is-open");
      window.location.hash = CHAT_HASH;
      setTimeout(fillChatInput, 450);
    });
    return modal;
  }

  function openPptModal() {
    const modal = ensureModal();
    modal.classList.add("is-open");
    setTimeout(() => modal.querySelector("textarea").focus(), 50);
  }

  function fillChatInput() {
    const prompt = localStorage.getItem(PROMPT_KEY);
    if (!prompt) return;
    const input = document.querySelector("textarea") || document.querySelector('[contenteditable="true"]');
    if (!input) {
      navigator.clipboard && navigator.clipboard.writeText(prompt).catch(() => {});
      toast("已复制 PPT 提示词，请粘贴到聊天框。");
      return;
    }
    if (input.tagName === "TEXTAREA" || input.tagName === "INPUT") {
      input.value = prompt;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } else {
      input.textContent = prompt;
      input.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: prompt }));
    }
    localStorage.removeItem(PROMPT_KEY);
    input.focus();
    toast("PPT 需求已填入聊天框，确认后发送即可。");
  }

  function toast(message) {
    let node = document.querySelector(".hema-app-toast");
    if (!node) {
      node = document.createElement("div");
      node.className = "hema-app-toast";
      document.body.appendChild(node);
    }
    node.textContent = message;
    node.classList.add("is-open");
    clearTimeout(node._timer);
    node._timer = setTimeout(() => node.classList.remove("is-open"), 2600);
  }

  function render() {
    ensureStyle();
    ensureSidebarLink();
    const view = ensureView();
    const open = window.location.hash === APPS_HASH;
    view.classList.toggle("is-open", open);
    document.querySelector(".hema-app-link")?.classList.toggle("active", open);
    if (!open && window.location.hash === CHAT_HASH) setTimeout(fillChatInput, 300);
  }

  function closeAppsView() {
    document.querySelector(".hema-apps-view")?.classList.remove("is-open");
    document.querySelector(".hema-app-link")?.classList.remove("active");
  }

  function renderSoon() {
    window.requestAnimationFrame(() => {
      if (window.location.hash !== APPS_HASH) closeAppsView();
      render();
    });
  }

  function patchHistoryEvents() {
    if (window.__hemaAppsHistoryPatched) return;
    window.__hemaAppsHistoryPatched = true;
    const fire = () => window.dispatchEvent(new Event("hema-route-change"));
    for (const name of ["pushState", "replaceState"]) {
      const original = history[name];
      history[name] = function patchedHistoryState() {
        const result = original.apply(this, arguments);
        fire();
        return result;
      };
    }
    window.addEventListener("popstate", fire);
  }

  const observer = new MutationObserver(() => ensureSidebarLink());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (link && !link.classList.contains("hema-app-link")) setTimeout(renderSoon, 0);
  }, true);
  patchHistoryEvents();
  window.addEventListener("hashchange", renderSoon);
  window.addEventListener("hema-route-change", renderSoon);
  window.addEventListener("load", renderSoon);
  setInterval(renderSoon, 1200);
  renderSoon();
})();
"""


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


def patch_hema_apps(client_root: Path) -> bool:
    script_path = client_root / HEMA_APPS_SCRIPT_NAME
    index_path = client_root / "index.html"

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
    script_tag = f'<script defer src="/{HEMA_APPS_SCRIPT_NAME}"></script>'
    if script_tag in index:
        print("Hema apps index hook already applied")
        return True

    if "</body>" not in index:
        print("ERROR: Could not find </body> in client index.html")
        return False

    index = index.replace("</body>", f"  {script_tag}\n</body>", 1)
    index_path.write_text(index, encoding="utf-8")
    print(f"Patched Hema apps index hook: {index_path}")
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
        client_root = server_target.parents[1] / "client" / "assets" / "js"
        for client_target in client_root.glob("index-*.js"):
            ok = patch_client(str(client_target)) and ok
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
