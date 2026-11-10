// Lab terminal, fake STK push, and nothing that talks to a server.
(function () {
  var KNOWN = {
    help: true,
    projects: true,
    skills: true,
    contact: true,
    whoami: true,
    clear: true,
    about: true,
    experience: true,
    hire: true,
    'sudo hire harrison': true
  };

  function motionReduced() {
    return document.documentElement.getAttribute('data-motion') === 'reduce';
  }

  function init() {
    document.querySelectorAll('[data-terminal]').forEach(initTerminal);
    initStk();
  }

  function initTerminal(root) {
    var output = root.querySelector('[data-terminal-output]');
    var form = root.querySelector('[data-terminal-form]');
    var input = root.querySelector('[data-terminal-input]');
    var body = root.querySelector('[data-terminal-body]');
    if (!output || !form || !input) return;

    var history = [];
    var historyIndex = -1;
    var projects = [
      ['Harrison Agent', '/work/harrison-agent/'],
      ['HostPro', '/work/hostpro/'],
      ['KENA Coin', '/work/kena-coin/'],
      ['Ride-hailing and Delivery API', '/work/ride-hailing/'],
      ['Domain Management Platform', '/work/domain-platform/'],
      ['Blockchain Web Application', '/work/blockchain-app/'],
      ['API Platform & Docs', '/work/api-platform/'],
      ['Homeserver / Proxmox Cluster', '/work/homeserver/']
    ];

    function addLine(text) {
      var line = document.createElement('div');
      line.className = 'lab-line';
      line.textContent = text;
      output.appendChild(line);
      return line;
    }

    function addLinkLine(href, label, trailingText) {
      var line = document.createElement('div');
      line.className = 'lab-line';
      var link = document.createElement('a');
      link.href = href;
      link.textContent = label;
      line.appendChild(link);
      if (trailingText) line.appendChild(document.createTextNode(trailingText));
      output.appendChild(line);
      return line;
    }

    function run(command) {
      switch (command) {
        case 'help':
          ['help', 'about', 'projects', 'skills', 'experience', 'contact', 'whoami', 'clear', 'sudo hire harrison'].forEach(addLine);
          break;
        case 'about':
          addLine('Full stack developer in Nairobi. 2+ years on production Django applications, React frontends, Laravel, Flask, FastAPI, and PayPal, Chpter, and M-Pesa.');
          break;
        case 'projects':
          projects.forEach(function (project) { addLinkLine(project[1], project[0]); });
          break;
        case 'skills':
          addLine('Backend, Frontend, Payments, Infrastructure.');
          break;
        case 'experience':
          addLine('Software Developer, Afripixel Solution (Jul 2026 – present).');
          addLine('Software Developer, Smart Web Kenya (Jan 2025 – Jul 2025).');
          addLine('Software Developer Intern, Quest Website Developers Ltd (Jul 2024 – Jan 2025).');
          addLine('ICT & Network Admin, Estream East Africa Ltd (Oct 2023 – Jul 2024).');
          addLine('ICT Assistant, NSSF Embu (Apr 2022 – Aug 2022).');
          break;
        case 'contact':
          addLinkLine('mailto:hezronmuraya9@gmail.com', 'hezronmuraya9@gmail.com', ' · Nairobi, Kenya');
          addLinkLine('/about/#contact', 'Open the contact form');
          break;
        case 'whoami':
          addLine('A visitor, currently in the lab.');
          break;
        case 'clear':
          output.textContent = '';
          break;
        case 'hire':
        case 'sudo hire harrison':
          addLine('Access granted. Harrison is available for new projects.');
          addLinkLine('/about/#contact', 'Get in touch');
          break;
        default:
          addLine('Unknown command. Type help.');
      }
    }

    function submitCommand(raw) {
      var typed = raw.trim().replace(/\s+/g, ' ');
      if (!typed) return;
      var echo = document.createElement('div');
      echo.className = 'lab-line lab-echo';
      echo.textContent = '› ' + typed;
      output.appendChild(echo);
      var normalized = typed.toLowerCase();
      run(normalized);
      history.push(typed);
      historyIndex = history.length;
      input.value = '';
      root.scrollTop = root.scrollHeight;
      if (output.parentElement) output.parentElement.scrollTop = output.parentElement.scrollHeight;
      if (window.portfolioTrack) {
        window.portfolioTrack('terminal_command_executed', {
          command: KNOWN[normalized] ? normalized : 'unknown'
        });
      }
      if (!root.closest('#terminal-dialog') || !document.getElementById('terminal-dialog').hidden) {
        input.focus();
      }
    }

    addLine("Harrison's lab. Type help.");
    if (input.id === 'lab-input') input.focus();

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      submitCommand(input.value);
    });

    input.addEventListener('keydown', function (event) {
      if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return;
      if (!history.length) return;
      event.preventDefault();
      if (event.key === 'ArrowUp') {
        historyIndex = Math.max(0, historyIndex - 1);
      } else if (historyIndex >= history.length - 1) {
        historyIndex = history.length;
        input.value = '';
        return;
      } else {
        historyIndex += 1;
      }
      input.value = history[historyIndex] || '';
    });

    root.querySelectorAll('[data-command]').forEach(function (button) {
      button.addEventListener('click', function () {
        submitCommand(button.getAttribute('data-command') || '');
      });
    });

    var closeBtn = root.querySelector('[data-terminal-close]');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        var dialog = document.getElementById('terminal-dialog');
        if (root.closest('#terminal-dialog') && dialog) {
          dialog.hidden = true;
          document.body.classList.remove('modal-open');
          var opener = document.getElementById('palette-open');
          if (opener) opener.focus();
          return;
        }
        if (!body) return;
        body.hidden = !body.hidden;
        closeBtn.textContent = body.hidden ? 'Open' : 'Close';
        closeBtn.setAttribute('aria-expanded', body.hidden ? 'false' : 'true');
      });
    }
  }

  function initStk() {
    var form = document.getElementById('stk-form');
    var phoneInput = document.getElementById('stk-phone');
    var amountInput = document.getElementById('stk-amount');
    var steps = document.getElementById('stk-steps');
    if (!form || !phoneInput || !amountInput || !steps) return;

    var timers = [];
    var runId = 0;

    function cancelTimers() {
      timers.forEach(clearTimeout);
      timers = [];
    }

    function writeStep(text) {
      var item = document.createElement('li');
      item.textContent = text;
      steps.appendChild(item);
      return item;
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      cancelTimers();
      var current = ++runId;
      var phone = phoneInput.value.trim();
      var digits = phone.replace(/\D/g, '');
      if (digits.length < 9) {
        steps.textContent = '';
        writeStep('Use a phone number with at least 9 digits.');
        return;
      }
      var amountText = amountInput.value.trim();
      var amount = Number(amountText);
      if (amountText === '' || !Number.isFinite(amount) || amount < 1) {
        steps.textContent = '';
        writeStep('Enter an amount of at least 1.');
        return;
      }
      if (window.portfolioTrack) window.portfolioTrack('demo_started', { demo: 'stk' });

      var messages = [
        'Sending STK push for KES ' + amountText + ' to ' + phone,
        'Waiting for the PIN on the phone',
        'Payment accepted',
        'Nothing was charged. This is a demo.'
      ];
      steps.textContent = '';
      var active = null;

      function reveal(text, index) {
        if (current !== runId) return;
        if (active) {
          active.classList.remove('is-active');
          active.classList.add('is-done');
        }
        var item = writeStep(text);
        item.classList.add('is-active');
        active = item;
        if (index === messages.length - 1 && window.portfolioTrack) {
          window.portfolioTrack('demo_completed', { demo: 'stk' });
        }
      }

      var delay = motionReduced() ? 0 : 700;
      messages.forEach(function (text, index) {
        if (delay === 0) reveal(text, index);
        else timers.push(setTimeout(function () { reveal(text, index); }, index * delay));
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
