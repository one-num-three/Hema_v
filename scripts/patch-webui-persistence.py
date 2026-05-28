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
HEMA_APPS_SCRIPT_VERSION = "20260528-fast-launch2"
ENABLE_HEMA_APPS = True


HEMA_APPS_SCRIPT = r"""
(function () {
  try {
  const APPS_HASH = "#/hema/apps";
  const CHAT_HASH = "#/hermes/chat";
  const PROMPT_KEY = "hema.pendingAppPrompt";
  const MODE_KEY = "hema.activeAppMode";
  const SHUTDOWN_MODAL_ID = "hema-shutdown-modal";

  const apps = [
    {
      name: "??/??PPT",
      desc: "?? ppt-master skill??????????????????????",
      accent: "#2563eb",
      action: "ppt"
    },
    {
      name: "Nature ????",
      desc: "????????????????????? paper-to-PPT?",
      accent: "#0f766e",
      action: "nature"
    },
    {
      name: "PDF ??",
      desc: "?? minimax-pdf???????????? PDF ???",
      accent: "#dc2626",
      action: "minimax-pdf"
    },
    {
      name: "????",
      desc: "?? minimax-xlsx???????????? Excel ???",
      accent: "#ca8a04",
      action: "minimax-xlsx"
    },
    {
      name: "Word ??",
      desc: "?? minimax-docx???????????????? DOCX?",
      accent: "#9333ea",
      action: "minimax-docx"
    },
    { name: "????", desc: "?????????????", accent: "#334155" },
    { name: "????", desc: "???????????????", accent: "#16a34a" },
    { name: "????", desc: "?????????????", accent: "#ea580c" },
    { name: "????", desc: "????????????", accent: "#7c3aed" },
    { name: "?????", desc: "?????????????", accent: "#0891b2" },
    { name: "????", desc: "?????????????", accent: "#be123c" },
    { name: "????", desc: "????????????????", accent: "#64748b" }
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
    const modal = ensureShutdownModal();
    modal.classList.add("is-open");
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

  const minimaxApps = {
    "minimax-pdf": {
      name: "PDF 排版",
      skill: "minimax-pdf",
      intro: "适合创建新 PDF、填写已有 PDF 表单、把已有文档重排成更专业的可打印 PDF。",
      placeholder: "例如：把这份论文/报告重排成正式 PDF；或：生成一份 6 页项目建议书 PDF，含封面、目录、正文和附录。",
      rules: [
        "先判断模式：CREATE 从零生成、FILL 填写表单字段、REFORMAT 重排已有文档。",
        "CREATE/REFORMAT 时先建立 token 化设计系统：文档类型、封面风格、配色、字体、间距和页眉页脚。",
        "PDF 必须可打印、版心稳定、标题层级清楚、页码/目录/脚注/引用等正式文档元素完整。",
        "如果用户提供已有文件，先确认文件路径、目标风格、输出页数或是否保持原内容顺序。"
      ]
    },
    "minimax-xlsx": {
      name: "表格处理",
      skill: "minimax-xlsx",
      intro: "适合 Excel/CSV 读取分析、创建表格、编辑现有 xlsx、公式修复、格式化和验证。",
      placeholder: "例如：读取这个 Excel 并分析销售数据；或：帮我生成一份带公式、汇总页和专业格式的预算表。",
      rules: [
        "先判断模式：READ 分析、CREATE 新建、EDIT 零格式损失编辑、FIX 修公式、VALIDATE 校验公式。",
        "读取分析时不要修改源文件；编辑时尽量保留原有格式、工作表结构和公式。",
        "输出表格要有清晰表头、冻结窗格、数字格式、条件格式、汇总区和必要说明。",
        "涉及金额、百分比、日期、小数位时必须统一格式；公式要可重算并验证关键结果。"
      ]
    },
    "minimax-docx": {
      name: "Word 文档",
      skill: "minimax-docx",
      intro: "适合 Word/DOCX 文书、论文、作文、报告、公文、合同、模板套用和规范化排版。",
      placeholder: "例如：把这篇作文排成正式 Word；或：把报告套成公文格式；或：按论文规范生成 DOCX。",
      rules: [
        "先判断流水线：A 从零创建、B 填写/编辑现有文档、C 应用模板格式并做验证门控。",
        "正式文书要处理标题层级、正文样式、页边距、页眉页脚、页码、目录、表格、脚注和参考文献。",
        "中文文书/作文要注意段首缩进、行距、标点、中英文空格、数字单位、标题居中和版心整洁。",
        "公文/报告场景优先参考 GB/T 9704；学术场景按用户指定 APA/MLA/Chicago/Nature/学校模板执行。"
      ]
    }
  };

  function ensureMiniMaxModal() {
    let modal = document.querySelector(".hema-minimax-modal-mask");
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "hema-app-modal-mask hema-minimax-modal-mask";
    modal.innerHTML = `
      <div class="hema-app-modal" role="dialog" aria-modal="true" aria-label="文件应用">
        <h3></h3>
        <p class="hema-minimax-intro"></p>
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
      const config = minimaxApps[modal.dataset.kind] || minimaxApps["minimax-docx"];
      const need = modal.querySelector("textarea").value.trim();
      if (!need) {
        toast(`先写一点${config.name}需求，我再帮你带到聊天里。`);
        return;
      }
      const prompt = buildMiniMaxPrompt(config, need);
      setAppMode({ name: config.name, action: config.skill });
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

  function buildMiniMaxPrompt(config, need) {
    return [
      `【应用模式：${config.name}】`,
      `请使用 ${config.skill} skill 完成这个文件任务。`,
      "",
      "用户初始需求：",
      need,
      "",
      "能力定位：",
      config.intro,
      "",
      "执行规则：",
      ...config.rules.map((rule, index) => `${index + 1}. ${rule}`),
      `${config.rules.length + 1}. 如果缺少必要文件、模板、格式标准、输出路径或关键字段，请先追问，不要凭空假设。`,
      `${config.rules.length + 2}. 输出必须是真实文件路径，并说明生成/修改了哪些内容、用户下一步应检查什么。`,
      `${config.rules.length + 3}. 在正式生成前，先给出简短处理方案并等待用户确认；用户确认后再执行。`
    ].join("\\n");
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
    document.querySelector(".hema-minimax-modal-mask")?.classList.remove("is-open");
    const modal = ensureModal();
    modal.classList.add("is-open");
    setTimeout(() => modal.querySelector("textarea").focus(), 50);
  }

  function openNatureModal() {
    document.querySelector(".hema-ppt-modal-mask")?.classList.remove("is-open");
    document.querySelector(".hema-minimax-modal-mask")?.classList.remove("is-open");
    const modal = ensureNatureModal();
    modal.classList.add("is-open");
    setTimeout(() => modal.querySelector("textarea").focus(), 50);
  }

  function openMiniMaxModal(kind) {
    document.querySelector(".hema-ppt-modal-mask")?.classList.remove("is-open");
    document.querySelector(".hema-nature-modal-mask")?.classList.remove("is-open");
    const config = minimaxApps[kind] || minimaxApps["minimax-docx"];
    const modal = ensureMiniMaxModal();
    modal.dataset.kind = kind;
    modal.querySelector("h3").textContent = config.name;
    modal.querySelector(".hema-minimax-intro").textContent = config.intro;
    const textarea = modal.querySelector("textarea");
    textarea.value = "";
    textarea.setAttribute("placeholder", config.placeholder);
    modal.classList.add("is-open");
    setTimeout(() => textarea.focus(), 50);
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
    ensureMoreLink();
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

    if 'process.env.UPSTREAM?.trim()' in content and 'new URL(l)' in content and 'this.activeProfile||"default"' in content:
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
            'if(l&&(G||"default")===(this.activeProfile||"default"))try{let b=new URL(l),Z=parseInt(b.port,10)||8642,W=b.hostname||c;'
            'return{port:Z>0&&Z<=65535?Z:8642,host:W||c}}catch{}'
            'let b=(0,Ml.join)(this.profileDir(G),"config.yaml");if(!(0,yI.existsSync)(b))return{port:8642,host:c};'
            'try{let Z=(0,yI.readFileSync)(b,"utf-8"),W=(_I.load(Z)||{})?.platforms?.api_server?.extra,d=W?.port||8642,'
            'm=typeof d=="number"?d:parseInt(d,10)||8642,N=W?.host||c;return{port:m>0&&m<=65535?m:8642,host:N}}'
            'catch{return{port:8642,host:c}}}'
        )
        if old_gateway_port_logic not in content:
            print("ERROR: Could not find GatewayManager readProfilePort() call site")
            return False
        content = content.replace(old_gateway_port_logic, new_gateway_port_logic, 1)
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
