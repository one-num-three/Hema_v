(function () {
  try {
    const APPS_HASH = "#/hema/apps";
    const CHAT_HASH = "#/hermes/chat";
    const PROMPT_KEY = "hema.pendingAppPrompt";
    const MODE_KEY = "hema.activeAppMode";
    const SHUTDOWN_MODAL_ID = "hema-shutdown-modal";
    const THEME_KEY = "hema.theme";

    const apps = [
      { name: "制作/修改PPT", desc: "调用 ppt-master skill，强调叙事结构、设计系统和可编辑高质量页面。", accent: "#2563eb", action: "ppt", image: "/hema-app-backgrounds/ppt.png" },
      { name: "Nature 科研套件", desc: "论文阅读、润色、引文、科研绘图、审稿回复和 paper-to-PPT。", accent: "#0f766e", action: "nature", image: "/hema-app-backgrounds/nature.png" },
      { name: "PDF 排版", desc: "调用 minimax-pdf，创建、填写或重排可打印 PDF 文档。", accent: "#dc2626", action: "minimax-pdf", image: "/hema-app-backgrounds/pdf.png" },
      { name: "表格处理", desc: "调用 minimax-xlsx，读取、分析、编辑和验证 Excel 表格。", accent: "#ca8a04", action: "minimax-xlsx", image: "/hema-app-backgrounds/excel.png" },
      { name: "Word 文档", desc: "调用 minimax-docx，创建、编辑、套模板和规范化排版 DOCX。", accent: "#9333ea", action: "minimax-docx", image: "/hema-app-backgrounds/word.png" },
      { name: "代码助手", desc: "解释、修改和排查代码问题。", accent: "#334155", action: "placeholder", image: "/hema-app-backgrounds/code.png" },
      { name: "工作计划", desc: "把目标拆成任务清单和执行顺序。", accent: "#16a34a", action: "placeholder", image: "/hema-app-backgrounds/plan.png" },
      { name: "日报周报", desc: "根据素材生成简洁汇报文本。", accent: "#ea580c", action: "placeholder", image: "/hema-app-backgrounds/weekly_report.png" },
      { name: "合同检查", desc: "提取风险点和待确认条款。", accent: "#7c3aed", action: "placeholder", image: "/hema-app-backgrounds/contract.png" },
      { name: "知识库问答", desc: "围绕已有资料做检索和问答。", accent: "#0891b2", action: "placeholder", image: "/hema-app-backgrounds/learning_ans.png" },
      { name: "邮件润色", desc: "改写语气、结构和表达方式。", accent: "#be123c", action: "placeholder", image: "/hema-app-backgrounds/email.png" },
      { name: "更多应用", desc: "占位功能，后续按你的业务继续补。", accent: "#64748b", action: "placeholder", image: "/hema-app-backgrounds/more.png" }
    ];

    const minimaxApps = {
      "minimax-pdf": {
        title: "PDF 排版",
        intro: "适合创建新 PDF、填写已有 PDF 表单、或把已有文档重排成更专业的可打印 PDF。",
        placeholder: "例如：把这份报告重排成正式 PDF；或生成一份带封面、目录和附录的项目建议书 PDF。",
        lines: [
          "先判断模式：CREATE 从零生成、FILL 填写表单、REFORMAT 重排已有文档。",
          "保持正式文档结构完整：封面、目录、页码、页眉页脚、表格、脚注和引用。",
          "输出结果要适合打印，版心稳定，层级清楚。"
        ]
      },
      "minimax-xlsx": {
        title: "表格处理",
        intro: "适合读取分析、创建表格、编辑现有 xlsx、修公式和做结果校验。",
        placeholder: "例如：读取这个 Excel 并分析销售数据；或生成一份带公式和汇总页的预算表。",
        lines: [
          "先判断模式：READ 分析、CREATE 新建、EDIT 编辑、FIX 修公式、VALIDATE 校验。",
          "尽量保留原有格式、工作表结构和公式。",
          "结果表格要有清晰表头、数字格式、汇总区和必要说明。"
        ]
      },
      "minimax-docx": {
        title: "Word 文档",
        intro: "适合 Word/DOCX 文书、论文、报告、公文、模板套用和规范化排版。",
        placeholder: "例如：把这份报告排成正式 Word；或按学校论文模板生成 DOCX。",
        lines: [
          "先判断流水线：新建、编辑现有文档、或应用模板格式。",
          "处理标题层级、页边距、页眉页脚、页码、目录、表格和参考文献。",
          "正式文书优先保证版式规范、结构清楚、可直接交付。"
        ]
      }
    };

    function ensureStyle() {
      if (document.getElementById("hema-apps-style")) return;
      const style = document.createElement("style");
      style.id = "hema-apps-style";
      style.textContent = `
        .hema-app-link,.hema-more-link{display:flex!important;align-items:center!important;gap:10px!important;width:100%!important;margin:0!important;padding:12px!important;border-radius:8px!important;color:var(--text-secondary)!important;text-decoration:none!important;font-size:14px!important;font-weight:400!important;line-height:1.6!important;box-sizing:border-box!important;background:transparent!important;border:0!important;outline:none!important;box-shadow:none!important;appearance:none!important;-webkit-appearance:none!important;font-family:inherit!important;text-align:left!important}
        .hema-app-link:hover,.hema-more-link:hover{background-color:rgba(var(--accent-primary-rgb), .06)!important;color:var(--text-primary)!important}
        .hema-app-link.active,.hema-more-link.active{background-color:rgba(var(--accent-primary-rgb), .12)!important;color:var(--accent-primary)!important}
        .hema-app-link .nav-icon,.hema-more-link .nav-icon{width:18px;height:18px;display:inline-flex;align-items:center;justify-content:center;color:inherit;flex:0 0 18px}
        .hema-more-link:focus,.hema-more-link:focus-visible{outline:none!important;box-shadow:none!important}
        html:not(.dark) aside .profile-selector .n-base-selection-label,
        html:not(.dark) aside .status-row .n-base-selection-label,
        html:not(.dark) aside .model-trigger,
        html:not(.dark) aside .n-select .n-base-selection-label{background:#fff!important;color:#1f2937!important;border-color:rgba(148,163,184,.28)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.82)!important}
        html:not(.dark) aside .profile-selector .n-base-selection-input,
        html:not(.dark) aside .profile-selector .n-base-selection-input__content,
        html:not(.dark) aside .status-row .n-base-selection-input,
        html:not(.dark) aside .status-row .n-base-selection-input__content,
        html:not(.dark) aside .n-select .n-base-selection-input,
        html:not(.dark) aside .n-select .n-base-selection-input__content{color:#374151!important}
        html:not(.dark) aside .n-base-selection .n-base-suffix,
        html:not(.dark) aside .model-trigger svg{color:#64748b!important}
        .hema-apps-view{position:fixed;top:16px;right:16px;bottom:16px;left:296px;background:
          radial-gradient(circle at 12% 0%, rgba(59,130,246,.10), transparent 24%),
          radial-gradient(circle at 88% 8%, rgba(20,184,166,.08), transparent 20%),
          linear-gradient(180deg,#f8fafc 0%,#eef4fb 46%,#e8eef7 100%);
          padding:34px 32px 28px;overflow:auto;z-index:40;display:none;border:1px solid rgba(148,163,184,.20);
          border-radius:28px;box-shadow:0 24px 70px rgba(15,23,42,.12), inset 0 1px 0 rgba(255,255,255,.72)}
        .dark .hema-apps-view{background:
          radial-gradient(circle at 12% 0%, rgba(59,130,246,.14), transparent 24%),
          radial-gradient(circle at 88% 8%, rgba(20,184,166,.12), transparent 20%),
          linear-gradient(180deg,#12141d 0%,#101521 46%,#0d1627 100%);
          border-color:rgba(96,165,250,.10);box-shadow:0 30px 90px rgba(2,6,23,.42), inset 0 1px 0 rgba(255,255,255,.04)}
        .hema-apps-view.is-open{display:block}
        .hema-apps-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:28px}
        .hema-apps-title{font-size:34px;font-weight:800;letter-spacing:-.05em;color:#10233a}
        .dark .hema-apps-title{color:#f8fafc}
        .hema-apps-sub{margin-top:10px;color:#51657e;font-size:14px;line-height:1.9;max-width:820px}
        .dark .hema-apps-sub{color:rgba(226,232,240,.82)}
        .hema-app-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px}
        .hema-app-card{position:relative;border:1px solid rgba(148,163,184,.24);border-radius:28px;padding:0;background:linear-gradient(180deg,rgba(255,255,255,.94),rgba(248,250,252,.98));box-shadow:0 18px 46px rgba(15,23,42,.10), inset 0 1px 0 rgba(255,255,255,.78);cursor:pointer;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;overflow:hidden;text-align:left;min-height:320px}
        .dark .hema-app-card{border-color:var(--hema-accent-soft,rgba(255,255,255,.12));background:linear-gradient(180deg,rgba(15,23,42,.92),rgba(10,15,26,.98));box-shadow:0 22px 54px rgba(2,6,23,.36), inset 0 1px 0 rgba(255,255,255,.04)}
        .hema-app-card:hover{transform:translateY(-4px);box-shadow:0 24px 56px rgba(15,23,42,.14), 0 0 0 1px var(--hema-accent-glow,rgba(255,255,255,.06));border-color:var(--hema-accent-line,rgba(255,255,255,.2))}
        .dark .hema-app-card:hover{box-shadow:0 28px 70px rgba(2,6,23,.48), 0 0 0 1px var(--hema-accent-glow,rgba(255,255,255,.06))}
        .hema-app-card:before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:linear-gradient(180deg,var(--hema-accent-line,#60a5fa),transparent 82%);opacity:.95}
        .hema-app-poster{position:relative;height:192px;background:var(--hema-poster-bg);background-size:115% auto;background-position:center;border-bottom:1px solid rgba(255,255,255,.06);overflow:hidden}
        .hema-app-poster:before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,.02),transparent 58%,rgba(2,6,23,.18) 100%)}
        .hema-app-poster:after{content:"";position:absolute;inset:0;border:1px solid rgba(255,255,255,.10);pointer-events:none}
        .dark .hema-app-poster:before{background:linear-gradient(180deg,rgba(2,6,23,.28),rgba(2,6,23,.34) 58%,rgba(2,6,23,.52) 100%)}
        .hema-app-poster-badge{position:absolute;top:16px;left:16px;display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;background:rgba(15,23,42,.46);border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(10px);color:#e2e8f0;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;z-index:1}
        .hema-app-dot{width:10px;height:10px;border-radius:999px;box-shadow:0 0 0 6px rgba(255,255,255,.08)}
        .hema-app-poster-mark{position:absolute;right:18px;bottom:16px;font-size:42px;font-weight:800;letter-spacing:-.06em;color:rgba(255,255,255,.18);z-index:1}
        .hema-app-body{padding:18px 18px 20px}
        .hema-app-card h3{margin:0;color:#10233a;font-size:17px;font-weight:800;letter-spacing:-.03em}
        .dark .hema-app-card h3{color:#f8fafc}
        .hema-app-card p{margin:10px 0 0;color:#5f7188;font-size:13px;line-height:1.75;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
        .dark .hema-app-card p{color:rgba(226,232,240,.70)}
        .hema-apps-kicker{font-size:12px;font-weight:700;letter-spacing:.20em;text-transform:uppercase;color:#4d78ad}
        .dark .hema-apps-kicker{color:#7aa2d8}
        .hema-app-modal-mask,.hema-shutdown-modal-mask{position:fixed;inset:0;background:rgba(15,23,42,.42);backdrop-filter:blur(6px);display:none;align-items:center;justify-content:center;z-index:9998;padding:16px}
        .hema-app-modal-mask.is-open,.hema-shutdown-modal-mask.is-open{display:flex}
        .hema-app-modal,.hema-shutdown-modal{width:min(720px,calc(100vw - 32px));background:var(--bg-card);border-radius:24px;padding:24px;border:1px solid rgba(var(--accent-primary-rgb),.12);box-shadow:0 28px 80px rgba(15,23,42,.24)}
        .hema-app-modal h3,.hema-shutdown-title{margin:0 0 10px;color:var(--text-primary);font-size:24px;font-weight:800}
        .hema-app-modal p,.hema-shutdown-text{margin:0;color:var(--text-secondary);font-size:14px;line-height:1.8}
        .hema-app-modal textarea{width:100%;min-height:132px;margin-top:16px;border-radius:16px;border:1px solid var(--border-color);background:var(--bg-input);color:var(--text-primary);padding:14px 16px;font:inherit;box-sizing:border-box;resize:vertical}
        .hema-app-actions,.hema-shutdown-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:18px}
        .hema-app-send,.hema-shutdown-confirm,.hema-app-cancel,.hema-shutdown-cancel{border:0;border-radius:999px;padding:11px 18px;font:inherit;cursor:pointer}
        .hema-app-send,.hema-shutdown-confirm{background:var(--accent-primary);color:var(--text-on-accent)}
        .hema-app-cancel,.hema-shutdown-cancel{background:rgba(var(--accent-primary-rgb), .08);color:var(--text-primary)}
        .hema-nature-options{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:16px}
        .hema-nature-option{border:1px solid rgba(var(--accent-primary-rgb),.12);background:var(--bg-secondary);border-radius:14px;padding:12px;text-align:left;cursor:pointer;color:var(--text-primary)}
        .hema-nature-option strong{display:block;font-size:14px}
        .hema-nature-option span{display:block;margin-top:4px;font-size:12px;color:var(--text-secondary);line-height:1.5}
        .hema-nature-option.is-selected{border-color:rgba(var(--accent-primary-rgb),.32);background:rgba(var(--accent-primary-rgb), .08)}
        .hema-minimax-lines{margin:14px 0 0;padding-left:18px;color:var(--text-secondary);font-size:13px;line-height:1.7}
        .hema-minimax-lines li+li{margin-top:6px}
        .hema-app-toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(14px);background:rgba(15,23,42,.92);color:#fff;border-radius:999px;padding:10px 16px;font-size:13px;opacity:0;pointer-events:none;transition:all .18s ease;z-index:10000}
        .hema-app-toast.is-open{opacity:1;transform:translateX(-50%) translateY(0)}
        .hema-mode-tag{display:inline-flex;align-items:center;gap:8px;margin-right:8px;padding:6px 8px 6px 10px;border-radius:999px;background:rgba(var(--accent-primary-rgb), .08);color:var(--text-primary);font-size:12px}
        .hema-mode-tag strong{font-weight:700}
        .hema-mode-tag-close{width:20px;height:20px;border:0;border-radius:999px;background:rgba(var(--accent-primary-rgb), .10);color:var(--text-secondary);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:13px;line-height:1;padding:0}
        .hema-mode-tag-close:hover{background:rgba(var(--accent-primary-rgb), .16);color:var(--text-primary)}
        .hema-theme-toggle{position:fixed;right:28px;bottom:128px;width:40px;height:40px;border:1px solid rgba(148,163,184,.20);border-radius:999px;background:rgba(255,255,255,.72);box-shadow:0 10px 24px rgba(15,23,42,.12), inset 0 1px 0 rgba(255,255,255,.68);backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2147483647;transition:transform .18s ease,background .18s ease,border-color .18s ease,box-shadow .18s ease}
        .hema-theme-toggle:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(15,23,42,.16), inset 0 1px 0 rgba(255,255,255,.70)}
        .hema-theme-toggle:focus-visible{outline:3px solid rgba(37,99,235,.42);outline-offset:3px}
        .hema-theme-moon{position:relative;width:22px;height:22px;border-radius:999px;background:#111827;box-shadow:inset -7px 0 0 #f8fafc}
        .hema-theme-moon:before{content:"";position:absolute;left:4px;top:5px;width:3px;height:3px;border-radius:999px;background:#f8fafc;box-shadow:7px 8px 0 -1px #f8fafc}
        .dark .hema-theme-toggle,.hema-theme-toggle.is-dark{background:rgba(15,23,42,.58);border-color:rgba(148,163,184,.22);box-shadow:0 10px 24px rgba(2,6,23,.28), inset 0 1px 0 rgba(255,255,255,.08)}
        .dark .hema-theme-moon,.hema-theme-toggle.is-dark .hema-theme-moon{background:#f8fafc;box-shadow:inset -7px 0 0 #111827}
        .dark .hema-theme-moon:before,.hema-theme-toggle.is-dark .hema-theme-moon:before{background:#111827;box-shadow:7px 8px 0 -1px #111827}
        .hema-shutdown-kicker{font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--text-muted);text-transform:uppercase}
        .hema-shutdown-card{margin-top:16px;padding:16px;border-radius:18px;background:rgba(220,38,38,.06);border:1px solid rgba(220,38,38,.12)}
        .hema-shutdown-card-title{font-size:16px;font-weight:700;color:var(--text-primary)}
        .hema-shutdown-hint{margin-top:6px;font-size:13px;color:var(--text-secondary)}
        .hema-exit-overlay{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(15,23,42,.45);backdrop-filter:blur(6px);z-index:9999}
        .hema-exit-card{width:min(420px,calc(100vw - 32px));padding:24px;border-radius:22px;background:var(--bg-card);text-align:center;box-shadow:0 28px 80px rgba(15,23,42,.24)}
        .hema-exit-spinner{width:42px;height:42px;margin:0 auto 14px;border-radius:999px;border:3px solid rgba(var(--accent-primary-rgb),.14);border-top-color:var(--accent-primary);animation:hema-spin .8s linear infinite}
        .hema-exit-title{font-size:20px;font-weight:800;color:var(--text-primary)}
        .hema-exit-text{margin-top:8px;font-size:13px;line-height:1.7;color:var(--text-secondary)}
        @keyframes hema-spin{to{transform:rotate(360deg)}}
        @media (max-width: 980px){
          .hema-apps-view{left:88px;top:10px;right:10px;bottom:10px;padding:24px 18px 20px;border-radius:22px}
          .hema-app-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
          .hema-app-poster{height:170px}
        }
        @media (max-width: 1440px){
          .hema-app-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
        }
        @media (max-width: 720px){
          .hema-app-grid{grid-template-columns:minmax(0,1fr)}
        }
      `;
      document.head.appendChild(style);
    }

    function getAppMode() {
      try {
        return JSON.parse(localStorage.getItem(MODE_KEY) || "null");
      } catch {
        return null;
      }
    }

    function setAppMode(value) {
      if (!value) {
        localStorage.removeItem(MODE_KEY);
        return;
      }
      localStorage.setItem(MODE_KEY, JSON.stringify(value));
    }

    function currentTheme() {
      const saved = localStorage.getItem(THEME_KEY) || localStorage.getItem("theme") || localStorage.getItem("vueuse-color-scheme");
      if (saved === "dark" || saved === "light") return saved;
      if (document.documentElement.classList.contains("dark") || document.body.classList.contains("dark")) return "dark";
      return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
    }

    function applyTheme(theme) {
      const next = theme === "dark" ? "dark" : "light";
      const root = document.documentElement;
      const body = document.body;
      root.classList.toggle("dark", next === "dark");
      body?.classList.toggle("dark", next === "dark");
      root.classList.remove("light");
      body?.classList.remove("light");
      if (next === "dark") {
        root.dataset.theme = "dark";
        if (body) body.dataset.theme = "dark";
      } else {
        delete root.dataset.theme;
        if (body) delete body.dataset.theme;
      }
      localStorage.setItem(THEME_KEY, next);
      localStorage.setItem("theme", next);
      localStorage.setItem("vueuse-color-scheme", next);
      const button = document.querySelector(".hema-theme-toggle");
      if (button) {
        button.classList.toggle("is-dark", next === "dark");
        button.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
        button.title = next === "dark" ? "切换到亮色模式" : "切换到暗色模式";
      }
    }

    function ensureThemeToggle() {
      let button = document.querySelector(".hema-theme-toggle");
      if (!button) {
        button = document.createElement("button");
        button.type = "button";
        button.className = "hema-theme-toggle";
        button.setAttribute("aria-label", "切换亮色和暗色模式");
        button.innerHTML = '<span class="hema-theme-moon" aria-hidden="true"></span>';
        button.addEventListener("click", () => {
          applyTheme(currentTheme() === "dark" ? "light" : "dark");
        });
        document.body.appendChild(button);
      }
      applyTheme(currentTheme());
    }

    function getPosterBackground(accent, index) {
      const palettes = [
        `radial-gradient(circle at 18% 18%, rgba(255,255,255,.18), transparent 18%), linear-gradient(135deg, ${accent} 0%, rgba(15,23,42,.92) 54%, rgba(2,6,23,.98) 100%)`,
        `radial-gradient(circle at 76% 22%, rgba(255,255,255,.16), transparent 20%), linear-gradient(145deg, rgba(15,23,42,.72) 0%, ${accent} 38%, rgba(3,7,18,.98) 100%)`,
        `linear-gradient(155deg, rgba(2,6,23,.92) 0%, ${accent} 34%, rgba(30,41,59,.96) 100%), radial-gradient(circle at 82% 84%, rgba(255,255,255,.12), transparent 16%)`,
        `radial-gradient(circle at 20% 80%, rgba(255,255,255,.12), transparent 18%), linear-gradient(135deg, rgba(15,23,42,.78) 0%, ${accent} 42%, rgba(2,6,23,.98) 100%)`
      ];
      return palettes[index % palettes.length];
    }

    function getPosterMark(name) {
      return (String(name || "").trim().charAt(0) || "A").toUpperCase();
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
      node._timer = setTimeout(() => node.classList.remove("is-open"), 2400);
    }

    function buildPrompt(prefix, need, lines) {
      return [
        prefix,
        "",
        "我的具体需求：",
        need,
        "",
        "执行要求：",
        ...lines.map((line, index) => `${index + 1}. ${line}`)
      ].join("\n");
    }

    function buildPptPrompt(need) {
      return buildPrompt(
        "请以 ppt-master 模式处理这次任务，优先保证可编辑、结构清楚、页面质量高。",
        need,
        [
          "先判断这是从零制作还是修改现有 PPT。",
          "明确目标受众、页数、风格、主叙事和每页重点。",
          "输出时优先保证逻辑、版式、标题层级和视觉统一。"
        ]
      );
    }

    function buildNaturePrompt(need, skill, label) {
      const head = skill === "auto"
        ? "请用 Nature 科研套件模式处理这次任务，并先判断最适合的子 skill。"
        : `请优先按 Nature 科研套件中的「${label}」模式处理这次任务。`;
      return buildPrompt(head, need, [
        "先判断输入素材是否完整，不完整就先列出缺失项。",
        "输出要偏正式、科研风格、结构化。",
        "如果适合产出 PPT、文档、图表或回复稿，请主动给出最合适的交付形式。"
      ]);
    }

    function buildMiniMaxPrompt(kind, need) {
      const config = minimaxApps[kind] || minimaxApps["minimax-docx"];
      return buildPrompt(`请使用 ${config.title} 工作流处理这次任务。`, need, config.lines);
    }

    function findChatInput() {
      const candidates = Array.from(document.querySelectorAll("textarea, input, [contenteditable='true']"));
      return candidates.find((node) => {
        if (node.closest(".hema-app-modal-mask")) return false;
        if (node.offsetParent === null && node.getClientRects().length === 0) return false;
        if (node.tagName === "INPUT") {
          const type = (node.getAttribute("type") || "text").toLowerCase();
          if (!["text", "search"].includes(type)) return false;
        }
        return true;
      }) || null;
    }

    function fillChatInput() {
      const prompt = localStorage.getItem(PROMPT_KEY);
      if (!prompt) return;
      const input = findChatInput();
      if (!input) {
        navigator.clipboard?.writeText(prompt).catch(() => {});
        toast("已复制应用提示词，请粘贴到聊天框。");
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
      ensureAppModeTag();
      toast("应用需求已填入聊天框，确认后发送即可。");
    }

    function ensureView() {
      let view = document.querySelector(".hema-apps-view");
      if (view) return view;
      const host = document.body;
      view = document.createElement("section");
      view.className = "hema-apps-view";
      view.innerHTML = `
        <div class="hema-apps-head">
          <div>
            <div class="hema-apps-kicker">Apps Workspace</div>
            <div class="hema-apps-title">应用</div>
            <div class="hema-apps-sub">把常见任务收成快捷入口。点开后我会帮你补全更明确的提示词，再带回聊天继续执行；适合直接做 PPT、科研、PDF、表格和 Word 工作流。</div>
          </div>
        </div>
        <div class="hema-app-grid"></div>
      `;
      host.appendChild(view);
      const grid = view.querySelector(".hema-app-grid");
      apps.forEach((app, index) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "hema-app-card";
        card.style.setProperty("--hema-accent-line", app.accent);
        card.style.setProperty("--hema-accent-soft", `${app.accent}55`);
        card.style.setProperty("--hema-accent-glow", `${app.accent}33`);
        card.style.setProperty("--hema-poster-bg", app.image ? `url("${app.image}")` : getPosterBackground(app.accent, index));
        card.innerHTML = `
          <div class="hema-app-poster">
            <div class="hema-app-poster-badge"><span class="hema-app-dot" style="background:${app.accent}"></span><span>APP ${String(index + 1).padStart(2, "0")}</span></div>
            ${app.image ? "" : `<div class="hema-app-poster-mark">${getPosterMark(app.name)}</div>`}
          </div>
          <div class="hema-app-body">
            <h3>${app.name}</h3>
            <p>${app.desc}</p>
          </div>
        `;
        card.addEventListener("click", () => {
          if (app.action === "ppt") {
            ensureModal().classList.add("is-open");
          } else if (app.action === "nature") {
            ensureNatureModal().classList.add("is-open");
          } else if (minimaxApps[app.action]) {
            openMiniMaxModal(app.action);
          } else {
            toast("这个应用还是占位，我们后面再一起定。");
          }
        });
        grid.appendChild(card);
      });
      return view;
    }

    function findSidebarItem(pattern) {
      return Array.from(document.querySelectorAll("a, button")).find((node) => {
        const text = (node.textContent || "").trim();
        return text && pattern.test(text);
      }) || null;
    }

    function getSidebarList() {
      const relay = findSidebarItem(/中转站|API relay|Relay/i);
      const more = document.querySelector(".hema-more-link") || findSidebarItem(/更多|More/i);
      const basis = relay || more || document.querySelector("aside");
      return basis?.parentElement || basis?.closest("nav") || document.querySelector("aside") || null;
    }

    function placeSidebarEntry(entry, anchorPattern, placeAfter) {
      const list = getSidebarList();
      if (!list || !entry) return;
      const anchor = findSidebarItem(anchorPattern);
      const anchorRow = anchor?.closest("a,button,li,div") || anchor?.parentElement || null;
      if (anchorRow && anchorRow.parentElement === list) {
        if (placeAfter) {
          if (anchorRow.nextSibling !== entry) list.insertBefore(entry, anchorRow.nextSibling);
        } else if (anchorRow !== entry.previousSibling) {
          list.insertBefore(entry, anchorRow);
        }
        return;
      }
      list.appendChild(entry);
    }

    function ensureSidebarLink() {
      let link = document.querySelector(".hema-app-link");
      if (!link) {
        link = document.createElement("a");
        link.href = APPS_HASH;
        link.className = "hema-app-link";
        link.innerHTML = `<span class="nav-icon">◫</span><span>应用</span>`;
      }
      placeSidebarEntry(link, /中转站|API relay|Relay/i, true);
    }

    function ensureMoreLink() {
      let link = document.querySelector(".hema-more-link");
      if (!link) {
        link = document.createElement("button");
        link.type = "button";
        link.className = "hema-more-link";
        link.innerHTML = `<span class="nav-icon">•••</span><span>更多</span>`;
        link.addEventListener("click", openShutdownModal);
      }
      placeSidebarEntry(link, /应用|Apps/i, true);
    }

    function ensureModal() {
      let modal = document.querySelector(".hema-ppt-modal-mask");
      if (modal) return modal;
      modal = document.createElement("div");
      modal.className = "hema-app-modal-mask hema-ppt-modal-mask";
      modal.innerHTML = `
        <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="制作或修改PPT">
          <h3>制作/修改PPT</h3>
          <p>告诉我主题、用途、页数、风格、是否已有素材。提交后会带着更严格的 ppt-master 设计提示打开聊天。</p>
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
        localStorage.setItem(PROMPT_KEY, buildPptPrompt(need));
        setAppMode({ name: "制作/修改PPT", action: "ppt" });
        modal.classList.remove("is-open");
        location.hash = CHAT_HASH;
        setTimeout(fillChatInput, 420);
      });
      return modal;
    }

    function ensureNatureModal() {
      let modal = document.querySelector(".hema-nature-modal-mask");
      if (modal) return modal;
      const options = [
        ["auto", "自动判断", "让 Hermes 选择合适 skill"],
        ["nature-reader", "论文阅读", "PDF/DOI/全文转阅读稿"],
        ["nature-polishing", "学术润色", "Nature 风格英文重构"],
        ["nature-citation", "补充引文", "CNS/Nature/Cell 引用"],
        ["nature-figure", "科研绘图", "Python/R 投稿级图表"],
        ["nature-response", "审稿回复", "逐点回复 reviewer"],
        ["nature-paper2ppt", "论文转PPT", "中文组会或汇报 PPTX"]
      ];
      modal = document.createElement("div");
      modal.className = "hema-app-modal-mask hema-nature-modal-mask";
      modal.innerHTML = `
        <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="Nature 科研套件">
          <h3>Nature 科研套件</h3>
          <p>先选一个方向，也可以保持自动判断。提交后会带着更适合的科研工作流打开聊天。</p>
          <div class="hema-nature-options">
            ${options.map(([value, title, desc], index) => `
              <button class="hema-nature-option ${index === 0 ? "is-selected" : ""}" type="button" data-skill="${value}">
                <strong>${title}</strong><span>${desc}</span>
              </button>
            `).join("")}
          </div>
          <textarea placeholder="例如：帮我把这篇论文整理成中文组会 PPT；或：帮我润色摘要并按 Nature 风格重构逻辑。"></textarea>
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
      modal.querySelectorAll(".hema-nature-option").forEach((button) => {
        button.addEventListener("click", () => {
          modal.querySelectorAll(".hema-nature-option").forEach((node) => node.classList.remove("is-selected"));
          button.classList.add("is-selected");
        });
      });
      modal.querySelector(".hema-app-send").addEventListener("click", () => {
        const need = modal.querySelector("textarea").value.trim();
        if (!need) {
          toast("先写一点科研需求，我再帮你带到聊天里。");
          return;
        }
        const selected = modal.querySelector(".hema-nature-option.is-selected");
        const skill = selected?.dataset.skill || "auto";
        const label = selected?.querySelector("strong")?.textContent || "自动判断";
        localStorage.setItem(PROMPT_KEY, buildNaturePrompt(need, skill, label));
        setAppMode({ name: label === "自动判断" ? "Nature 科研套件" : `Nature：${label}`, action: "nature", skill });
        modal.classList.remove("is-open");
        location.hash = CHAT_HASH;
        setTimeout(fillChatInput, 420);
      });
      return modal;
    }

    function ensureMiniMaxModal() {
      let modal = document.querySelector(".hema-minimax-modal-mask");
      if (modal) return modal;
      modal = document.createElement("div");
      modal.className = "hema-app-modal-mask hema-minimax-modal-mask";
      modal.innerHTML = `
        <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="文档处理">
          <h3></h3>
          <p class="hema-minimax-intro"></p>
          <ul class="hema-minimax-lines"></ul>
          <textarea></textarea>
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
        const kind = modal.dataset.kind || "minimax-docx";
        const need = modal.querySelector("textarea").value.trim();
        if (!need) {
          toast("先写一点需求，我再帮你带到聊天里。");
          return;
        }
        const title = minimaxApps[kind]?.title || "文档处理";
        localStorage.setItem(PROMPT_KEY, buildMiniMaxPrompt(kind, need));
        setAppMode({ name: title, action: kind });
        modal.classList.remove("is-open");
        location.hash = CHAT_HASH;
        setTimeout(fillChatInput, 420);
      });
      return modal;
    }

    function openMiniMaxModal(kind) {
      const config = minimaxApps[kind] || minimaxApps["minimax-docx"];
      const modal = ensureMiniMaxModal();
      modal.dataset.kind = kind;
      modal.querySelector("h3").textContent = config.title;
      modal.querySelector(".hema-minimax-intro").textContent = config.intro;
      modal.querySelector(".hema-minimax-lines").innerHTML = config.lines.map((line) => `<li>${line}</li>`).join("");
      const textarea = modal.querySelector("textarea");
      textarea.value = "";
      textarea.placeholder = config.placeholder;
      modal.classList.add("is-open");
      setTimeout(() => textarea.focus(), 60);
    }

    function ensureShutdownModal() {
      let modal = document.getElementById(SHUTDOWN_MODAL_ID);
      if (modal) return modal;
      modal = document.createElement("div");
      modal.id = SHUTDOWN_MODAL_ID;
      modal.className = "hema-shutdown-modal-mask";
      modal.innerHTML = `
        <div class="hema-shutdown-modal" role="dialog" aria-modal="true" aria-label="更多">
          <div class="hema-shutdown-kicker">More</div>
          <div class="hema-shutdown-title">完全退出</div>
          <div class="hema-shutdown-text">关闭当前 Web 管理界面，同时停止 Web UI 和网关。这个操作更适合你确定这次会话已经结束的时候使用。</div>
          <div class="hema-shutdown-card">
            <div class="hema-shutdown-card-title">完全退出并关闭网关</div>
            <div class="hema-shutdown-hint">你将无法在微信上和河马对话哦</div>
          </div>
          <div class="hema-shutdown-actions">
            <button class="hema-shutdown-cancel" type="button">取消</button>
            <button class="hema-shutdown-confirm" type="button">完全退出</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
      modal.querySelector(".hema-shutdown-cancel").addEventListener("click", () => modal.classList.remove("is-open"));
      modal.addEventListener("click", (event) => {
        if (event.target === modal) modal.classList.remove("is-open");
      });
      modal.querySelector(".hema-shutdown-confirm").addEventListener("click", () => {
        requestFullShutdown(modal);
      });
      return modal;
    }

    function openShutdownModal() {
      ensureShutdownModal().classList.add("is-open");
    }

    function showExitOverlay() {
      let overlay = document.querySelector(".hema-exit-overlay");
      if (overlay) return overlay;
      overlay = document.createElement("div");
      overlay.className = "hema-exit-overlay";
      overlay.innerHTML = `
        <div class="hema-exit-card">
          <div class="hema-exit-spinner" aria-hidden="true"></div>
          <div class="hema-exit-title">正在完全退出</div>
          <div class="hema-exit-text">Web 管理界面和网关正在关闭。稍后你可以重新通过快捷方式启动。</div>
        </div>
      `;
      document.body.appendChild(overlay);
      return overlay;
    }

    async function requestFullShutdown(modal) {
      const button = modal?.querySelector(".hema-shutdown-confirm");
      if (button?.dataset.busy === "1") return;
      if (button) {
        button.dataset.busy = "1";
        button.disabled = true;
        button.textContent = "正在退出…";
      }
      try {
        const res = await fetch("/__hema/shutdown-all", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        if (!res.ok) {
          let message = `退出失败（${res.status}）`;
          try {
            const data = await res.json();
            if (data?.error) message = data.error;
          } catch {}
          throw new Error(message);
        }
        modal?.classList.remove("is-open");
        showExitOverlay();
        setTimeout(() => {
          try { window.open("", "_self"); } catch {}
          try { window.close(); } catch {}
        }, 700);
        setTimeout(() => {
          try { window.location.replace("about:blank"); } catch {}
        }, 1800);
      } catch (error) {
        toast(error?.message || "完全退出失败，请稍后再试。");
        if (button) {
          button.dataset.busy = "0";
          button.disabled = false;
          button.textContent = "完全退出";
        }
      }
    }

    function ensureAppModeTag() {
      const inputWrap = findChatInput()?.closest("form, .input-wrapper, .chat-input-area, .message-input") || document.querySelector(".chat-input-area, form");
      if (!inputWrap) return;
      let tag = inputWrap.querySelector(".hema-mode-tag");
      tag?.remove();
      const mode = getAppMode();
      if (!mode?.name) return;
      tag = document.createElement("div");
      tag.className = "hema-mode-tag";
      tag.innerHTML = `<span>当前应用</span><strong>${mode.name}</strong><button class="hema-mode-tag-close" type="button" aria-label="关闭应用模式" title="关闭应用模式">×</button>`;
      tag.querySelector(".hema-mode-tag-close")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setAppMode(null);
        localStorage.removeItem(PROMPT_KEY);
        ensureAppModeTag();
        toast("已退出应用模式。");
      });
      inputWrap.prepend(tag);
    }

    function closeAppsView() {
      document.querySelector(".hema-apps-view")?.classList.remove("is-open");
      document.querySelector(".hema-app-link")?.classList.remove("active");
    }

    function updateViewFrame() {
      const view = document.querySelector(".hema-apps-view");
      if (!view) return;
      const aside = document.querySelector("aside");
      if (!aside) return;
      const rect = aside.getBoundingClientRect();
      const left = Math.max(88, Math.round(rect.right + 14));
      view.style.left = `${left}px`;
    }

    function pruneSidebarFooter() {
      const aside = document.querySelector("aside");
      if (!aside) return;
      const hidePattern = /(退出登录|logout|abmelden|升级版本|update to v|aktualisieren auf v|web ui v|changelog|变更日志|github)/i;
      const keepPattern = /(已连接|未连接|connected|disconnected|verbunden|getrennt|中文|english|theme|hell|dark|system|亮|暗)/i;
      const nodes = Array.from(aside.querySelectorAll("a, button, div, span"));
      for (const node of nodes) {
        if (node.closest(".hema-app-link, .hema-more-link")) continue;
        const text = (node.textContent || "").replace(/\s+/g, " ").trim();
        if (!text) continue;
        if (keepPattern.test(text)) continue;
        if (!hidePattern.test(text)) continue;
        const row = node.closest("a, button, .n-button, .n-base-selection, .n-select, .n-space, .n-flex, div");
        const target = row || node;
        if (target instanceof HTMLElement) {
          target.style.display = "none";
        }
      }
    }

    function render() {
      ensureStyle();
      ensureSidebarLink();
      ensureMoreLink();
      ensureAppModeTag();
      ensureThemeToggle();
      updateViewFrame();
      pruneSidebarFooter();
      const open = location.hash === APPS_HASH;
      if (!open) {
        closeAppsView();
        if (location.hash === CHAT_HASH) setTimeout(fillChatInput, 260);
        return;
      }
      const view = ensureView();
      view.classList.add("is-open");
      document.querySelector(".hema-app-link")?.classList.add("active");
    }

    let renderQueued = false;

    function renderSoon() {
      if (renderQueued) return;
      renderQueued = true;
      requestAnimationFrame(() => {
        renderQueued = false;
        try {
          render();
        } catch (error) {
          console.warn("Hema apps render skipped:", error);
          closeAppsView();
        }
      });
    }

    document.addEventListener("click", (event) => {
      const target = event.target?.closest ? event.target.closest("a, button") : null;
      if (!target) return;
      if (target.closest(".hema-apps-view")) return;
      if (target.closest(".hema-app-modal-mask, .hema-shutdown-modal-mask")) return;
      if (target.classList.contains("hema-app-link")) return;
      closeAppsView();
      setTimeout(renderSoon, 0);
    }, true);

    window.addEventListener("hashchange", renderSoon);
    window.addEventListener("load", renderSoon);
    window.addEventListener("resize", renderSoon);
    setInterval(() => {
      ensureSidebarLink();
      ensureMoreLink();
      ensureAppModeTag();
      ensureThemeToggle();
      updateViewFrame();
      pruneSidebarFooter();
    }, 2500);
    renderSoon();
  } catch (error) {
    console.warn("Hema apps patch failed to initialize:", error);
  }
})();
