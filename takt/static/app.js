(() => {
  "use strict";
  const CFG = Object.assign({ priceSingle: 490, pricePack: 1490, packSize: 5, minTarget: 20, maxTarget: 600,
    maxUploadMb: 25, retentionDays: 7, rebuilds: 3 }, window.TAKT || {});
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* приватный режим */ } },
    del(k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } },
  };
  const DEVICE = store.get("takt_dev") || (() => {
    const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
    store.set("takt_dev", id);
    return id;
  })();

  // ---------- утилиты ----------
  const pad = (n) => String(n).padStart(2, "0");
  function fmt(sec) {
    sec = Math.max(0, sec || 0);
    const m = Math.floor(sec / 60), s = Math.floor(sec % 60);
    return `${m}:${pad(s)}`;
  }
  function fmtPrecise(sec) {
    const m = Math.floor(sec / 60), s = sec - m * 60;
    const whole = Math.floor(s), tenth = Math.round((s - whole) * 10);
    if (tenth === 10) return fmtPrecise(Math.round(sec));
    return `${m}:${pad(whole)},${tenth}`;
  }
  function parseTime(v) {
    v = String(v || "").trim().replace(",", ".");
    const m = v.match(/^(\d{1,2})\s*[:.]\s*(\d{1,2}(?:\.\d+)?)$/);
    if (m) {
      const s = parseFloat(m[2]);
      if (s >= 60) return NaN;
      return parseInt(m[1], 10) * 60 + s;
    }
    if (/^\d+(\.\d+)?$/.test(v)) return parseFloat(v);
    return NaN;
  }
  function plural(n, one, few, many) {
    const a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b > 1 && b < 5) return few;
    if (b === 1) return one;
    return many;
  }
  const rub = (n) => `${Number(n).toLocaleString("ru-RU")} ₽`;
  const pct = (x) => `${x > 0 ? "+" : ""}${x.toFixed(1).replace(".", ",")} %`;
  function el(tag, attrs = {}, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v);
    }
    for (const k of kids) if (k != null) e.append(k);
    return e;
  }
  function track(name, props = {}, jobId = null) {
    try {
      fetch("/api/events", { method: "POST", keepalive: true,
        headers: { "Content-Type": "application/json", "X-Device": DEVICE },
        body: JSON.stringify({ name, props, job_id: jobId || (state.job && state.job.id) || null }) });
      if (window.ym && window.METRIKA_ID) window.ym(window.METRIKA_ID, "reachGoal", name, props);
    } catch (e) { /* аналитика не должна ломать сайт */ }
  }
  function goal(name, props = {}) {
    try { if (window.ym && window.METRIKA_ID) window.ym(window.METRIKA_ID, "reachGoal", name, props); } catch (e) { /* ignore */ }
  }
  async function api(path, opts = {}) {
    const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json", "X-Device": DEVICE } }, opts));
    let data = null;
    try { data = await res.json(); } catch (e) { /* пустой ответ */ }
    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || `Ошибка ${res.status}. Попробуйте ещё раз.`;
      const err = new Error(typeof msg === "string" ? msg : "Ошибка запроса");
      err.status = res.status;
      throw err;
    }
    return data;
  }
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // ---------- состояние ----------
  const state = { file: null, fileDuration: null, ending: "natural", job: null, token: null, polling: false,
    selected: null, players: [], lastPaid: null };

  const views = { form: $("#form"), busy: $("#busy"), results: $("#results"), failed: $("#failed") };
  function show(name) {
    for (const [k, v] of Object.entries(views)) v.hidden = k !== name;
  }
  function setUrl(params) {
    const u = new URL(location.href);
    ["job", "t", "order", "ot"].forEach((k) => u.searchParams.delete(k));
    for (const [k, v] of Object.entries(params || {})) if (v) u.searchParams.set(k, v);
    history.replaceState(null, "", u.pathname + (u.search ? u.search : "") + u.hash);
  }
  function scrollToTool(smooth = true) {
    const t = $("#tool");
    const y = t.getBoundingClientRect().top + window.scrollY - 76;
    // при смене состояния высота карточки резко меняется — плавная прокрутка «промахивается»
    if (Math.abs(window.scrollY - y) < 4) return;
    window.scrollTo({ top: Math.max(0, y), behavior: smooth ? "smooth" : "auto" });
  }

  // ---------- шапка ----------
  const top = $("#top");
  const onScroll = () => top.classList.toggle("scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  $$("[data-go-tool]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    scrollToTool();
    if (!views.form.hidden && !state.file) setTimeout(() => $("#file").click(), 350);
  }));
  $$("[data-max-mb]").forEach((n) => (n.textContent = CFG.maxUploadMb));
  $$("[data-retention]").forEach((n) => (n.textContent = CFG.retentionDays));
  $$("[data-rebuilds]").forEach((n) => (n.textContent = CFG.rebuilds));
  (() => {
    const c = $("#contacts");
    if (CFG.contactEmail) c.append(el("a", { href: `mailto:${CFG.contactEmail}`, text: CFG.contactEmail }));
    if (CFG.contactTelegram) {
      if (CFG.contactEmail) c.append(" · ");
      const tg = CFG.contactTelegram.replace(/^@/, "");
      c.append(el("a", { href: `https://t.me/${tg}`, target: "_blank", rel: "noopener", text: `Telegram @${tg}` }));
    }
  })();

  // ---------- форма ----------
  const fileInput = $("#file"), drop = $("#drop"), picked = $("#picked"), target = $("#target");
  function pickFile(f) {
    if (!f) return;
    formError("");
    if (f.size > CFG.maxUploadMb * 1024 * 1024) {
      formError(`Файл больше ${CFG.maxUploadMb} МБ. Сожмите его или загрузите MP3.`);
      return;
    }
    state.file = f;
    state.fileDuration = null;
    $("#fname").textContent = f.name;
    $("#fmeta").textContent = `${(f.size / 1048576).toFixed(1).replace(".", ",")} МБ`;
    drop.hidden = true;
    picked.hidden = false;
    // длительность — чтобы сразу подсказать, сократим или удлиним
    try {
      const url = URL.createObjectURL(f);
      const a = new Audio();
      a.preload = "metadata";
      a.onloadedmetadata = () => {
        if (isFinite(a.duration) && a.duration > 0) {
          state.fileDuration = a.duration;
          $("#fmeta").textContent = `${fmt(a.duration)} · ${(f.size / 1048576).toFixed(1).replace(".", ",")} МБ`;
          updateHint();
        }
        URL.revokeObjectURL(url);
      };
      a.onerror = () => URL.revokeObjectURL(url);
      a.src = url;
    } catch (e) { /* не страшно */ }
    track("upload_start", { size_mb: Math.round(f.size / 1048576) });
  }
  fileInput.addEventListener("change", () => pickFile(fileInput.files[0]));
  drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
  ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => pickFile(e.dataTransfer.files[0]));
  $("#tool").addEventListener("dragover", (e) => e.preventDefault());
  $("#tool").addEventListener("drop", (e) => { e.preventDefault(); if (!views.form.hidden) pickFile(e.dataTransfer.files[0]); });
  $("#change").addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });

  function currentTarget() { return parseTime(target.value); }
  function syncChips() {
    const t = currentTarget();
    $$("#presets .chip").forEach((c) => c.setAttribute("aria-pressed", String(Math.abs(parseTime(c.dataset.t) - t) < 0.05)));
  }
  function updateHint() {
    const t = currentTarget(), hint = $("#durhint");
    if (!isFinite(t)) { hint.textContent = "Введите время в формате мин:сек, например 1:30."; return; }
    if (state.fileDuration) {
      const d = state.fileDuration;
      if (Math.abs(d - t) < 1) hint.textContent = `Трек уже почти нужной длины — чуть подправим темп.`;
      else if (d > t) hint.textContent = `Сократим с ${fmt(d)} до ${fmtPrecise(t)} — уберём ${fmt(d - t)}.`;
      else if (t > d * 3) hint.textContent = `Удлинить можно максимум в 3 раза (до ${fmt(d * 3)}).`;
      else hint.textContent = `Удлиним с ${fmt(d)} до ${fmtPrecise(t)}, повторив подходящий фрагмент.`;
    } else {
      hint.textContent = "Точное время берите из положения о соревнованиях или у тренера.";
    }
  }
  target.addEventListener("input", () => { syncChips(); updateHint(); });
  target.addEventListener("blur", () => { const t = currentTarget(); if (isFinite(t)) target.value = fmtPrecise(t).replace(/,0$/, ""); });
  $$("[data-step]").forEach((b) => b.addEventListener("click", () => {
    let t = currentTarget();
    if (!isFinite(t)) t = 90;
    t = Math.min(CFG.maxTarget, Math.max(CFG.minTarget, Math.round(t) + Number(b.dataset.step)));
    target.value = fmt(t);
    syncChips(); updateHint();
  }));
  $$("#presets .chip").forEach((c) => c.addEventListener("click", () => { target.value = c.dataset.t; syncChips(); updateHint(); }));
  $$("[data-ending]").forEach((b) => b.addEventListener("click", () => {
    state.ending = b.dataset.ending;
    $$("[data-ending]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  }));
  const tempo = $("#tempo");
  tempo.addEventListener("input", () => {
    const v = Number(tempo.value);
    $("#tempoval").textContent = v === 0 ? "без изменений" : `${v > 0 ? "быстрее" : "медленнее"} на ${Math.abs(v)} %`;
  });
  function formError(msg) {
    const e = $("#formerr");
    e.textContent = msg;
    e.hidden = !msg;
  }

  $("#form").addEventListener("submit", (e) => {
    e.preventDefault();
    const t = currentTarget();
    if (!state.file) { formError("Сначала выберите файл с музыкой."); drop.focus(); return; }
    if (!isFinite(t) || t < CFG.minTarget || t > CFG.maxTarget) {
      formError(`Длительность — от ${CFG.minTarget} секунд до ${Math.floor(CFG.maxTarget / 60)} минут, например 1:30.`);
      target.focus();
      return;
    }
    if (state.fileDuration && t > state.fileDuration * 3) {
      formError(`Трек звучит ${fmt(state.fileDuration)} — удлинить можно максимум до ${fmt(state.fileDuration * 3)}.`);
      return;
    }
    upload(t);
  });

  function setSteps(stage) {
    const order = ["upload", "beats", "plan", "render"];
    const idx = order.indexOf(stage);
    $$("#steps li").forEach((li, i) => {
      li.classList.toggle("done", i < idx);
      li.classList.toggle("on", i === idx);
    });
  }
  function setBar(p) { $("#bar").style.width = `${Math.max(2, Math.min(100, p))}%`; }

  function upload(t) {
    show("busy");
    $("#busytitle").textContent = "Загружаем трек…";
    $("#waitnote").textContent = "Обычно всё занимает 1–2 минуты. Страницу можно не обновлять — результат появится сам.";
    setSteps("upload");
    setBar(2);
    scrollToTool(false);
    const fd = new FormData();
    fd.append("file", state.file, state.file.name);
    fd.append("target", String(t));
    fd.append("ending", state.ending);
    fd.append("signal", $("#signal").checked ? "1" : "0");
    fd.append("tempo", String(1 + Number(tempo.value) / 100));
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/jobs");
    xhr.setRequestHeader("X-Device", DEVICE);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) setBar((e.loaded / e.total) * 25); };
    xhr.onload = () => {
      let data = null;
      try { data = JSON.parse(xhr.responseText); } catch (e) { /* ignore */ }
      if (xhr.status >= 200 && xhr.status < 300 && data) {
        startJob(data.id, data.token);
      } else {
        show("form");
        const msg = (data && data.detail) || `Не удалось загрузить файл (ошибка ${xhr.status}).`;
        formError(typeof msg === "string" ? msg : "Не удалось загрузить файл.");
        track("upload_error", { status: xhr.status });
      }
    };
    xhr.onerror = () => { show("form"); formError("Нет связи с сервером. Проверьте интернет и попробуйте ещё раз."); track("upload_error", { status: 0 }); };
    xhr.send(fd);
  }

  function startJob(id, token) {
    state.job = { id };
    state.token = token;
    store.set("takt_last", JSON.stringify({ id, token, ts: Date.now() }));
    setUrl({ job: id, t: token });
    poll();
  }

  async function poll() {
    if (state.polling) return;
    state.polling = true;
    show("busy");
    $("#busytitle").textContent = "Обрабатываем трек…";
    let delay = 900, errors = 0;
    try {
      for (;;) {
        let job;
        try {
          job = await api(`/api/jobs/${state.job.id}?token=${encodeURIComponent(state.token)}`);
          errors = 0;
        } catch (e) {
          if (e.status === 404) { failed("Задание не найдено или устарело. Загрузите трек заново."); return; }
          if (++errors > 20) { failed("Нет связи с сервером. Обновите страницу чуть позже — результат сохранится."); return; }
          await sleep(2000);
          continue;
        }
        state.job = job;
        if (job.status === "queued") {
          setSteps("beats"); setBar(27);
          $("#busytitle").textContent = "Трек в очереди…";
          $("#waitnote").textContent = job.queue > 0 ? `Перед вами ${job.queue} ${plural(job.queue, "трек", "трека", "треков")}. Обычно это пара минут.` : "Сейчас начнём.";
        } else if (job.status === "processing") {
          $("#busytitle").textContent = "Обрабатываем трек…";
          const p = job.progress || 0;
          setSteps(p < 45 ? "beats" : p < 55 ? "plan" : "render");
          setBar(27 + p * 0.73);
          $("#waitnote").textContent = job.stage ? `${job.stage}…` : "Работаем…";
        } else if (job.status === "done") {
          setSteps("done"); setBar(100);
          renderResults(job);
          scrollToTool(false);
          return;
        } else if (job.status === "failed") {
          failed(job.error || "Не получилось обработать трек.");
          return;
        } else if (job.status === "expired") {
          failed(`Файлы этого трека уже удалены (храним ${CFG.retentionDays} дней). Загрузите трек заново.`);
          return;
        }
        await sleep(delay);
        delay = Math.min(delay + 150, 2000);
      }
    } finally {
      state.polling = false;
    }
  }

  function failed(msg) {
    show("failed");
    $("#failmsg").textContent = msg;
  }
  $("#retry").addEventListener("click", restart);
  $("#restart").addEventListener("click", restart);
  function restart() {
    stopAll();
    state.job = null; state.token = null; state.selected = null;
    setUrl({});
    show("form");
    formError("");
    scrollToTool();
  }

  // ---------- плеер и волна ----------
  function stopAll(except) {
    state.players.forEach((p) => { if (p !== except) p.pause(); });
  }
  function makePlayer(root, { src, peaks, duration, seams = [], onplay }) {
    const btn = $(".play", root), wave = $(".wave", root), canvas = $("canvas", wave), timeEl = $(".v-time", root);
    const audio = new Audio();
    audio.preload = "none";
    audio.src = src;
    let raf = 0, dragging = false;
    const PLAY = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
    const PAUSE = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>';
    const dur = () => (isFinite(audio.duration) && audio.duration > 0 ? audio.duration : duration);
    function draw() {
      const dpr = window.devicePixelRatio || 1;
      const w = wave.clientWidth, h = wave.clientHeight;
      if (!w) return;
      if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
      const c = canvas.getContext("2d");
      c.setTransform(dpr, 0, 0, dpr, 0, 0);
      c.clearRect(0, 0, w, h);
      const n = Math.max(24, Math.floor(w / 3.2));
      const step = peaks.length / n;
      const pos = dur() ? audio.currentTime / dur() : 0;
      const bw = Math.max(1.4, w / n - 1.4);
      for (let i = 0; i < n; i++) {
        let v = 0;
        for (let j = Math.floor(i * step); j < Math.floor((i + 1) * step); j++) v = Math.max(v, peaks[j] || 0);
        const bh = Math.max(2, v * (h - 6));
        c.fillStyle = i / n <= pos ? "#6d28d9" : "#cfc6ec";
        const x = (i * w) / n;
        c.beginPath();
        if (c.roundRect) c.roundRect(x, (h - bh) / 2, bw, bh, 1.2); else c.rect(x, (h - bh) / 2, bw, bh);
        c.fill();
      }
      c.fillStyle = "#e11d74";
      for (const s of seams) {
        const x = (s / dur()) * w;
        c.fillRect(Math.round(x) - 1, 0, 2, h);
        c.beginPath(); c.arc(Math.round(x), 4, 4, 0, Math.PI * 2); c.fill();
      }
      if (timeEl) timeEl.textContent = `${fmt(audio.currentTime)} / ${fmt(dur())}`;
    }
    function loop() { draw(); if (!audio.paused) raf = requestAnimationFrame(loop); }
    audio.addEventListener("play", () => { btn.innerHTML = PAUSE; btn.setAttribute("aria-label", "Пауза"); stopAll(api_); cancelAnimationFrame(raf); loop(); if (onplay) onplay(); });
    audio.addEventListener("pause", () => { btn.innerHTML = PLAY; btn.setAttribute("aria-label", "Слушать"); draw(); });
    audio.addEventListener("ended", () => { btn.innerHTML = PLAY; draw(); });
    audio.addEventListener("loadedmetadata", draw);
    btn.addEventListener("click", () => (audio.paused ? audio.play().catch(() => {}) : audio.pause()));
    function seekFromEvent(e) {
      const r = wave.getBoundingClientRect();
      const x = Math.min(Math.max((e.clientX - r.left) / r.width, 0), 1);
      audio.currentTime = x * dur();
      draw();
    }
    wave.addEventListener("pointerdown", (e) => { dragging = true; wave.setPointerCapture(e.pointerId); seekFromEvent(e); });
    wave.addEventListener("pointermove", (e) => { if (dragging) seekFromEvent(e); });
    wave.addEventListener("pointerup", () => {
      dragging = false;
      if (audio.paused) audio.play().catch(() => {});
    });
    const api_ = {
      audio,
      pause() { audio.pause(); },
      playFrom(t) {
        const go = () => { audio.currentTime = Math.max(0, t); audio.play().catch(() => {}); };
        if (audio.readyState >= 1) go(); else { audio.addEventListener("loadedmetadata", go, { once: true }); audio.load(); }
      },
      draw,
    };
    state.players.push(api_);
    requestAnimationFrame(draw);
    return api_;
  }
  window.addEventListener("resize", () => state.players.forEach((p) => p.draw()));

  // ---------- результаты ----------
  const QUALITY = {
    great: ["b-great", "Склейку почти не слышно"],
    ok: ["b-ok", "Хорошая склейка"],
    check: ["b-check", "Послушайте склейку"],
    fade: ["b-fade", "Финал с затуханием"],
  };

  function renderResults(job) {
    stopAll();
    state.players = state.players.filter((p) => p.demo);
    show("results");
    const vs = job.variants || [];
    const n = vs.length;
    $("#restitle").textContent = n === 1 ? "Готово: 1 вариант" : `Готово: ${n} ${plural(n, "вариант", "варианта", "вариантов")}`;
    const an = job.analysis || {};
    const parts = [`${job.filename || "Трек"}: ${fmt(an.source_duration)} → ${fmtPrecise(job.target)}`];
    if (an.tempo) parts.push(`${Math.round(an.tempo)} уд/мин`);
    if (an.unit === "bar" && an.meter) parts.push(`размер ${an.meter}/4`);
    $("#ressub").textContent = parts.join(" · ");
    if (an.rubato) {
      $("#ressub").append(el("span", { style: "display:block;margin-top:6px;color:#a35207;font-weight:600",
        text: "В треке свободный темп — внимательно послушайте места склеек." }));
    }
    const box = $("#variants");
    box.innerHTML = "";
    const anyUnlocked = vs.some((v) => v.downloads);
    if (job.rebuild && job.entitled && !anyUnlocked) {
      box.append(el("div", { class: "okmsg", text: "Это бесплатная пересборка: выберите вариант — он откроется без оплаты." }));
    }
    vs.forEach((v, i) => box.append(renderVariant(job, v, i)));
    track("results_view", {}, job.id);
  }

  function renderVariant(job, v, i) {
    const node = $("#tpl-variant").content.firstElementChild.cloneNode(true);
    node.dataset.index = v.index;
    let name = `Вариант ${i + 1}`;
    if (i === 0 && v.quality !== "check") name += " · рекомендуем";
    $(".v-name", node).textContent = name;
    const badge = $(".badge", node);
    let q = QUALITY[v.quality] || QUALITY.ok;
    if (v.kind === "stretch") q = ["b-great", "Без склеек — только темп"];
    badge.className = `badge ${q[0]}`;
    badge.textContent = q[1];
    const seams = (v.seams || []).map((s) => s.t);
    const player = makePlayer(node, { src: v.preview_url, peaks: v.peaks || [], duration: v.duration, seams,
      onplay: () => track("preview_play", { variant: v.index }, job.id) });
    const info = $(".v-info", node);
    const uniq = [];
    (v.seams || []).forEach((s) => { if (!uniq.some((u) => Math.abs(u.t - s.t) < 0.5)) uniq.push(s); });
    uniq.forEach((s, k) => {
      info.append(el("button", { class: "seamlink", type: "button",
        text: uniq.length > 1 ? `Склейка ${k + 1} (${fmt(s.t)}) — послушать` : `Склейка на ${fmt(s.t)} — послушать`,
        onclick: () => { player.playFrom(s.t - 3); track("seam_jump", { variant: v.index }, job.id); } }));
    });
    if (v.kind === "extend") info.append(el("span", { text: "Удлинено повтором фрагмента" }));
    if (Math.abs(v.tempo_change) >= 0.2) info.append(el("span", { text: `Темп ${pct(v.tempo_change)}` }));
    if (v.kind === "fade") info.append(el("span", { text: `Затухание ${Math.round(v.fade_out)} с в конце` }));
    if (job.options && job.options.signal) info.append(el("span", { text: "Сигнал за 2 с до музыки" }));
    info.append(el("span", { text: `Длительность музыки ${fmtPrecise(v.music_duration)}` }));
    const actions = $(".v-actions", node), extra = $(".v-extra", node);
    if (v.downloads) {
      node.classList.add("sel");
      badge.insertAdjacentElement("afterend", el("span", { class: "badge b-paid", text: "Оплачено" }));
      extra.append(renderPaid(job, v));
    } else if (job.rebuild && job.entitled && !(job.variants || []).some((x) => x.downloads)) {
      actions.append(el("button", { class: "btn btn-primary", type: "button", text: "Забрать бесплатно",
        onclick: async (e) => {
          e.target.disabled = true;
          try {
            await api(`/api/jobs/${job.id}/claim`, { method: "POST", body: JSON.stringify({ token: state.token, variant: v.index }) });
            await reloadJob();
          } catch (err) { e.target.disabled = false; alert(err.message); }
        } }));
    } else {
      actions.append(el("button", { class: "btn btn-primary", type: "button", text: `Выбрать — ${rub(CFG.priceSingle)}`,
        onclick: () => openCheckout(job, v, node) }));
    }
    return node;
  }

  function openCheckout(job, v, node) {
    $$(".variant").forEach((x) => { x.classList.remove("sel"); const c = $(".checkout", x); if (c) c.remove(); $$(".v-actions", x).forEach((a) => (a.hidden = false)); });
    node.classList.add("sel");
    $(".v-actions", node).hidden = true;
    state.selected = v.index;
    track("variant_selected", { variant: v.index }, job.id);
    const err = el("div", { class: "err", hidden: true });
    const email = el("input", { type: "email", placeholder: CFG.requireEmail ? "E-mail для чека и ссылки" : "E-mail (необязательно) — пришлём ссылку", autocomplete: "email", inputmode: "email" });
    const lastEmail = store.get("takt_email");
    if (lastEmail) email.value = lastEmail;
    const payBtn = el("button", { class: "btn btn-primary btn-lg btn-block", type: "button", text: `Оплатить ${rub(CFG.priceSingle)}` });
    const perTrack = Math.round(CFG.pricePack / CFG.packSize);
    const packBtn = el("button", { class: "btn btn-line pack-btn", type: "button" },
      el("span", {}, el("b", { text: `Пакет ${CFG.packSize} треков — ${rub(CFG.pricePack)}` }),
        el("small", { text: `${rub(perTrack)} за трек. Этот + ещё ${CFG.packSize - 1} по коду` })),
      el("span", { text: "→" }));
    const codeInput = el("input", { type: "text", placeholder: "TAKT-XXXX-XXXX", autocomplete: "off", "aria-label": "Код пакета" });
    const codeBtn = el("button", { class: "btn btn-ghost", type: "button", text: "Применить" });
    const codeBox = el("div", { class: "codebox", hidden: true }, codeInput, codeBtn);
    const codeLink = el("button", { class: "link", type: "button", text: "У меня есть код пакета",
      onclick: () => { codeBox.hidden = false; codeLink.hidden = true; codeInput.focus(); } });
    const lastCode = store.get("takt_pack");
    if (lastCode) codeInput.value = lastCode;
    const box = el("div", { class: "checkout fade-in" },
      email,
      el("div", { class: "pay-grid" }, payBtn, packBtn),
      el("div", { style: "margin-top:12px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap" }, codeLink,
        el("button", { class: "link", type: "button", text: "Отмена", onclick: () => {
          box.remove(); node.classList.remove("sel"); $(".v-actions", node).hidden = false; } })),
      codeBox, err,
      el("p", { class: "fine" }));
    $(".fine", box).innerHTML = `Оплата картой или через СБП. Оплачивая, вы принимаете <a href="/offer" target="_blank">оферту</a>.`;
    async function pay(product, btn) {
      err.hidden = true;
      const mail = email.value.trim();
      if (CFG.requireEmail && !mail) { err.textContent = "Укажите e-mail — пришлём чек и ссылку на трек."; err.hidden = false; email.focus(); return; }
      if (mail && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) { err.textContent = "Проверьте e-mail."; err.hidden = false; email.focus(); return; }
      if (mail) store.set("takt_email", mail);
      btn.disabled = true;
      try {
        const r = await api(`/api/jobs/${job.id}/checkout`, { method: "POST",
          body: JSON.stringify({ token: state.token, variant: v.index, product, email: mail || null }) });
        track("checkout_open", { product, variant: v.index }, job.id);
        store.set("takt_order", JSON.stringify({ id: r.order_id, token: r.order_token, job: job.id, t: state.token, ts: Date.now() }));
        location.href = r.confirmation_url;
      } catch (e) {
        err.textContent = e.message; err.hidden = false; btn.disabled = false;
      }
    }
    payBtn.addEventListener("click", () => pay("single", payBtn));
    packBtn.addEventListener("click", () => pay("pack", packBtn));
    codeBtn.addEventListener("click", async () => {
      err.hidden = true;
      const code = codeInput.value.trim();
      if (!code) { codeInput.focus(); return; }
      codeBtn.disabled = true;
      try {
        const r = await api(`/api/jobs/${job.id}/redeem`, { method: "POST", body: JSON.stringify({ token: state.token, variant: v.index, code }) });
        store.set("takt_pack", code.toUpperCase());
        state.lastPaid = { variant: v.index, packCode: code.toUpperCase(), packRemaining: r.remaining };
        await reloadJob();
      } catch (e) { err.textContent = e.message; err.hidden = false; codeBtn.disabled = false; }
    });
    $(".v-extra", node).append(box);
    track("pack_offer_view", {}, job.id);
  }

  function renderPaid(job, v) {
    const wrap = el("div", { class: "fade-in" });
    wrap.append(el("div", { class: "okmsg", text: "Готово! Скачайте трек — ссылки действуют " + CFG.retentionDays + " " + plural(CFG.retentionDays, "день", "дня", "дней") + "." }));
    wrap.append(el("div", { class: "dl" },
      el("a", { class: "btn btn-primary", href: v.downloads.mp3, onclick: () => track("download_click", { fmt: "mp3" }, job.id), text: "Скачать MP3" }),
      el("a", { class: "btn btn-line", href: v.downloads.wav, onclick: () => track("download_click", { fmt: "wav" }, job.id), text: "WAV без сжатия" })));
    const lp = state.lastPaid;
    if (lp && lp.packCode && lp.variant === v.index) {
      const copy = el("button", { class: "link", type: "button", text: "Скопировать", onclick: () => {
        try { navigator.clipboard.writeText(lp.packCode); copy.textContent = "Скопировано"; } catch (e) { /* ignore */ } } });
      wrap.append(el("div", { class: "packcode" },
        el("div", { text: "Ваш код пакета — сохраните его:" }), el("code", { text: lp.packCode }), " ", copy,
        el("div", { class: "hint", text: lp.packRemaining != null ? `Осталось ${lp.packRemaining} ${plural(lp.packRemaining, "трек", "трека", "треков")}. Введите код вместо оплаты у следующего трека.` : "" })));
    }
    // оценка
    const rate = el("div", { class: "rate" }, el("div", { class: "label" }, el("span", { text: "Как вам результат?" })));
    const seg = el("div", { class: "seg", role: "group" });
    const comment = el("input", { type: "text", placeholder: "Что поправить? (необязательно)", hidden: true, style: "margin-top:8px;width:100%;border:1.5px solid #d9d3ea;border-radius:12px;padding:10px 12px" });
    const thanks = el("div", { class: "hint", hidden: true, text: "Спасибо! Это помогает делать склейки лучше." });
    [["ready", "Готово к выступлению"], ["needs_fix", "Нужны правки"], ["bad", "Не подошло"]].forEach(([r, label]) => {
      seg.append(el("button", { type: "button", "aria-pressed": "false", text: label, onclick: async (e) => {
        $$("button", seg).forEach((b) => b.setAttribute("aria-pressed", String(b === e.target)));
        comment.hidden = r === "ready";
        send(r);
      } }));
    });
    let rating = null;
    async function send(r) {
      rating = r || rating;
      try {
        await api(`/api/jobs/${job.id}/feedback`, { method: "POST", body: JSON.stringify({ token: state.token, variant: v.index, rating, comment: comment.value || null }) });
        thanks.hidden = false;
      } catch (e) { /* не критично */ }
    }
    comment.addEventListener("change", () => send());
    rate.append(seg, comment, thanks);
    wrap.append(rate);
    // пересборка
    if (job.rebuilds_left > 0) {
      const inp = el("input", { value: fmt(job.target), inputmode: "decimal", "aria-label": "Новая длительность" });
      const btn = el("button", { class: "btn btn-ghost", type: "button", text: "Пересобрать" });
      const msg = el("div", { class: "err", hidden: true });
      btn.addEventListener("click", async () => {
        const t = parseTime(inp.value);
        if (!isFinite(t)) { msg.textContent = "Введите время, например 1:25"; msg.hidden = false; return; }
        btn.disabled = true;
        try {
          const r = await api(`/api/jobs/${job.id}/rebuild`, { method: "POST", body: JSON.stringify({ token: state.token, target: String(t) }) });
          track("rebuild_open", {}, job.id);
          state.lastPaid = null;
          startJob(r.id, r.token);
          scrollToTool(false);
        } catch (e) { msg.textContent = e.message; msg.hidden = false; btn.disabled = false; }
      });
      wrap.append(el("div", { class: "rebuild" },
        el("div", { class: "label" }, el("span", { text: "Нужна другая длительность?" }),
          el("small", { text: `бесплатно ещё ${job.rebuilds_left} ${plural(job.rebuilds_left, "раз", "раза", "раз")}` })),
        el("div", { class: "row" }, inp, btn), msg));
    }
    return wrap;
  }

  async function reloadJob() {
    const job = await api(`/api/jobs/${state.job.id}?token=${encodeURIComponent(state.token)}`);
    state.job = job;
    renderResults(job);
  }

  // ---------- возврат после оплаты ----------
  async function checkOrder(orderId, orderToken, quick = false) {
    show("busy");
    $("#busytitle").textContent = "Проверяем оплату…";
    $("#waitnote").textContent = "Обычно это несколько секунд.";
    setSteps("done"); setBar(100);
    let order = null;
    for (let i = 0; i < (quick ? 4 : 40); i++) {
      try {
        order = await api(`/api/orders/${orderId}?token=${encodeURIComponent(orderToken)}`);
      } catch (e) {
        if (e.status === 404) break;
      }
      if (order && order.status !== "pending") break;
      await sleep(i < 10 ? 1500 : 3000);
    }
    setUrl({ job: state.job.id, t: state.token });
    store.del("takt_order");
    await reloadJob().catch(() => {});
    if (!order) return;
    if (order.status === "paid") {
      goal("payment_success", { product: order.product });
      if (order.pack_code) {
        store.set("takt_pack", order.pack_code);
        state.lastPaid = { variant: order.variant, packCode: order.pack_code, packRemaining: order.pack_remaining };
        await reloadJob().catch(() => {});
      }
      const v = $(`.variant[data-index="${order.variant}"]`);
      if (v) v.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (order.status === "canceled") {
      $("#variants").prepend(el("div", { class: "err", text: "Оплата не прошла или была отменена. Можно попробовать ещё раз." }));
    } else {
      $("#variants").prepend(el("div", { class: "err", text: "Оплата ещё обрабатывается. Обновите страницу через минуту — трек откроется автоматически." }));
    }
  }

  // ---------- восстановление ссылок ----------
  $("#restoreform").addEventListener("submit", async (e) => {
    e.preventDefault();
    const m = $("#restoremsg");
    try {
      await api("/api/restore", { method: "POST", body: JSON.stringify({ email: $("#restoreemail").value }) });
      m.className = "okmsg"; m.textContent = "Если на этот адрес были покупки, письмо уже в пути.";
    } catch (err) { m.className = "err"; m.textContent = err.message; }
    m.hidden = false;
  });
  $$(".faq details").forEach((d) => d.addEventListener("toggle", () => { if (d.open) track("faq_open", { q: $("summary", d).textContent.slice(0, 40) }); }));

  // ---------- демо ----------
  (async () => {
    try {
      const d = await fetch("/static/demo/demo.json").then((r) => (r.ok ? r.json() : null));
      if (!d) { $("#demo").hidden = true; return; }
      const before = $('[data-demo="before"]').closest(".card"), after = $('[data-demo="after"]').closest(".card");
      $('[data-demo-dur="before"]').textContent = fmt(Math.round(d.before.duration));
      const pb = makePlayer(before, { src: d.before.url, peaks: d.before.peaks, duration: d.before.duration, onplay: () => track("demo_play", { which: "before" }) });
      const pa = makePlayer(after, { src: d.after.url, peaks: d.after.peaks, duration: d.after.duration, seams: d.after.seams, onplay: () => track("demo_play", { which: "after" }) });
      pb.demo = pa.demo = true;
      $("[data-demo-seam]").addEventListener("click", () => pa.playFrom((d.after.seams[0] || 0) - 3));
      if (d.credit) $("#democredit").textContent = d.credit;
    } catch (e) { $("#demo").hidden = true; }
  })();

  // ---------- тестовый режим оплаты: видно сразу, чтобы не забыть переключить ----------
  if (CFG.mockPayments) {
    document.body.prepend(el("div", { style: "background:#a35207;color:#fff;text-align:center;font:600 13px/1.4 Manrope,sans-serif;padding:6px 12px",
      text: "Тестовый режим оплаты: деньги не списываются. Для запуска включите PAYMENT_PROVIDER=yookassa." }));
  }

  // ---------- старт ----------
  track("landing_view", { ref: document.referrer ? new URL(document.referrer).hostname : "" });
  syncChips();
  const qs = new URLSearchParams(location.search);
  const jobId = qs.get("job"), jobToken = qs.get("t");
  if (jobId && jobToken) {
    state.job = { id: jobId };
    state.token = jobToken;
    const orderId = qs.get("order"), orderToken = qs.get("ot");
    if (orderId && orderToken) checkOrder(orderId, orderToken);
    else poll();
    setTimeout(scrollToTool, 50);
  } else {
    // вернулись с оплаты без параметров (например, закрыли вкладку) — проверим незавершённый заказ
    const pending = store.get("takt_order");
    if (pending) {
      try {
        const o = JSON.parse(pending);
        if (!o.ts || Date.now() - o.ts > 30 * 60 * 1000) throw new Error("old");
        state.job = { id: o.job }; state.token = o.t;
        setUrl({ job: o.job, t: o.t });
        checkOrder(o.id, o.token, true);
      } catch (e) { store.del("takt_order"); }
    }
  }
})();
