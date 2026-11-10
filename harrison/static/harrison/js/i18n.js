(function () {
  var STRINGS = {
    en: {
      nav_home: "Home",
      nav_work: "Work",
      nav_lab: "Lab",
      nav_chat: "Chat",
      nav_about: "About",
      hero_eyebrow: "Nairobi · software developer",
      hero_lede: "Fullstack in Nairobi — payments, APIs, and VPS. Ask the agent anything about the work.",
      hero_ask: "Ask Harrison",
      hero_work: "Explore projects",
      chat_greet: "Ask about a project, a job, or how to get in touch.",
      chip_who: "Who are you?",
      chip_built: "What have you built?",
      chip_contact: "How do I contact you?",
      chat_placeholder: "Type a message...",
      chat_send: "Send"
    },
    sw: {
      nav_home: "Nyumbani",
      nav_work: "Kazi",
      nav_lab: "Maabara",
      nav_chat: "Soga",
      nav_about: "Kuhusu",
      hero_eyebrow: "Nairobi · mtengenezaji programu",
      hero_lede: "Fullstack Nairobi — malipo, API, na VPS. Uliza agent kuhusu kazi yangu.",
      hero_ask: "Uliza Harrison",
      hero_work: "Angalia miradi",
      chat_greet: "Uliza kuhusu mradi, kazi, au jinsi ya kuwasiliana.",
      chip_who: "Wewe ni nani?",
      chip_built: "Umejenga nini?",
      chip_contact: "Nawezaje kukuwasiliana?",
      chat_placeholder: "Andika ujumbe...",
      chat_send: "Tuma"
    }
  };

  function apply(lang) {
    var dict = STRINGS[lang] || STRINGS.en;
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (!dict[key]) return;
      el.textContent = dict[key];
    });
    // Keep chip queries in English so FAQ matching stays reliable.
    document.querySelectorAll("[data-hm-chip][data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var en = (STRINGS.en || {})[key];
      if (en) el.setAttribute("data-hm-chip", en);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (dict[key]) el.setAttribute("placeholder", dict[key]);
    });
    try { localStorage.setItem("portfolio-lang", lang); } catch (e) {}
    document.querySelectorAll("[data-lang]").forEach(function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-lang") === lang ? "true" : "false");
    });
  }

  var start = "en";
  try { start = localStorage.getItem("portfolio-lang") || "en"; } catch (e) {}
  apply(start);

  document.querySelectorAll("[data-lang]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      apply(btn.getAttribute("data-lang") || "en");
    });
  });
})();
