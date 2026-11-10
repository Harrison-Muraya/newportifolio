(function () {
  var form = document.getElementById("agent-form");
  var log = document.getElementById("agent-log");
  var input = document.getElementById("agent-message");
  var status = document.getElementById("agent-status");
  if (!form || !log || !input || !window.HarrisonChat) return;

  var history = [];
  var sending = false;
  var chat = window.HarrisonChat;

  function addBubble(text, who) {
    var bubble = document.createElement("p");
    bubble.className = "agent-bubble agent-bubble-" + who;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (sending) return;
    var message = input.value.trim();
    if (!message) return;
    sending = true;
    input.disabled = true;
    form.querySelector("button").disabled = true;
    addBubble(message, "user");
    input.value = "";
    if (status) {
      status.innerHTML = '<span class="hm-typing" aria-hidden="true"><span></span><span></span><span></span></span>';
    }

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
            if (!botBubble) botBubble = addBubble(reply, "bot");
            else botBubble.textContent = reply;
            history.push({ role: "user", content: message });
            history.push({ role: "assistant", content: reply });
            history = history.slice(-12);
          }
        },
        form
      )
      .catch(function (err) {
        addBubble((err && err.message) || "The agent is not reachable right now.", "bot");
      })
      .finally(function () {
        sending = false;
        input.disabled = false;
        form.querySelector("button").disabled = false;
        if (status) status.textContent = "";
        input.focus();
      });
  });
})();
