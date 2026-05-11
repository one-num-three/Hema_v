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
import sys


RELAY_LOGIN_URL = "https://ai.opcstore.com/login?expired=true"
OLD_RELAY_URLS = (
    "https://apikey.fun/register?aff=LIBAPI",
)
HEMA_APPS_SCRIPT_NAME = "hema-apps.js"
HEMA_APPS_SCRIPT_VERSION = "20260512-modal-scope1"
ENABLE_HEMA_APPS = True


HEMA_APPS_SCRIPT = r"""
(function () {
  try {
  const APPS_HASH = "#/hema/apps";
  const CHAT_HASH = "#/hermes/chat";
  const PROMPT_KEY = "hema.pendingAppPrompt";
  const MODE_KEY = "hema.activeAppMode";

  const apps = [
    {
      name: "制作/修改PPT",
      desc: "调用 ppt-master skill，强调叙事结构、设计系统和可编辑高质量页面。",
      accent: "#2563eb",
      action: "ppt"
    },
    {
      name: "Nature 科研套件",
      desc: "论文阅读、润色、引文、科研绘图、审稿回复和 paper-to-PPT。",
      accent: "#0f766e",
      action: "nature"
    },
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
      .hema-app-link{display:flex!important;align-items:center!important;gap:10px!important;width:100%!important;margin:0!important;padding:12px!important;border-radius:6px!important;color:var(--text-secondary)!important;text-decoration:none!important;font-size:14px!important;font-weight:400!important;line-height:1.6!important;box-sizing:border-box!important}
      .hema-app-link:hover{background-color:rgba(var(--accent-primary-rgb), .06)!important;color:var(--text-primary)!important}
      .hema-app-link.active{background-color:rgba(var(--accent-primary-rgb), .12)!important;color:var(--accent-primary)!important}
      .hema-app-link .nav-icon{width:18px;height:18px;display:inline-flex;align-items:center;justify-content:center;color:inherit;flex:0 0 18px}
      .hema-app-link svg{width:18px;height:18px;stroke-width:1.8}
      .hema-app-link .nav-label{line-height:1}
      .sidebar.collapsed .hema-app-link,.collapsed .hema-app-link{justify-content:center!important;gap:0!important;padding:10px 4px!important}
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
      .hema-nature-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:2px 0 14px}
      .hema-nature-option{border:1px solid #e5e7eb;border-radius:12px;background:#fafafa;color:#333;text-align:left;padding:9px 10px;cursor:pointer;transition:border-color .16s ease,background .16s ease,box-shadow .16s ease}
      .hema-nature-option strong{display:block;font-size:12px;font-weight:700;color:#202020;margin-bottom:2px}
      .hema-nature-option span{display:block;font-size:11px;color:#8b8b8b;line-height:1.35}
      .hema-nature-option.is-selected{border-color:#0f766e;background:rgba(15,118,110,.08);box-shadow:0 0 0 3px rgba(15,118,110,.08)}
      .hema-app-modal textarea{width:100%;height:148px;border:1px solid #ddd;border-radius:14px;padding:12px 14px;resize:vertical;font:14px/1.5 inherit;box-sizing:border-box;outline:none}
      .hema-app-modal textarea:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}
      .hema-app-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px}
      .hema-app-actions button{border:0;border-radius:12px;padding:10px 16px;font-size:14px;cursor:pointer}
      .hema-app-cancel{background:#f2f2f2;color:#444}
      .hema-app-send{background:#171717;color:#fff}
      .hema-app-toast{position:fixed;right:24px;bottom:24px;z-index:100;background:#171717;color:#fff;border-radius:12px;padding:10px 14px;font-size:13px;display:none}
      .hema-app-toast.is-open{display:block}
      .hema-app-mode-tag{display:flex;align-items:center;justify-content:space-between;gap:10px;width:max-content;max-width:100%;margin:0 0 8px;padding:6px 8px 6px 10px;border:1px solid rgba(37,99,235,.22);border-radius:999px;background:rgba(37,99,235,.08);color:#1f3f8f;font-size:12px;line-height:1.2}
      .hema-app-mode-tag strong{font-weight:650;color:#1d2d5f}
      .hema-app-mode-tag button{width:18px;height:18px;border:0;border-radius:999px;background:rgba(37,99,235,.12);color:#1f3f8f;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:14px;line-height:18px;padding:0}
      .hema-app-mode-tag button:hover{background:rgba(37,99,235,.2)}
      @media (max-width:1100px){.hema-apps-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hema-apps-shell{padding:30px 22px 44px}}
      @media (max-width:640px){.hema-apps-grid{grid-template-columns:1fr}.hema-app-card{height:236px}.hema-nature-options{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function icon() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>';
  }

  function ensureSidebarLink() {
    const relay = document.querySelector(".nav-item.fun-link");
    if (!relay) return;
    let link = document.querySelector(".hema-app-link");
    if (link && link.dataset.hemaAppsReady === "1") return;
    if (!link) {
      link = document.createElement("a");
      relay.insertAdjacentElement("afterend", link);
    }
    for (const attr of Array.from(relay.attributes)) {
      if (attr.name.startsWith("data-v-")) {
        link.setAttribute(attr.name, attr.value);
      }
    }
    link.className = "nav-item hema-app-link";
    link.href = APPS_HASH;
    link.innerHTML = `<span class="nav-icon">${icon()}</span><span class="nav-label">应用</span>`;
    const scopeAttr = Array.from(link.attributes).find((attr) => attr.name.startsWith("data-v-"));
    if (scopeAttr) {
      for (const child of link.querySelectorAll("span, svg")) {
        child.setAttribute(scopeAttr.name, scopeAttr.value);
      }
    }
    if (link.__hemaAppsClickBound) return;
    link.__hemaAppsClickBound = true;
    link.dataset.hemaAppsReady = "1";
    link.addEventListener("click", (event) => {
      event.preventDefault();
      window.location.hash = APPS_HASH;
      render();
    });
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
    const main = document.querySelector(".app-main");
    if (!main) return null;
    if (!view) {
      view = document.createElement("section");
      view.className = "hema-apps-view";
      view.innerHTML = `
        <div class="hema-apps-shell">
          <div class="hema-apps-kicker">Hema Apps</div>
          <h1 class="hema-apps-title">应用</h1>
          <p class="hema-apps-subtitle">把常用能力做成入口。先上线 PPT 和 Nature 科研套件，其它功能先占位，后面按真实工作流补齐。</p>
          <div class="hema-apps-grid">${apps.map(card).join("")}</div>
        </div>
      `;
    }
    if (view.parentElement !== main) main.appendChild(view);
    if (!view.__hemaAppsClickBound) {
      view.__hemaAppsClickBound = true;
      view.addEventListener("click", (event) => {
        const item = event.target.closest(".hema-app-card");
        if (!item) return;
        if (item.dataset.action === "ppt") openPptModal();
        else if (item.dataset.action === "nature") openNatureModal();
        else toast("这个应用还是占位，我们后面再一起定。");
      });
    }
    return view;
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
      const prompt = buildPptPrompt(need);
      setAppMode({ name: "制作/修改PPT", action: "ppt" });
      localStorage.setItem(PROMPT_KEY, prompt);
      modal.classList.remove("is-open");
      window.location.hash = CHAT_HASH;
      setTimeout(fillChatInput, 450);
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
      ["nature-data", "数据声明", "Data Availability/FAIR"],
      ["nature-response", "审稿回复", "逐点回复 reviewer"],
      ["nature-paper2ppt", "论文转PPT", "中文组会/汇报 PPTX"]
    ];
    modal = document.createElement("div");
    modal.className = "hema-app-modal-mask hema-nature-modal-mask";
    modal.innerHTML = `
      <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="Nature 科研套件">
        <h3>Nature 科研套件</h3>
        <p>先选一个方向，也可以保持“自动判断”。下面继续写你的通用需求，提交后会带着对应 nature-skills 提示打开聊天。</p>
        <div class="hema-nature-options" role="group" aria-label="选择科研任务方向">
          ${options.map(([value, title, desc], index) => `
            <button class="hema-nature-option ${index === 0 ? "is-selected" : ""}" type="button" data-skill="${value}">
              <strong>${title}</strong><span>${desc}</span>
            </button>
          `).join("")}
        </div>
        <textarea placeholder="例如：帮我把这篇论文整理成中文组会 PPT；或：帮我润色摘要并按 Nature 风格重构逻辑；或：帮我给这段引言补 CNS/Nature 引文。"></textarea>
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
      const prompt = buildNaturePrompt(need, skill, label);
      setAppMode({ name: label === "自动判断" ? "Nature 科研套件" : `Nature：${label}`, action: "nature", skill });
      localStorage.setItem(PROMPT_KEY, prompt);
      modal.classList.remove("is-open");
      window.location.hash = CHAT_HASH;
      setTimeout(fillChatInput, 450);
    });
    return modal;
  }

  function buildPptPrompt(need) {
    return [
      "【应用模式：制作/修改PPT】",
      "请使用 ppt-master skill 帮我完成一份高质量、可编辑、适合真实交付的 PPT。",
      "",
      "用户初始需求：",
      need,
      "",
      "任务判断：",
      "1. 先判断任务类型：新建 PPT、根据文档/资料生成 PPT、修改已有 PPT、润色/重构整份 PPT、论文/报告转汇报。",
      "2. 如果用户没有提供必要资料，请先追问：主题/用途、目标受众、页数范围、语言、使用场景、风格偏好、是否有品牌模板、是否需要演讲备注、是否已有文档或旧 PPT。",
      "3. 如果用户提供文档、网页、Markdown、PDF、Word、Excel 或旧 PPT，请优先把资料作为内容来源，不要凭空扩写关键事实。",
      "4. 如果是修改或润色旧 PPT，请先分析现有结构、叙事逻辑、视觉风格、信息密度和主要问题，再提出修改方案。",
      "",
      "质量目标：",
      "1. 不要做成普通 bullet list。每页必须有一个清晰 key message，并围绕它组织信息层级。",
      "2. 先建立整套 design spec：受众、叙事主线、页面节奏、色彩、字体、版式、图标、图片、图表和辅助元素规则。用户确认后再生成。",
      "3. 页面节奏要有变化：封面/章节页可作为 anchor，信息页可 dense，重点页要 breathing。不要每页都做成同一种卡片网格。",
      "4. 使用辅助性视觉元素，但必须服务理解，而不是纯装饰：章节进度条、页眉小标签、关键数字徽章、图标锚点、时间线、流程箭头、对比矩阵、注释 callout、数据来源脚注、图例、分割线、浅色背景块、局部高亮、微弱渐变、品牌纹理。",
      "5. 辅助元素要克制：同一页最多 1-2 个主要装饰手法；禁止堆叠无意义圆点、随机波浪、过多阴影、荧光色、满屏渐变和花哨贴纸。",
      "6. 能图示就不要只堆文字：流程用流程图，比较用矩阵，时间关系用 timeline，结构关系用层级/环形/中心辐射，数据用柱状/折线/瀑布/雷达等合适图表。",
      "7. 优先使用 ppt-master 内置能力：布局模板、charts_index 可视化模板、icons 图标库、spec_lock、svg_quality_checker 和 SVG-to-PPTX 导出流程。",
      "8. 字体、对齐、间距和留白要统一。正文密度高时减少装饰，重点页则用留白和大标题/大数字制造记忆点。",
      "9. 输出目标必须是可在 PowerPoint 中继续编辑的 .pptx：文字、形状、图标、图表尽量保持可编辑，不要把整页导成一张图片。",
      "10. 生成前先给出简短制作方案并等待用户确认，方案至少包含：页数建议、叙事结构、视觉方向、辅助元素策略、可能使用的图表/图标类型。",
      "11. 生成后必须做质量检查：是否跑版、文字是否溢出、对比度是否足够、每页 key message 是否明确、页面节奏是否重复、图表和注释是否可读。",
      "12. 完成后告诉用户输出文件路径，并提醒其打开检查；如果发现某页视觉弱，要主动建议可继续精修。"
    ].join("\\n");
  }

  function buildNaturePrompt(need, skill, label) {
    const skills = {
      "nature-reader": "把 PDF、DOI、arXiv、论文正文或网页论文整理成完整、双语、带图表位置和来源锚点的 Markdown 阅读稿。",
      "nature-polishing": "把中文或英文科研文本润色/重构为更接近 Nature 风格的学术英文，适合摘要、引言、结果、讨论、标题和方法。",
      "nature-citation": "为段落或稿件补充严格的 Nature/CNS/Cell 系列引用，并按可导入文献管理器的格式输出。",
      "nature-figure": "用 Python 或 R 制作、修改、审查高水平论文图，输出 SVG/PDF/TIFF 等投稿级结果。",
      "nature-data": "准备或审查 Data Availability、数据仓库、FAIR 元数据和数据引用。",
      "nature-response": "逐点撰写或修改审稿回复、修回信、rebuttal letter。",
      "nature-paper2ppt": "把科研论文、预印本、PDF、摘要、图注或阅读笔记生成中文学术汇报 PPTX。"
    };
    const selected = skill && skill !== "auto" ? `${skill}（${label}）：${skills[skill] || ""}` : "自动判断：请根据用户需求在下方 7 个 nature-* skill 中选择最合适的一个或多个。";
    const lines = [
      "【应用模式：Nature 科研套件】",
      `用户选择方向：${selected}`,
      "",
      "可用 skill 清单：",
      "- nature-reader：把 PDF、DOI、arXiv、论文正文或网页论文整理成完整、双语、带图表位置和来源锚点的 Markdown 阅读稿。",
      "- nature-polishing：把中文或英文科研文本润色/重构为更接近 Nature 风格的学术英文，适合摘要、引言、结果、讨论、标题和方法。",
      "- nature-citation：为段落或稿件补充严格的 Nature/CNS/Cell 系列引用，并按可导入文献管理器的格式输出。",
      "- nature-figure：用 Python 或 R 制作、修改、审查高水平论文图，输出 SVG/PDF/TIFF 等投稿级结果。",
      "- nature-data：准备或审查 Data Availability、数据仓库、FAIR 元数据和数据引用。",
      "- nature-response：逐点撰写或修改审稿回复、修回信、rebuttal letter。",
      "- nature-paper2ppt：把科研论文、预印本、PDF、摘要、图注或阅读笔记生成中文学术汇报 PPTX。",
      "",
      "用户初始需求：",
      need,
      "",
      "执行规则：",
      "1. 先判断任务类型，并选择对应的 nature-* skill；如果一个任务需要多个 skill，请说明顺序。",
      "2. 如果缺少必要材料，先追问，不要假装已经读过论文或数据。常见必需材料包括 PDF/DOI/链接/正文、目标期刊、图表数据、审稿意见、旧稿或旧 PPT。",
      "3. 如果用户要生成文件，最终产物必须是真实文件路径，例如 .md、.pptx、.svg、.pdf、.tiff、.ris 或 .enw，而不是只给大纲。",
      "4. 如果涉及论文事实、引用或图表结论，必须基于用户提供材料或可验证来源，不要编造。",
      "5. 在正式执行前，先给出简短工作方案并等待用户确认；用户确认后再调用对应 skill 工作流。",
      "6. 完成后用中文说明输出文件、主要改动和用户下一步该检查什么。"
    ];
    if (skill && skill !== "auto") {
      lines.push("", `优先约束：除非用户需求明显不匹配，否则优先使用 ${skill}；如果需要额外 skill，请先说明为什么。`);
    }
    return lines.join("\\n");
  }

  function getAppMode() {
    try {
      return JSON.parse(localStorage.getItem(MODE_KEY) || "null");
    } catch {
      return null;
    }
  }

  function setAppMode(mode) {
    if (!mode) localStorage.removeItem(MODE_KEY);
    else localStorage.setItem(MODE_KEY, JSON.stringify(mode));
    ensureAppModeTag();
  }

  function ensureAppModeTag() {
    const existing = document.querySelector(".hema-app-mode-tag");
    const mode = getAppMode();
    if (!mode) {
      existing && existing.remove();
      return;
    }
    const inputArea = document.querySelector(".chat-input-area");
    if (!inputArea) return;
    let tag = existing;
    if (!tag) {
      tag = document.createElement("div");
      tag.className = "hema-app-mode-tag";
      tag.innerHTML = '<span>应用：<strong></strong></span><button type="button" title="退出应用模式" aria-label="退出应用模式">×</button>';
      tag.querySelector("button").addEventListener("click", () => {
        setAppMode(null);
        localStorage.removeItem(PROMPT_KEY);
        toast("已退出应用模式。");
      });
    }
    tag.querySelector("strong").textContent = mode.name || "应用";
    if (tag.parentElement !== inputArea) inputArea.insertBefore(tag, inputArea.firstChild);
  }

  function openPptModal() {
    document.querySelector(".hema-nature-modal-mask")?.classList.remove("is-open");
    const modal = ensureModal();
    modal.classList.add("is-open");
    setTimeout(() => modal.querySelector("textarea").focus(), 50);
  }

  function openNatureModal() {
    document.querySelector(".hema-ppt-modal-mask")?.classList.remove("is-open");
    const modal = ensureNatureModal();
    modal.classList.add("is-open");
    setTimeout(() => modal.querySelector("textarea").focus(), 50);
  }

  function fillChatInput() {
    const prompt = localStorage.getItem(PROMPT_KEY);
    if (!prompt) return;
    const input = findChatInput();
    if (!input) {
      navigator.clipboard && navigator.clipboard.writeText(prompt).catch(() => {});
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
    ensureAppModeTag();
    const open = window.location.hash === APPS_HASH;
    if (!open) {
      closeAppsView();
      if (window.location.hash === CHAT_HASH) setTimeout(fillChatInput, 300);
      return;
    }
    const view = ensureView();
    if (!view) return;
    view.classList.toggle("is-open", open);
    document.querySelector(".hema-app-link")?.classList.toggle("active", open);
  }

  function closeAppsView() {
    document.querySelector(".hema-apps-view")?.classList.remove("is-open");
    document.querySelector(".hema-app-link")?.classList.remove("active");
  }

  function renderSoon() {
    window.requestAnimationFrame(() => {
      try {
        render();
      } catch (error) {
        console.warn("Hema apps render skipped:", error);
        closeAppsView();
      }
    });
  }

  const observer = new MutationObserver(() => ensureSidebarLink());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("click", (event) => {
    const link = event.target && event.target.closest ? event.target.closest("a") : null;
    if (link && !link.classList.contains("hema-app-link")) {
      closeAppsView();
      setTimeout(renderSoon, 0);
    }
  }, true);
  window.addEventListener("hashchange", renderSoon);
  window.addEventListener("load", renderSoon);
  setInterval(renderSoon, 1200);
  try {
    renderSoon();
  } catch (error) {
    console.warn("Hema apps patch disabled after error:", error);
    closeAppsView();
  }
  } catch (error) {
    console.warn("Hema apps patch failed to initialize:", error);
  }
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
    script_tag = (
        '<script id="hema-apps-loader">'
        '(function(){function load(){'
        'if(document.getElementById("hema-apps-runtime"))return;'
        'var s=document.createElement("script");'
        's.id="hema-apps-runtime";s.defer=true;'
        f's.src="/{HEMA_APPS_SCRIPT_NAME}?v={HEMA_APPS_SCRIPT_VERSION}";'
        's.onerror=function(){console.warn("Hema apps failed to load")};'
        'document.body.appendChild(s)}'
        'if(document.readyState==="complete")setTimeout(load,800);'
        'else window.addEventListener("load",function(){setTimeout(load,800)},{once:true});'
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
