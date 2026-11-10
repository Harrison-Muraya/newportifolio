(function () {
  var FAQ = [
    {
      keys: ["who are you", "your name", "full name", "who is harrison", "wewe ni nani"],
      reply: "I'm Harrison Ng'ang'a Muraya, a fullstack software developer in Nairobi."
    },
    {
      keys: ["contact", "email", "phone", "reach you", "how do i contact", "kukuwasiliana", "wasiliana"],
      reply: "Email hezronmuraya9@gmail.com or harrisonmuraya8@gmail.com. Phone +254 726 688 832. LinkedIn linkedin.com/in/muraya-harrison."
    },
    {
      keys: ["what have you built", "projects", "github", "built", "umejenga"],
      reply: "Flagship work includes HostPro, KENA Coin, Ashkey RideDelivery, Sunne, Alpha Loans, and Harrison Agent. GitHub: github.com/Harrison-Muraya."
    },
    {
      keys: ["where do you work", "current job", "afripixel", "unafanya kazi"],
      reply: "I'm a software developer at Afripixel Solution (since July 2026), building with Laravel, Flask, and payment APIs."
    }
  ];

  function matchLocal(message) {
    var lower = String(message || "").toLowerCase();
    for (var i = 0; i < FAQ.length; i++) {
      for (var j = 0; j < FAQ[i].keys.length; j++) {
        if (lower.indexOf(FAQ[i].keys[j]) !== -1) return FAQ[i].reply;
      }
    }
    return null;
  }

  function csrfToken(form) {
    if (form) {
      var field = form.querySelector("[name=csrfmiddlewaretoken]");
      if (field && field.value) return field.value;
    }
    return window.CSRF_TOKEN || "";
  }

  function parseSseChunk(chunk, onEvent) {
    var lines = chunk.split("\n");
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (line.indexOf("data: ") !== 0) continue;
      try {
        onEvent(JSON.parse(line.slice(6)));
      } catch (err) {
        /* ignore incomplete JSON */
      }
    }
  }

  function send(message, history, hooks, form) {
    hooks = hooks || {};
    var local = matchLocal(message);
    if (local) {
      if (hooks.onStart) hooks.onStart();
      if (hooks.onToken) hooks.onToken(local, local);
      if (hooks.onDone) hooks.onDone(local, "instant");
      return Promise.resolve(local);
    }

    if (hooks.onStart) hooks.onStart();

    return fetch("/chat/stream/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "X-CSRFToken": csrfToken(form)
      },
      body: JSON.stringify({ message: message, history: history || [] })
    }).then(function (res) {
      if (!res.ok || !res.body) {
        return res.json().then(function (data) {
          throw new Error((data && data.detail) || "The agent could not answer.");
        });
      }

      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";
      var reply = "";
      var agent = "remote";

      function handleEvent(event) {
        if (event.error) throw new Error(event.error);
        if (event.agent) agent = event.agent;
        if (event.replace) {
          reply = event.replace;
          if (hooks.onToken) hooks.onToken("", reply);
          return;
        }
        if (event.token) {
          reply += event.token;
          if (hooks.onToken) hooks.onToken(event.token, reply);
        }
      }

      function pump() {
        return reader.read().then(function (result) {
          if (result.done) {
            if (!reply) throw new Error("The agent could not answer.");
            if (hooks.onDone) hooks.onDone(reply, agent);
            return reply;
          }
          buffer += decoder.decode(result.value, { stream: true });
          var parts = buffer.split("\n\n");
          buffer = parts.pop() || "";
          for (var i = 0; i < parts.length; i++) parseSseChunk(parts[i], handleEvent);
          return pump();
        });
      }

      return pump();
    });
  }

  window.HarrisonChat = {
    matchLocal: matchLocal,
    send: send,
    faq: FAQ
  };
})();
