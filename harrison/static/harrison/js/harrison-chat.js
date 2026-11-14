(function () {
  // Canonical facts — must match agent conversation.CANONICAL wording.
  var FAQ = [
    {
      keys: ["full name"],
      reply: "Harrison Ng'ang'a Muraya."
    },
    {
      keys: ["who are you", "who is harrison", "wewe ni nani"],
      reply: "I'm Harrison Ng'ang'a Muraya — fullstack developer in Nairobi."
    },
    {
      keys: ["your email", "what is your email", "what's your email"],
      reply: "hezronmuraya9@gmail.com"
    },
    {
      keys: ["your phone", "phone number", "your number"],
      reply: "+254 726 688 832"
    },
    {
      keys: ["how do i contact", "contact you", "kukuwasiliana", "wasiliana", "reach you"],
      reply: "Email hezronmuraya9@gmail.com, call +254 726 688 832, or LinkedIn linkedin.com/in/muraya-harrison."
    },
    {
      keys: ["what have you built", "projects", "umejenga"],
      reply: "Flagship work: HostPro, KENA Coin, Ashkey RideDelivery, Sunne, Alpha Loans, and Harrison Agent. GitHub: github.com/Harrison-Muraya."
    },
    {
      keys: ["github"],
      reply: "github.com/Harrison-Muraya"
    },
    {
      keys: ["where do you work", "current job", "afripixel", "unafanya kazi"],
      reply: "Software developer at Afripixel Solution since July 2026."
    },
    {
      keys: ["are you available", "can i hire", "hire you", "freelance"],
      reply: "I take interesting builds — especially payments and APIs. Email hezronmuraya9@gmail.com with what you're shipping."
    }
  ];

  // Greetings + follow-ups go to the agent so history/canonical stay consistent.
  function matchLocal(message) {
    var lower = String(message || "").toLowerCase().trim().replace(/[!?.]+$/g, "");
    if (
      /^(hi+|hello|hey|sasa|mambo|niaje|habari|thanks|thank you|asante)$/.test(lower)
    ) {
      return null;
    }
    // "and your email?", "what about phone?" — never answer from FAQ substring keys.
    if (
      /^(and|also|what about|how about)\b/.test(lower) ||
      /^(and\s+)?(email|mail|phone|number|linkedin|github|stack)\s*$/.test(lower)
    ) {
      return null;
    }
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

    // Prefer the public agent URL from the browser (CORS). This avoids
    // PythonAnywhere free-account outbound blocks to a home IP.
    var endpoint = window.AGENT_CHAT_URL || "/chat/stream/";
    var direct = endpoint.indexOf("http") === 0;
    var headers = {
      "Content-Type": "application/json",
      Accept: "text/event-stream"
    };
    if (!direct) headers["X-CSRFToken"] = csrfToken(form);
    var payload = {
      message: message,
      history: history || []
    };
    if (direct) payload.stream = true;

    return fetch(endpoint, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
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
