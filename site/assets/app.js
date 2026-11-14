/* Interactive project site. Plain JS, no dependencies, no network calls after load. */
(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const svgEl = (name, attrs = {}) => {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
  };
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d));

  let DATA = null;
  let QINDEX = null;

  async function load() {
    const response = await fetch("assets/data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`data.json: ${response.status}`);
    DATA = await response.json();
    QINDEX = new Map(DATA.label.quarters.map((q, i) => [q, i]));
    return DATA;
  }

  /* ---------------------------------------------------------------- charts */
  function frame(container, height, margins = {}) {
    container.innerHTML = "";
    const width = 960;
    const m = { top: 18, right: 18, bottom: 34, left: 52, ...margins };
    const svg = svgEl("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": container.dataset.label || "chart",
    });
    container.appendChild(svg);
    return { svg, width, height, m, innerW: width - m.left - m.right, innerH: height - m.top - m.bottom };
  }

  function axes(svg, f, xTicks, yTicks, xFormat, yFormat) {
    const { m, innerW, innerH } = f;
    const g = svgEl("g");
    for (const [value, label] of xTicks) {
      const x = m.left + value * innerW;
      g.appendChild(svgEl("line", { x1: x, x2: x, y1: m.top, y2: m.top + innerH, stroke: "#e6ebf1", "stroke-width": 1 }));
      const t = svgEl("text", { x, y: m.top + innerH + 18, "text-anchor": "middle", "font-size": 11, fill: "#6b7788" });
      t.textContent = label;
      g.appendChild(t);
    }
    for (const [value, label] of yTicks) {
      const y = m.top + innerH - value * innerH;
      g.appendChild(svgEl("line", { x1: m.left, x2: m.left + innerW, y1: y, y2: y, stroke: "#e6ebf1", "stroke-width": 1 }));
      const t = svgEl("text", { x: m.left - 10, y: y + 3.5, "text-anchor": "end", "font-size": 11, fill: "#6b7788" });
      t.textContent = label;
      g.appendChild(t);
    }
    g.appendChild(svgEl("line", { x1: m.left, x2: m.left + innerW, y1: m.top + innerH, y2: m.top + innerH, stroke: "#b9c4d2" }));
    svg.appendChild(g);
  }

  function recessionBands(svg, f, opts = {}) {
    const { m, innerH, innerW } = f;
    const step = innerW / (DATA.label.quarters.length - 1);
    let start = null;
    const bands = [];
    DATA.label.R.forEach((flag, i) => {
      if (flag === 1 && start === null) start = i;
      if (flag !== 1 && start !== null) { bands.push([start, i - 1]); start = null; }
    });
    if (start !== null) bands.push([start, DATA.label.quarters.length - 1]);
    for (const [a, b] of bands) {
      svg.appendChild(svgEl("rect", {
        x: m.left + a * step - step / 2,
        y: m.top,
        width: (b - a + 1) * step,
        height: innerH,
        fill: opts.fill || "rgba(166,61,47,.09)",
      }));
    }
  }

  function linePath(values, f, yMin, yMax) {
    const { m, innerW, innerH } = f;
    const n = values.length;
    let d = "";
    let open = false;
    values.forEach((v, i) => {
      if (v === null || v === undefined || Number.isNaN(v)) { open = false; return; }
      const x = m.left + (i / (n - 1)) * innerW;
      const y = m.top + innerH - ((v - yMin) / (yMax - yMin || 1)) * innerH;
      d += `${open ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)} `;
      open = true;
    });
    return d;
  }

  function yExtent(values) {
    const nums = values.filter((v) => v !== null && v !== undefined && Number.isFinite(v));
    const lo = Math.min(...nums), hi = Math.max(...nums);
    const pad = (hi - lo) * 0.08 || 0.5;
    return [lo - pad, hi + pad];
  }

  function tickLabels(maxIndex, count = 7) {
    const ticks = [];
    for (let i = 0; i < count; i++) {
      const idx = Math.round((i / (count - 1)) * (DATA.label.quarters.length - 1));
      ticks.push([idx / (DATA.label.quarters.length - 1), DATA.label.quarters[idx]]);
    }
    return ticks;
  }

  function drawLabelChart(container) {
    if (!container) return;
    const f = frame(container, 380);
    recessionBands(f.svg, f);
    const values = DATA.label.level;
    const [lo, hi] = yExtent(values);
    axes(f.svg, f, tickLabels(), [
      [0, lo.toFixed(1)], [0.5, ((lo + hi) / 2).toFixed(1)], [1, hi.toFixed(1)],
    ]);
    f.svg.appendChild(svgEl("path", {
      d: linePath(values, f, lo, hi), fill: "none", stroke: "#0b6e75", "stroke-width": 2.4,
      "stroke-linejoin": "round", "stroke-linecap": "round",
    }));
    // episode markers
    DATA.label.episodes.forEach((ep) => {
      for (const [q, kind] of [[ep.peak, "peak"], [ep.trough, "trough"]]) {
        const idx = QINDEX.get(q);
        if (idx === undefined) continue;
        const x = f.m.left + (idx / (values.length - 1)) * f.innerW;
        const v = values[idx];
        const y = f.m.top + f.innerH - ((v - lo) / (hi - lo || 1)) * f.innerH;
        f.svg.appendChild(svgEl("circle", { cx: x, cy: y, r: 4, fill: kind === "peak" ? "#a63d2f" : "#2b6cb0", stroke: "#fff", "stroke-width": 1.5 }));
      }
    });
    // hover layer
    const step = f.innerW / (values.length - 1);
    const tip = svgEl("g", { opacity: 0 });
    const tipBg = svgEl("rect", { width: 150, height: 44, rx: 6, fill: "#12233f" });
    const tipText = svgEl("text", { x: 10, y: 18, "font-size": 11, fill: "#fff" });
    const tipText2 = svgEl("text", { x: 10, y: 33, "font-size": 11, fill: "#c9d6e8" });
    tip.append(tipBg, tipText, tipText2);
    f.svg.appendChild(tip);
    values.forEach((v, i) => {
      const rect = svgEl("rect", { x: f.m.left + i * step - step / 2, y: f.m.top, width: step, height: f.innerH, fill: "transparent" });
      rect.addEventListener("mouseenter", () => {
        const x = f.m.left + (i / (values.length - 1)) * f.innerW;
        const y = f.m.top + f.innerH - ((v - lo) / (hi - lo || 1)) * f.innerH;
        tip.setAttribute("opacity", 1);
        tip.setAttribute("transform", `translate(${Math.min(x + 8, f.width - 165)},${Math.max(y - 52, 4)})`);
        tipText.textContent = DATA.label.quarters[i];
        tipText2.textContent = `level ${fmt(v)} · R=${DATA.label.R[i]}`;
      });
      rect.addEventListener("mouseleave", () => tip.setAttribute("opacity", 0));
      f.svg.appendChild(rect);
    });
  }

  function drawDiffusionChart(container) {
    if (!container) return;
    const f = frame(container, 230, { top: 14 });
    const values = DATA.label.diffusion;
    const [lo, hi] = yExtent(values);
    axes(f.svg, f, tickLabels(6), [
      [0, lo.toFixed(1)], [0.5, ((lo + hi) / 2).toFixed(1)], [1, hi.toFixed(1)],
    ]);
    const gate = 0.5;
    const y = f.m.top + f.innerH - ((gate - lo) / (hi - lo || 1)) * f.innerH;
    f.svg.appendChild(svgEl("line", { x1: f.m.left, x2: f.m.left + f.innerW, y1: y, y2: y, stroke: "#b7791f", "stroke-dasharray": "5 4", "stroke-width": 1.4 }));
    f.svg.appendChild(svgEl("text", { x: f.m.left + f.innerW, y: y - 6, "text-anchor": "end", "font-size": 10, fill: "#7a5212" })).textContent = "diffusion gate 0.50";
    f.svg.appendChild(svgEl("path", { d: linePath(values, f, lo, hi), fill: "none", stroke: "#2b6cb0", "stroke-width": 1.8 }));
  }

  /* ------------------------------------------------------------ feature explorer */
  let featureIndex = 0;

  function populateFeatureControls() {
    const select = $("#feature-select");
    if (!select) return;
    const groups = {};
    DATA.features.names.forEach((name, i) => {
      const g = DATA.features.groups[name];
      (groups[g] ||= []).push([name, i]);
    });
    select.innerHTML = "";
    for (const [group, items] of Object.entries(groups)) {
      const optgroup = document.createElement("optgroup");
      optgroup.label = group;
      for (const [name, i] of items) {
        const option = document.createElement("option");
        option.value = String(i);
        option.textContent = name;
        optgroup.appendChild(option);
      }
      select.appendChild(optgroup);
    }
    featureIndex = DATA.features.names.findIndex((n) => n === "beai_copy_ACT_IP__qoq_growth");
    if (featureIndex < 0) featureIndex = 0;
    select.value = String(featureIndex);
    select.addEventListener("change", () => { featureIndex = Number(select.value); drawFeatureChart(); });
    $("#feature-random")?.addEventListener("click", () => {
      featureIndex = Math.floor(Math.random() * DATA.features.names.length);
      select.value = String(featureIndex);
      drawFeatureChart();
    });
  }

  function drawFeatureChart() {
    const container = $("#feature-chart");
    if (!container) return;
    const name = DATA.features.names[featureIndex];
    const values = DATA.features.values.map((row) => row[featureIndex]);
    const f = frame(container, 330);
    recessionBands(f.svg, f);
    const [lo, hi] = yExtent(values);
    axes(f.svg, f, tickLabels(7), [[0, lo.toFixed(2)], [1, hi.toFixed(2)]]);
    f.svg.appendChild(svgEl("path", { d: linePath(values, f, lo, hi), fill: "none", stroke: "#0b6e75", "stroke-width": 2 }));
    f.svg.appendChild(svgEl("line", {
      x1: f.m.left, x2: f.m.left + f.innerW,
      y1: f.m.top + f.innerH - ((0 - lo) / (hi - lo || 1)) * f.innerH,
      y2: f.m.top + f.innerH - ((0 - lo) / (hi - lo || 1)) * f.innerH,
      stroke: "#9aa7b6", "stroke-dasharray": "3 4", "stroke-width": 1,
    }));
    const nums = values.filter((v) => v !== null && Number.isFinite(v));
    const mean = nums.reduce((a, b) => a + b, 0) / nums.length;
    const variance = nums.reduce((a, b) => a + (b - mean) ** 2, 0) / nums.length;
    $("#feature-name").textContent = name;
    $("#feature-group").textContent = DATA.features.groups[name];
    $("#feature-stats").innerHTML = `
      <div><span class="muted">mean</span><strong>${fmt(mean, 3)}</strong></div>
      <div><span class="muted">std</span><strong>${fmt(Math.sqrt(variance), 3)}</strong></div>
      <div><span class="muted">missing</span><strong>${values.length - nums.length}</strong> / ${values.length}</div>
      <div><span class="muted">min / max</span><strong>${fmt(Math.min(...nums), 2)} / ${fmt(Math.max(...nums), 2)}</strong></div>`;
  }

  /* ------------------------------------------------------------ fold explorer */
  function drawFoldExplorer() {
    const container = $("#fold-chart");
    if (!container) return;
    const horizon = $("#fold-horizon")?.value || "2";
    const folds = DATA.folds.blocks[horizon];
    const f = frame(container, 470, { left: 58, right: 24, bottom: 30 });
    const n = DATA.label.quarters.length;
    const rowH = f.innerH / folds.length;
    // year grid
    const years = [];
    DATA.label.quarters.forEach((q, i) => { if (q.endsWith("Q1") && Number(q.slice(0, 4)) % 5 === 0) years.push([i / (n - 1), q.slice(0, 4)]); });
    axes(f.svg, f, years, []);
    folds.forEach((fold, i) => {
      const y = f.m.top + i * rowH;
      const trainEnd = QINDEX.get(fold.train_end);
      const testStart = QINDEX.get(fold.test_start);
      const testEnd = QINDEX.get(fold.test_end);
      f.svg.appendChild(svgEl("rect", {
        x: f.m.left, y, width: ((trainEnd + 1) / n) * f.innerW, height: Math.max(rowH - 1.2, 2.2),
        fill: "rgba(11,110,117,.16)",
      }));
      f.svg.appendChild(svgEl("rect", {
        x: f.m.left + (testStart / n) * f.innerW,
        y, width: Math.max(((testEnd - testStart + 1) / n) * f.innerW, 3), height: Math.max(rowH - 1.2, 2.2),
        fill: "#a63d2f",
      }));
    });
    f.svg.appendChild(svgEl("text", { x: f.m.left, y: f.m.top - 5, "font-size": 10, fill: "#5d6b80" })).textContent = "each row = one outer fold · teal = train · rust = test";
    const primary = DATA.folds.blocks["2"].length;
    const note = $("#fold-note");
    if (note) {
      note.innerHTML = `${folds.length} outer folds at <strong>${horizon}Q</strong> horizon. ` +
        `First test quarter <strong>${folds[0].test_start}</strong>, last <strong>${folds[folds.length - 1].test_end}</strong>. ` +
        `Purge equals the horizon before every test block.`;
    }
  }

  /* ------------------------------------------------------------ baselines */
  function drawBaselineChart() {
    const container = $("#baseline-chart");
    if (!container) return;
    const horizons = ["1Q", "2Q", "4Q"];
    const models = [
      ["majority", "Majority", "#9aa7b6"],
      ["term_spread", "Yield slope", "#0b6e75"],
      ["plain_logistic", "Plain logistic", "#b7791f"],
    ];
    const f = frame(container, 300, { top: 24, bottom: 46 });
    const max = Math.max(...DATA.baselines.map((r) => r.pr_auc || 0)) * 1.15;
    axes(f.svg, f, horizons.map((h, i) => [(i + 0.5) / 3, h]), [
      [0, "0"], [0.5, (max / 2).toFixed(2)], [1, max.toFixed(2)],
    ]);
    const groupW = f.innerW / 3;
    horizons.forEach((h, gi) => {
      models.forEach(([key, label, color], mi) => {
        const row = DATA.baselines.find((r) => r.horizon === h && r.model === key);
        const value = row?.pr_auc || 0;
        const barH = (value / max) * f.innerH;
        const x = f.m.left + gi * groupW + groupW * 0.18 + mi * (groupW * 0.22);
        const y = f.m.top + f.innerH - barH;
        f.svg.appendChild(svgEl("rect", { x, y, width: groupW * 0.18, height: barH, fill: color, rx: 3 }));
        const t = svgEl("text", { x: x + groupW * 0.09, y: y - 5, "text-anchor": "middle", "font-size": 10, fill: "#34435a" });
        t.textContent = value.toFixed(3);
        f.svg.appendChild(t);
      });
    });
    const legend = $("#baseline-legend");
    if (legend) {
      legend.innerHTML = models.map(([, label, color]) => `<span><i class="sw box" style="background:${color}"></i>${label}</span>`).join("");
    }
  }

  function fillBaselineTable() {
    const body = $("#baseline-body");
    if (!body) return;
    body.innerHTML = DATA.baselines.map((row) => `
      <tr class="${row.is_primary ? "hl" : ""}">
        <td>${row.horizon}${row.is_primary ? " · primary" : ""}</td>
        <td>${row.model}</td>
        <td>${fmt(row.pr_auc, 4)}</td>
        <td>${fmt(row.roc_auc, 4)}</td>
        <td>${fmt(row.episode_recall, 4)}</td>
        <td>${fmt(row.brier, 4)}</td>
        <td>${row.n_test_obs}</td>
      </tr>`).join("");
  }

  /* ------------------------------------------------------------ firewall demo */
  const CHECKS = [
    ["schema", "Schema", "147 contiguous quarters and 149 unique columns"],
    ["blacklist", "Blacklist", "No label, factor, chronology, episode or identifier column"],
    ["unscaled", "Unscaled", "No standardised column; rate levels equal the source"],
    ["future", "No future leakage", "Truncated-history rebuild leaves every past value identical"],
    ["independence", "Independence", "Every BEAI copy is reproducible from the panel alone"],
    ["mutation", "Mutation", "A poisoned table must fail the same checks"],
  ];

  function renderDemo(state) {
    const list = $("#demo-checks");
    const code = $("#demo-code");
    if (!list || !code) return;
    const status = Object.fromEntries(CHECKS.map(([key]) => [key, true]));
    let message = "validate_feature_table(table) → OK";
    if (state === "label") {
      status.blacklist = false; status.mutation = false;
      message = "ValueError: forbidden columns present: ['R']";
    } else if (state === "factor") {
      status.blacklist = false; status.mutation = false;
      message = "ValueError: forbidden columns present: ['factor']";
    } else if (state === "shift") {
      status.future = false; status.mutation = false;
      message = "AssertionError: future leakage at 2019Q4: max diff 4.63";
    } else if (state === "level") {
      status.unscaled = false;
      message = "ValueError: FIN_CREDIT_GDP__level looks like a raw level, not a change";
    }
    list.innerHTML = CHECKS.map(([key, title, text]) => `
      <li class="${status[key] ? "" : "fail"}">
        <i class="dot"></i>
        <div><strong>${title} ${status[key] ? "PASS" : "FAIL"}</strong><span>${text}</span></div>
      </li>`).join("");
    code.innerHTML = `<span class="cmd">$ python -m pytest tests/test_feature_firewall.py</span>\n` +
      (state === "clean"
        ? `<span class="ok">7 passed</span>  ·  full table accepted`
        : `<span class="bad">1 failed</span>  ·  ${message.replaceAll("<", "&lt;")}`);
  }

  function initDemo() {
    if (!$("#demo-checks")) return;
    $$("#demo-controls button").forEach((button) => {
      button.addEventListener("click", () => {
        $$("#demo-controls button").forEach((b) => b.classList.remove("active"));
        button.classList.add("active");
        renderDemo(button.dataset.state);
      });
    });
    renderDemo("clean");
  }

  /* ------------------------------------------------------------ page setup */
  function fillMeta() {
    $$("[data-count='features']").forEach((n) => (n.textContent = DATA.meta.counts.features));
    $$("[data-count='series']").forEach((n) => (n.textContent = DATA.meta.counts.series));
    $$("[data-count='beai']").forEach((n) => (n.textContent = DATA.meta.counts.beai_copy_columns));
    $$("[data-count='folds']").forEach((n) => (n.textContent = DATA.meta.counts.outer_folds_per_horizon));
    $$("[data-hash='table']").forEach((n) => (n.textContent = DATA.meta.hashes["dataset.parquet"].slice(0, 12) + "…"));
    $$("[data-hash='folds']").forEach((n) => (n.textContent = DATA.meta.hashes["folds.json"].slice(0, 12) + "…"));
    $$("[data-hash='label']").forEach((n) => (n.textContent = DATA.meta.hashes["USA_labels.csv"].slice(0, 12) + "…"));
    $$("[data-generated]").forEach((n) => (n.textContent = DATA.meta.generated));
  }

  async function init() {
    try {
      await load();
    } catch (error) {
      console.error(error);
      $$(".chart").forEach((n) => (n.textContent = "Data bundle not found. Run: python scripts/09_build_site.py"));
      return;
    }
    fillMeta();
    const page = document.body.dataset.page;
    if (page === "overview" || page === "methodology" || page === "results") drawLabelChart($("#label-chart"));
    if (page === "methodology") {
      drawDiffusionChart($("#diffusion-chart"));
      drawFoldExplorer();
      $("#fold-horizon")?.addEventListener("change", drawFoldExplorer);
    }
    if (page === "firewall") {
      populateFeatureControls();
      drawFeatureChart();
      initDemo();
    }
    if (page === "results") {
      drawBaselineChart();
      fillBaselineTable();
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
