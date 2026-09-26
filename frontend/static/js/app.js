/* ============================================================
   Trip Planner AI — frontend JavaScript
   Talks to:  POST   /api/travel  { message, thread_id }
              GET    /api/config          credential status
              POST   /api/config          set session keys
              DELETE /api/config          fall back to server .env
              GET    /health
   ============================================================ */
(function () {
  "use strict";

  /* ---------------- dom ---------------- */

  var $ = function (id) { return document.getElementById(id); };

  var conversation = $("conversation");
  var messages     = $("messages");
  var hero         = $("hero");
  var input        = $("input");
  var composer     = $("composer");
  var sendBtn      = $("sendBtn");
  var builder      = $("builder");
  var toastEl      = $("toast");

  var composerWrap = document.querySelector(".composer-wrap");

  var statusBtn    = $("apiStatus");
  var statusText   = statusBtn.querySelector(".status-text");

  var setupGate    = $("setupGate");
  var gateCreds    = $("gateCreds");
  var gateSub      = $("gateSub");
  var gateSave     = $("gateSave");

  var settingsModal = $("settingsModal");
  var settingsScrim = $("settingsScrim");
  var credList      = $("credList");
  var settingsSave  = $("settingsSave");

  /* ---------------- state ---------------- */

  var THEME_KEY = "tripplanner.theme";

  var threadId = null;   // LangGraph conversation thread for the current trip
  var busy = false;
  var config = null;     // last /api/config payload
  var savingConfig = false;

  /* Progress phases - indicative weights for the progress bar */
  var PHASES = [
    { label: "Researching flights…",       weight: 0.20 },
    { label: "Searching hotels…",           weight: 0.17 },
    { label: "Checking the weather…",       weight: 0.13 },
    { label: "Estimating your budget…",     weight: 0.17 },
    { label: "Building your itinerary…",    weight: 0.18 },
    { label: "Writing your travel plan…",   weight: 0.15 }
  ];

  var ESTIMATED_MS = 60000;

  /* ---------------- utils ---------------- */

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  var toastTimer;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    requestAnimationFrame(function () { toastEl.classList.add("show"); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.remove("show");
      setTimeout(function () { toastEl.hidden = true; }, 250);
    }, 2800);
  }

  function scrollToEnd(smooth) {
    requestAnimationFrame(function () {
      conversation.scrollTo({ top: conversation.scrollHeight, behavior: smooth ? "smooth" : "auto" });
    });
  }

  /* ---------------- theme ---------------- */

  function initTheme() {
    var stored = null;
    try { stored = localStorage.getItem(THEME_KEY); } catch (e) {}
    var prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    document.documentElement.setAttribute("data-theme", stored || (prefersLight ? "light" : "dark"));
  }

  $("themeToggle").addEventListener("click", function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
  });

  /* ============================================================
     credentials / settings
     ============================================================ */

  function isReady() {
    return !!(config && config.ready);
  }

  function updateEmptyState() {
    var hasMessages = messages.children.length > 0;
    var ready = isReady();

    setupGate.hidden = ready || hasMessages;
    hero.classList.toggle("is-hidden", !ready || hasMessages);

    composerWrap.classList.toggle("is-locked", !ready);
    input.disabled = !ready || busy;
    sendBtn.disabled = !ready || busy;
  }

  function applyConfig(data) {
    config = data;

    var missing = (data && data.missing) || [];

    if (data && data.ready) {
      statusBtn.setAttribute("data-state", "ok");
      statusText.textContent = "API connected";
      statusBtn.title = "All keys configured — open settings";
    } else {
      statusBtn.setAttribute("data-state", "setup");
      statusText.textContent = "No Live API";
      statusBtn.title = "No API keys configured — open settings";

      var labels = missing.map(function (name) {
        return (data.credentials[name] && data.credentials[name].label) || name;
      });

      gateSub.textContent = labels.length
        ? "The server has no " + joinAnd(labels) + " configured. Add " +
          (labels.length === 1 ? "it" : "them") + " below to start planning."
        : "The server has no API keys configured.";

      renderCreds(gateCreds);
    }

    if (!settingsModal.hidden) renderCreds(credList);

    updateEmptyState();
  }

  function joinAnd(list) {
    if (list.length <= 1) return list[0] || "";
    return list.slice(0, -1).join(", ") + " and " + list[list.length - 1];
  }

  function markUnreachable() {
    config = null;
    statusBtn.setAttribute("data-state", "down");
    statusText.textContent = "API unreachable";
    statusBtn.title = "Could not reach the server";
    updateEmptyState();
  }

  function refreshConfig() {
    return fetch("/api/config", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status)); })
      .then(applyConfig)
      .catch(markUnreachable);
  }

  function renderCreds(container) {
    container.innerHTML = "";

    if (!config || !config.credentials) {
      container.appendChild(el("p", "cred-loading", "Loading…"));
      return;
    }

    Object.keys(config.credentials).forEach(function (name) {
      var info = config.credentials[name];

      var row = el("div", "cred");
      var head = el("div", "cred-head");
      head.appendChild(el("label", "cred-label", info.label));

      var badgeText = info.source === "env" ? "From server .env"
                    : info.source === "session" ? "Set for this session"
                    : "Not configured";

      head.appendChild(el("span", "badge badge-" + (info.source || "missing"), badgeText));
      row.appendChild(head);
      row.appendChild(el("p", "cred-hint", info.hint));

      var field = el("div", "cred-field");
      var inp = el("input");
      inp.type = "password";
      inp.className = "cred-input";
      inp.dataset.key = name;
      inp.placeholder = info.source ? "(leave blank to keep existing)" : "Paste your key here";
      inp.autocomplete = "off";
      field.appendChild(inp);

      var toggle = el("button");
      toggle.type = "button";
      toggle.className = "cred-toggle";
      toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
      toggle.addEventListener("click", function () {
        inp.type = inp.type === "password" ? "text" : "password";
      });
      field.appendChild(toggle);
      row.appendChild(field);
      container.appendChild(row);
    });
  }

  function saveCredentials(container, callback) {
    if (savingConfig) return;
    savingConfig = true;

    var inputs = container.querySelectorAll(".cred-input");
    var body = {};

    inputs.forEach(function (inp) {
      if (!inp.value.trim()) return;
      var key = inp.dataset.key;
      // Map SCREAMING_SNAKE to camelCase for backend
      if (key === "GROQ_API_KEY")  body.groq_api_key  = inp.value.trim();
      if (key === "DATABASE_URL")  body.database_url   = inp.value.trim();
    });

    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        savingConfig = false;
        if (data.ok) {
          toast("Settings saved!");
          refreshConfig();
          if (callback) callback();
        } else {
          var errs = data.errors || {};
          var msgs = Object.values(errs).join(" ");
          toast("Error: " + (msgs || "Could not save settings."));
        }
      })
      .catch(function () {
        savingConfig = false;
        toast("Network error saving settings.");
      });
  }

  /* Gate */
  gateSave.addEventListener("click", function () {
    saveCredentials(gateCreds, function () {
      setupGate.hidden = true;
    });
  });

  /* Settings modal */
  function openSettings() {
    renderCreds(credList);
    settingsModal.hidden = false;
    settingsScrim.hidden = false;
  }

  function closeSettings() {
    settingsModal.hidden = true;
    settingsScrim.hidden = true;
  }

  $("settingsBtn").addEventListener("click", openSettings);
  statusBtn.addEventListener("click", openSettings);
  $("settingsClose").addEventListener("click", closeSettings);
  settingsScrim.addEventListener("click", closeSettings);

  settingsSave.addEventListener("click", function () {
    saveCredentials(credList, closeSettings);
  });

  $("settingsClear").addEventListener("click", function () {
    fetch("/api/config", { method: "DELETE" })
      .then(function () { return refreshConfig(); })
      .then(function () { toast("Reset to server defaults."); closeSettings(); });
  });

  /* ============================================================
     chip suggestions
     ============================================================ */

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      // Strip leading emoji
      var text = chip.textContent.replace(/^\S+\s/, "").trim();
      input.value = text;
      input.focus();
      autoResize();
    });
  });

  /* ============================================================
     progress builder
     ============================================================ */

  var builderFill  = $("builderFill");
  var builderLabel = $("builderLabel");
  var builderTimer = null;
  var phaseIdx     = 0;
  var accumulated  = 0;

  function startBuilder() {
    builder.hidden = false;
    phaseIdx = 0;
    accumulated = 0;
    builderFill.style.width = "0%";
    builderLabel.textContent = PHASES[0].label;
    runPhase();
  }

  function runPhase() {
    clearTimeout(builderTimer);
    if (phaseIdx >= PHASES.length) {
      builderFill.style.width = "95%";
      return;
    }

    var phase = PHASES[phaseIdx];
    var msForPhase = ESTIMATED_MS * phase.weight;
    var steps = 20;
    var stepMs = msForPhase / steps;
    var stepPct = (phase.weight / steps) * 100;
    var stepsDone = 0;

    function tick() {
      stepsDone++;
      accumulated += stepPct;
      builderFill.style.width = Math.min(accumulated, 95) + "%";

      if (stepsDone >= steps) {
        phaseIdx++;
        if (phaseIdx < PHASES.length) {
          builderLabel.textContent = PHASES[phaseIdx].label;
          runPhase();
        }
        return;
      }

      builderTimer = setTimeout(tick, stepMs);
    }

    builderTimer = setTimeout(tick, stepMs);
  }

  function stopBuilder() {
    clearTimeout(builderTimer);
    builderFill.style.width = "100%";
    setTimeout(function () { builder.hidden = true; builderFill.style.width = "0%"; }, 400);
  }

  /* ============================================================
     markdown — minimal subset for AI responses
     ============================================================ */

  function mdToHtml(text) {
    return text
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      .replace(/^---+$/gm, "<hr>")
      .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
      .replace(/(<li>.*?<\/li>(\n|$))+/gs, "<ul>$&</ul>")
      .replace(/\n{2,}/g, "</p><p>")
      .replace(/\n/g, "<br>");
  }

  /* ============================================================
     send a message
     ============================================================ */

  function appendMessage(role, content) {
    var msg    = el("div", "msg msg-" + role);
    var avatar = el("div", "msg-avatar");
    avatar.textContent = role === "user" ? "✈" : "🗺";
    var bubble = el("div", "msg-bubble");

    if (role === "user") {
      bubble.textContent = content;
    } else {
      bubble.innerHTML = "<p>" + mdToHtml(content) + "</p>";
    }

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    messages.appendChild(msg);
    scrollToEnd(true);
    return msg;
  }

  function sendMessage() {
    var text = input.value.trim();
    if (!text || busy) return;

    busy = true;
    input.disabled = true;
    sendBtn.disabled = true;

    hero.classList.add("is-hidden");
    appendMessage("user", text);
    input.value = "";
    autoResize();

    startBuilder();

    fetch("/api/travel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, thread_id: threadId }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        stopBuilder();
        busy = false;

        if (data.error === "missing_credentials") {
          toast("API keys missing — please open Settings.");
          updateEmptyState();
          return;
        }

        if (data.error) {
          appendMessage("ai", "Sorry, something went wrong. Please try again.");
          return;
        }

        if (data.thread_id) threadId = data.thread_id;
        appendMessage("ai", data.reply || "No response returned.");
      })
      .catch(function () {
        stopBuilder();
        busy = false;
        appendMessage("ai", "Network error. Please check your connection and try again.");
      })
      .finally(function () {
        input.disabled = !isReady();
        sendBtn.disabled = !isReady();
        input.focus();
      });
  }

  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  /* auto-resize textarea */
  function autoResize() {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
  }
  input.addEventListener("input", autoResize);

  /* ============================================================
     new trip
     ============================================================ */

  $("newTripBtn").addEventListener("click", function () {
    threadId = null;
    messages.innerHTML = "";
    hero.classList.remove("is-hidden");
    input.value = "";
    input.focus();
    autoResize();
    updateEmptyState();
  });

  /* ============================================================
     init
     ============================================================ */

  initTheme();
  refreshConfig();

}());
