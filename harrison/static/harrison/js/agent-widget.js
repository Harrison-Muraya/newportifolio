(function () {
  var fab = document.getElementById("hm-fab");
  var dock = document.getElementById("hm-dock");
  if (!fab || !dock) return;

  var closeBtn = document.getElementById("hm-dock-close");
  var form = document.getElementById("hm-dock-form");
  var input = document.getElementById("hm-dock-input");
  var log = document.getElementById("hm-dock-log");
  var status = document.getElementById("hm-dock-status");
  var chipsWrap = document.getElementById("hm-chips");
  var chips = dock.querySelectorAll("[data-hm-chip]");
  var announcer = document.getElementById("hm-announcer");
  var history = [];
  var sending = false;
  var chat = window.HarrisonChat;
  var lastFocus = null;
  var mobileQuery = window.matchMedia("(max-width: 640px)");

  function isMobile() {
    return mobileQuery.matches;
  }

  function focusables() {
    return Array.prototype.slice
      .call(
        dock.querySelectorAll(
          'button:not([disabled]), textarea, input, select, [href], [tabindex]:not([tabindex="-1"])'
        )
      )
      .filter(function (el) {
        return el.offsetParent !== null || el === document.activeElement;
      });
  }

  function setKeyboardInset() {
    if (!window.visualViewport) return;
    var inset = Math.max(0, window.innerHeight - window.visualViewport.height - window.visualViewport.offsetTop);
    document.documentElement.style.setProperty("--keyboard-inset", inset + "px");
  }

  function openDock(seed) {
    lastFocus = document.activeElement;
    dock.classList.add("is-open");
    dock.setAttribute("aria-hidden", "false");
    dock.setAttribute("aria-modal", isMobile() ? "true" : "false");
    fab.setAttribute("aria-expanded", "true");
    if (isMobile()) document.body.classList.add("modal-open");
    setKeyboardInset();
    if (seed && input) input.value = seed;
    if (input) input.focus();
    if (window.portfolioTrack) window.portfolioTrack("agent_opened");
  }

  function closeDock() {
    dock.classList.remove("is-open");
    dock.setAttribute("aria-hidden", "true");
    dock.setAttribute("aria-modal", "false");
    fab.setAttribute("aria-expanded", "false");
    document.body.classList.remove("modal-open");
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
    else fab.focus();
  }

  function addBubble(text, who) {
    var bubble = document.createElement("div");
    bubble.className = "hm-msg hm-msg-" + who;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  function showTyping() {
    if (status) {
      status.innerHTML =
        '<span class="hm-typing" aria-hidden="true"><span></span><span></span><span></span></span> Thinking…';
    }
    if (log) log.setAttribute("aria-busy", "true");
  }

  function clearStatus() {
    if (status) status.textContent = "";
    if (log) log.removeAttribute("aria-busy");
  }

  function announce(text) {
    if (announcer) announcer.textContent = text || "";
  }

  function hideChips() {
    if (chipsWrap) chipsWrap.hidden = true;
  }

  function pushHistory(message, reply) {
    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: reply });
    history = history.slice(-12);
  }

  function setSending(on) {
    sending = on;
    if (form) form.querySelector("button").disabled = on;
    chips.forEach(function (chip) {
      chip.disabled = on;
    });
  }

  function ask(message) {
    if (sending || !message || !chat) return;
    setSending(true);
    hideChips();
    addBubble(message, "user");
    if (input) input.value = "";

    var local = chat.matchLocal(message);
    if (local) {
      addBubble(local, "bot");
      pushHistory(message, local);
      announce(local);
      setSending(false);
      if (input) input.focus();
      return;
    }

    showTyping();
    var botBubble = null;

    chat
      .send(
        message,
        history,
        {
          onStart: function () {
            botBubble = addBubble("", "bot");
          },
          onToken: function (_token, full) {
            if (!botBubble) botBubble = addBubble("", "bot");
            botBubble.textContent = full;
            log.scrollTop = log.scrollHeight;
          },
          onDone: function (reply) {
            clearStatus();
            if (!botBubble) botBubble = addBubble(reply, "bot");
            else botBubble.textContent = reply;
            pushHistory(message, reply);
            announce(reply);
          }
        },
        form
      )
      .catch(function (err) {
        var msg = (err && err.message) || "Agent offline — email still works.";
        addBubble(msg, "bot");
        announce(msg);
      })
      .finally(function () {
        setSending(false);
        clearStatus();
        if (input) input.focus();
      });
  }

  fab.addEventListener("click", function () {
    if (dock.classList.contains("is-open")) closeDock();
    else openDock();
  });
  if (closeBtn) closeBtn.addEventListener("click", closeDock);

  document.addEventListener("keydown", function (event) {
    if (!dock.classList.contains("is-open")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeDock();
      return;
    }
    if (event.key !== "Tab" || !isMobile()) return;
    var nodes = focusables();
    if (!nodes.length) return;
    var first = nodes[0];
    var last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  if (input) {
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        ask((input.value || "").trim());
      }
    });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    ask((input.value || "").trim());
  });

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      ask(chip.getAttribute("data-hm-chip") || chip.textContent.trim());
    });
  });

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setKeyboardInset);
    window.visualViewport.addEventListener("scroll", setKeyboardInset);
  }

  window.hmOpenAgent = openDock;
  window.hmAskAgent = function (message) {
    openDock();
    ask(message);
  };

  document.addEventListener("click", function (event) {
    var trigger = event.target.closest("[data-open-agent]");
    if (trigger) {
      event.preventDefault();
      openDock(trigger.getAttribute("data-agent-seed") || "");
      return;
    }
    var askTrigger = event.target.closest("[data-ask-agent]");
    if (askTrigger) {
      event.preventDefault();
      var q = askTrigger.getAttribute("data-ask-agent");
      openDock();
      if (q) ask(q);
    }
  });
})();
