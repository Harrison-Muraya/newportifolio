(function () {
  var ARCH = {
    visitor: {
      name: 'Visitor',
      copy: 'Someone using the Laravel and Livewire application.',
      links: ['app'],
      payload: ''
    },
    app: {
      name: 'Laravel & Livewire app',
      copy: 'Built with Laravel and Livewire. This is where payment requests and the payout workflow start.',
      links: ['visitor', 'mpesa', 'paypal', 'chpter', 'payout'],
      payload: ''
    },
    mpesa: {
      name: 'M-Pesa',
      copy: 'One of the payment APIs integrated at Smart Web Kenya, alongside PayPal and Chpter.',
      links: ['app', 'payout'],
      payload: '{\n  "note": "Simulated sample. Not sent.",\n  "Amount": "100",\n  "PhoneNumber": "2547XXXXXXXX",\n  "CallBackURL": "https://example.test/callback"\n}'
    },
    paypal: {
      name: 'PayPal',
      copy: 'One of the payment APIs integrated at Smart Web Kenya.',
      links: ['app'],
      payload: ''
    },
    chpter: {
      name: 'Chpter',
      copy: 'One of the payment APIs integrated at Smart Web Kenya.',
      links: ['app'],
      payload: ''
    },
    payout: {
      name: 'Payout workflow',
      copy: 'Payout workflows designed so funds can move on after a payment, including through M-Pesa.',
      links: ['app', 'mpesa'],
      payload: ''
    }
  };

  var API_EMPTY = 'Select an endpoint and run the demonstration.';
  var CHALLENGE_START = ['3', '1', '5', '2', '4'];

  function reduced() {
    return document.documentElement.getAttribute('data-motion') === 'reduce';
  }

  function setMotion(mode) {
    document.documentElement.setAttribute('data-motion', mode);
    try { localStorage.setItem('portfolio-motion', mode); } catch (error) {}
    var toggle = document.getElementById('motion-toggle');
    if (toggle) toggle.textContent = mode === 'reduce' ? 'Motion off' : 'Motion on';
    document.dispatchEvent(new CustomEvent('portfolio:motion'));
  }

  function initMotion() {
    var toggle = document.getElementById('motion-toggle');
    if (!document.documentElement.getAttribute('data-motion') && reduced()) {
      document.documentElement.setAttribute('data-motion', 'reduce');
    }
    if (toggle) {
      toggle.textContent = document.documentElement.getAttribute('data-motion') === 'reduce' ? 'Motion off' : 'Motion on';
      toggle.addEventListener('click', function () {
        setMotion(document.documentElement.getAttribute('data-motion') === 'reduce' ? 'full' : 'reduce');
      });
    }
  }

  function initProgress() {
    var bar = document.getElementById('scroll-progress');
    if (!bar) return;
    function paint() {
      var height = document.documentElement.scrollHeight - window.innerHeight;
      var value = height > 0 ? Math.min(1, window.scrollY / height) : 0;
      bar.style.transform = 'scaleX(' + value + ')';
    }
    paint();
    window.addEventListener('scroll', paint, { passive: true });
    window.addEventListener('resize', paint);
  }

  function initPointer() {
    return;
  }

  function initTilt() {}

  function initTracking() {
    document.addEventListener('click', function (event) {
      var link = event.target.closest('[data-track]');
      if (!link || !window.portfolioTrack) return;
      var name = link.getAttribute('data-track');
      if (name === 'project_opened') {
        window.portfolioTrack(name, { href: link.getAttribute('href') || '' });
      } else if (name === 'contact_clicked') {
        window.portfolioTrack(name, {});
      }
    });
  }

  function paletteItems() {
    return [
      { label: 'Home', href: '/', group: 'Pages' },
      { label: 'Work', href: '/work/', group: 'Pages' },
      { label: 'Lab', href: '/lab/', group: 'Pages' },
      { label: 'Chat', href: '/chat/', group: 'Pages' },
      { label: 'Ask Harrison', action: 'ask-harrison', group: 'Actions' },
      { label: 'About', href: '/about/', group: 'Pages' },
      { label: 'Contact', href: '/about/#contact', group: 'Pages' },
      { label: 'Harrison Agent', href: '/work/harrison-agent/', group: 'Projects' },
      { label: 'HostPro', href: '/work/hostpro/', group: 'Projects' },
      { label: 'KENA Coin', href: '/work/kena-coin/', group: 'Projects' },
      { label: 'Ride-hailing and Delivery API', href: '/work/ride-hailing/', group: 'Projects' },
      { label: 'Domain Management Platform', href: '/work/domain-platform/', group: 'Projects' },
      { label: 'Blockchain Web Application', href: '/work/blockchain-app/', group: 'Projects' },
      { label: 'API Platform & Docs', href: '/work/api-platform/', group: 'Projects' },
      { label: 'Homeserver / Proxmox Cluster', href: '/work/homeserver/', group: 'Projects' },
      { label: 'Open terminal', action: 'terminal', group: 'Actions' },
      { label: 'Toggle motion', action: 'motion', group: 'Actions' }
    ];
  }

  function initPalette() {
    var root = document.getElementById('command-palette');
    var opener = document.getElementById('palette-open');
    var input = document.getElementById('palette-input');
    var list = document.getElementById('palette-list');
    if (!root || !input || !list) return;

    var active = 0;
    var current = [];
    var lastFocus = null;

    function closePalette() {
      root.hidden = true;
      document.body.classList.remove('modal-open');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function render(query) {
      var needle = (query || '').trim().toLowerCase();
      current = paletteItems().filter(function (item) {
        return !needle || item.label.toLowerCase().indexOf(needle) !== -1 || item.group.toLowerCase().indexOf(needle) !== -1;
      });
      active = 0;
      list.textContent = '';
      current.forEach(function (item, index) {
        var li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.id = 'palette-option-' + index;
        li.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
        var button = document.createElement('button');
        button.type = 'button';
        button.textContent = item.label;
        var meta = document.createElement('span');
        meta.textContent = item.group;
        button.appendChild(meta);
        button.addEventListener('click', function () { choose(index); });
        li.appendChild(button);
        list.appendChild(li);
      });
      if (!current.length) {
        var empty = document.createElement('li');
        empty.textContent = 'No matches';
        list.appendChild(empty);
      }
      input.setAttribute('aria-activedescendant', current.length ? 'palette-option-0' : '');
    }

    function mark(index) {
      if (!current.length) return;
      active = (index + current.length) % current.length;
      list.querySelectorAll('[role="option"]').forEach(function (option, optionIndex) {
        option.setAttribute('aria-selected', optionIndex === active ? 'true' : 'false');
      });
      input.setAttribute('aria-activedescendant', 'palette-option-' + active);
      var selected = document.getElementById('palette-option-' + active);
      if (selected && selected.scrollIntoView) selected.scrollIntoView({ block: 'nearest' });
    }

    function choose(index) {
      var item = current[index];
      if (!item) return;
      closePalette();
      if (item.action === 'terminal') {
        var dialog = document.getElementById('terminal-dialog');
        if (!dialog) return;
        dialog.hidden = false;
        document.body.classList.add('modal-open');
        var field = dialog.querySelector('[data-terminal-input]');
        if (field) field.focus();
        return;
      }
      if (item.action === 'motion') {
        setMotion(document.documentElement.getAttribute('data-motion') === 'reduce' ? 'full' : 'reduce');
        return;
      }
      if (item.action === 'ask-harrison') {
        if (window.hmOpenAgent) window.hmOpenAgent();
        else window.location.href = '/chat/';
        return;
      }
      if (item.href) {
        if (item.group === 'Projects' && window.portfolioTrack) {
          window.portfolioTrack('project_opened', { href: item.href });
        }
        if (item.label === 'Contact' && window.portfolioTrack) {
          window.portfolioTrack('contact_clicked', {});
        }
        window.location.href = item.href;
      }
    }

    function openPalette() {
      lastFocus = document.activeElement;
      root.hidden = false;
      document.body.classList.add('modal-open');
      input.value = '';
      render('');
      input.focus();
    }

    if (opener) opener.addEventListener('click', openPalette);
    root.querySelectorAll('[data-close-palette]').forEach(function (node) {
      node.addEventListener('click', closePalette);
    });
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        mark(active + 1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        mark(active - 1);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        choose(active);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        closePalette();
      }
    });
    document.addEventListener('keydown', function (event) {
      var key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === 'k') {
        event.preventDefault();
        if (root.hidden) openPalette();
        else closePalette();
        return;
      }
      if (event.key === 'Escape' && !root.hidden) closePalette();
    });
    root.addEventListener('keydown', function (event) {
      if (event.key !== 'Tab' || root.hidden) return;
      var focusable = root.querySelectorAll('input, button');
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  function initTerminalDialog() {
    var dialog = document.getElementById('terminal-dialog');
    if (!dialog) return;
    dialog.addEventListener('click', function (event) {
      if (event.target !== dialog) return;
      dialog.hidden = true;
      document.body.classList.remove('modal-open');
    });
    dialog.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        dialog.hidden = true;
        document.body.classList.remove('modal-open');
      }
    });
  }

  function initArchitecture() {
    var diagram = document.getElementById('arch-diagram');
    if (!diagram) return;
    var name = document.getElementById('arch-name');
    var copy = document.getElementById('arch-copy');
    var payload = document.getElementById('arch-payload');
    var nodes = diagram.querySelectorAll('[data-node]');

    function clearNodes() {
      nodes.forEach(function (node) {
        node.classList.remove('is-selected', 'is-linked');
        node.setAttribute('aria-pressed', 'false');
      });
      if (name) name.textContent = 'Select a component';
      if (copy) copy.textContent = 'Choose a box to see how it connects. The list under the diagram says the same thing in text.';
      if (payload) payload.hidden = true;
    }

    function select(id) {
      var item = ARCH[id];
      if (!item) return;
      nodes.forEach(function (node) {
        var nodeId = node.getAttribute('data-node');
        var selected = nodeId === id;
        var linked = item.links.indexOf(nodeId) !== -1;
        node.classList.toggle('is-selected', selected);
        node.classList.toggle('is-linked', linked);
        node.setAttribute('aria-pressed', selected ? 'true' : 'false');
      });
      if (name) name.textContent = item.name;
      if (copy) copy.textContent = item.copy;
      if (payload) {
        payload.hidden = !item.payload;
        var code = payload.querySelector('code');
        if (code) code.textContent = item.payload;
      }
      if (window.portfolioTrack) window.portfolioTrack('architecture_component_opened', { component: id });
    }

    nodes.forEach(function (node) {
      node.addEventListener('click', function () { select(node.getAttribute('data-node')); });
    });
    var reset = document.getElementById('arch-reset');
    if (reset) reset.addEventListener('click', clearNodes);
  }

  function initApi() {
    var select = document.getElementById('api-endpoint');
    var output = document.getElementById('api-output');
    var run = document.getElementById('api-run');
    if (!select || !output || !run) return;

    function showFields() {
      document.querySelectorAll('[data-api-fields]').forEach(function (block) {
        block.hidden = block.getAttribute('data-api-fields') !== select.value;
      });
    }

    function write(data) {
      output.textContent = JSON.stringify(data, null, 2);
    }

    function payload(forceError) {
      var endpoint = select.value;
      if (endpoint === 'health') {
        if (forceError) return { simulated: true, error: 'service_unavailable' };
        return { simulated: true, status: 'ok', service: 'api-platform' };
      }
      if (endpoint === 'stk') {
        var phone = (document.getElementById('api-phone').value || '').replace(/\D/g, '');
        var amount = Number(document.getElementById('api-amount').value);
        if (forceError || phone.length < 9 || !Number.isFinite(amount) || amount < 1) {
          return { simulated: true, error: 'invalid_payment_request' };
        }
        return { simulated: true, status: 'accepted', amount: amount, phone: phone };
      }
      var domain = (document.getElementById('api-name').value || '').trim().toLowerCase();
      if (forceError || domain.length < 3) return { simulated: true, error: 'invalid_domain' };
      return { simulated: true, domain: domain, available: domain.indexOf('taken') === -1 };
    }

    select.addEventListener('change', showFields);
    showFields();
    run.addEventListener('click', function () {
      if (window.portfolioTrack) window.portfolioTrack('demo_started', { demo: 'api' });
      write(payload(false));
      if (window.portfolioTrack) window.portfolioTrack('demo_completed', { demo: 'api' });
    });
    document.getElementById('api-error').addEventListener('click', function () { write(payload(true)); });
    document.getElementById('api-reset').addEventListener('click', function () { output.textContent = API_EMPTY; });
  }

  function initChallenge() {
    var list = document.getElementById('challenge-list');
    var feedback = document.getElementById('challenge-feedback');
    if (!list || !feedback) return;
    var original = Array.prototype.map.call(list.children, function (item) { return item; });

    function order() {
      return Array.prototype.map.call(list.children, function (item) {
        return item.getAttribute('data-step');
      }).join('');
    }

    function reset() {
      original.forEach(function (item) { list.appendChild(item); });
      feedback.textContent = '';
    }

    list.addEventListener('click', function (event) {
      var button = event.target.closest('[data-move]');
      if (!button) return;
      var item = button.closest('li');
      if (!item) return;
      if (button.getAttribute('data-move') === 'up' && item.previousElementSibling) {
        list.insertBefore(item, item.previousElementSibling);
      } else if (button.getAttribute('data-move') === 'down' && item.nextElementSibling) {
        list.insertBefore(item.nextElementSibling, item);
      }
    });

    document.getElementById('challenge-check').addEventListener('click', function () {
      if (order() === '12345') {
        feedback.textContent = 'That order matches the flow: collect the details, send the STK push, wait for the PIN, receive the callback, then record the payout.';
      } else {
        feedback.textContent = 'Not yet. Start with the amount and phone, then the push, the PIN, the callback, and the payout record.';
      }
    });
    document.getElementById('challenge-reset').addEventListener('click', reset);
  }

  function initExperience() {
    var cards = document.querySelectorAll('.exp-timeline .exp-card');
    if (!cards.length || !('IntersectionObserver' in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) entry.target.classList.add('is-current');
      });
    }, { threshold: 0.4 });
    cards.forEach(function (card) { observer.observe(card); });
  }

  function initPageEnter() {
    var shells = document.querySelectorAll('.page-shell');
    if (!shells.length) return;
    if (reduced()) {
      shells.forEach(function (el) { el.classList.add('is-entered'); });
      return;
    }
    shells.forEach(function (el) { el.classList.add('is-entering'); });
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        shells.forEach(function (el, i) {
          el.style.transitionDelay = (i * 40) + 'ms';
          el.classList.remove('is-entering');
          el.classList.add('is-entered');
        });
      });
    });
  }

  function initWorkReveal() {
    var cards = document.querySelectorAll('.work-grid .work-card, .featured-row .work-card');
    if (!cards.length || !('IntersectionObserver' in window) || reduced()) {
      cards.forEach(function (card) { card.classList.add('is-shown'); });
      return;
    }
    cards.forEach(function (card) { card.classList.add('will-reveal'); });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-shown');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    cards.forEach(function (card, i) {
      card.style.transitionDelay = (i % 6) * 55 + 'ms';
      observer.observe(card);
    });
  }

  function init() {
    initMotion();
    initProgress();
    initPointer();
    initTilt();
    initTracking();
    initPalette();
    initTerminalDialog();
    initArchitecture();
    initApi();
    initChallenge();
    initExperience();
    initPageEnter();
    initWorkReveal();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
