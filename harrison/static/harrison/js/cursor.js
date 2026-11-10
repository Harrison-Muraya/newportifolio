/* Cursor interactions:
 * 1. Anchor dot
 * 2. Trailing ring
 * 3. Velocity stretch
 * 4. Context label
 * 5. Magnetic controls
 * 6. Card tilt and sheen
 * 7. Photo lens
 * 8. Letter magnet
 * 9. Five-dot trail
 * 10. Invert over dark
 * 11. Click ripple
 * 12. Edge light
 * 13. Skill repel
 * 14. Live coordinates
 */
(function () {
  var TRAIL_EASE = [0.35, 0.28, 0.22, 0.16, 0.12];
  var RING_EASE = 0.18;
  var MAGNET_PULL = 0.22;
  var MAGNET_MAX = 8;
  var LETTER_RADIUS = 90;
  var LETTER_PUSH = 7;
  var SKILL_RADIUS = 50;
  var SKILL_PUSH = 6;
  var RIPPLE_CAP = 4;

  function reduced() {
    return document.documentElement.getAttribute('data-motion') === 'reduce';
  }

  function finePointer() {
    return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  }

  function active() {
    return finePointer() && !reduced();
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function closest(target, selector) {
    var node = target;
    if (node && node.nodeType === 3) node = node.parentElement;
    if (!node || typeof node.closest !== 'function') return null;
    return node.closest(selector);
  }

  function place(el, px, py) {
    if (!el) return;
    el.style.transform = 'translate3d(' + px + 'px,' + py + 'px,0) translate(-50%,-50%)';
  }

  function edgeFor(el, event) {
    var rect = el.getBoundingClientRect();
    var ex = event.clientX - rect.left;
    var ey = event.clientY - rect.top;
    var left = Math.abs(ex);
    var right = Math.abs(rect.width - ex);
    var top = Math.abs(ey);
    var bottom = Math.abs(rect.height - ey);
    var min = Math.min(left, right, top, bottom);
    if (min === top) return 'top';
    if (min === bottom) return 'bottom';
    if (min === right) return 'right';
    return 'left';
  }

  function wrapHeroName() {
    var name = document.querySelector('.hero-name');
    if (!name || name.getAttribute('data-letters') === 'on') return;
    var readable = (name.innerText || name.textContent || '').replace(/\s+/g, ' ').trim();
    if (readable) name.setAttribute('aria-label', readable);
    var texts = [];
    var walker = document.createTreeWalker(name, NodeFilter.SHOW_TEXT, null);
    var current;
    while ((current = walker.nextNode())) texts.push(current);
    texts.forEach(function (textNode) {
      var raw = textNode.nodeValue || '';
      if (!raw.trim()) {
        if (textNode.parentNode) textNode.parentNode.removeChild(textNode);
        return;
      }
      var value = raw.replace(/\s+/g, ' ').trim();
      var frag = document.createDocumentFragment();
      for (var i = 0; i < value.length; i++) {
        var ch = value.charAt(i);
        if (ch === ' ') {
          frag.appendChild(document.createTextNode(' '));
          continue;
        }
        var span = document.createElement('span');
        span.className = 'cursor-letter';
        span.textContent = ch;
        frag.appendChild(span);
      }
      textNode.parentNode.replaceChild(frag, textNode);
    });
    name.setAttribute('data-letters', 'on');
  }

  function initCursor() {
    var root = document.getElementById('cursor');
    if (!root || root.getAttribute('data-ready') === 'on') return;
    root.setAttribute('data-ready', 'on');

    var ring = root.querySelector('.cursor-ring');
    var dot = root.querySelector('.cursor-dot');
    var label = root.querySelector('.cursor-label');
    var coords = root.querySelector('.cursor-coords');
    if (!coords) {
      coords = document.createElement('span');
      coords.className = 'cursor-coords';
      coords.setAttribute('aria-hidden', 'true');
      root.appendChild(coords);
    }

    var trails = Array.prototype.slice.call(root.querySelectorAll('.cursor-trail'));
    while (trails.length < 5) {
      var trail = document.createElement('span');
      trail.className = 'cursor-trail';
      trail.setAttribute('data-index', String(trails.length));
      trail.setAttribute('aria-hidden', 'true');
      if (ring) root.insertBefore(trail, ring);
      else root.appendChild(trail);
      trails.push(trail);
    }
    trails = trails.slice(0, 5);

    var x = window.innerWidth / 2;
    var y = window.innerHeight / 2;
    var rx = x;
    var ry = y;
    var vx = 0;
    var vy = 0;
    var stretchX = 1;
    var stretchY = 1;
    var running = false;
    var primed = false;
    var lettersHot = false;
    var skillsHot = false;
    var letters = [];
    var pills = [];
    var trailPos = trails.map(function () { return { x: x, y: y }; });

    wrapHeroName();
    letters = Array.prototype.slice.call(document.querySelectorAll('.hero-name .cursor-letter'));
    pills = Array.prototype.slice.call(document.querySelectorAll('.skill-pill'));

    function contextLabel(target) {
      if (closest(target, 'a[href^="mailto:"]')) return 'Mail';
      if (closest(target, '#palette-open')) return 'Search';
      if (closest(target, '#lab-terminal, #stk-demo, .arch-node')) return 'Play';
      if (closest(target, 'a[target="_blank"]')) return 'View';
      if (closest(target, '.work-card')) return 'Open';
      return '';
    }

    function resetLetters() {
      letters.forEach(function (span) {
        span.style.transform = '';
        span._mx = 0;
        span._my = 0;
      });
    }

    function resetSkills() {
      pills.forEach(function (pill) {
        pill.style.transform = '';
        pill._mx = 0;
        pill._my = 0;
      });
    }

    function resetAll() {
      document.querySelectorAll('.btn-hero-primary, .btn-hero-secondary, .work-card').forEach(function (el) {
        el.classList.remove('is-tracking');
        el.style.removeProperty('--shift-x');
        el.style.removeProperty('--shift-y');
        el.style.removeProperty('--rx');
        el.style.removeProperty('--ry');
        el.style.removeProperty('--sx');
        el.style.removeProperty('--sy');
        el.removeAttribute('data-edge');
      });
      document.querySelectorAll('.hero-photo-frame img').forEach(function (img) {
        img.style.transform = '';
        img.style.transformOrigin = '';
      });
      resetLetters();
      resetSkills();
      lettersHot = false;
      skillsHot = false;
      root.classList.remove('is-active', 'is-invert', 'is-coords', 'is-down', 'is-hidden');
      if (label) label.textContent = '';
      if (coords) coords.textContent = '';
      root.querySelectorAll('.cursor-ripple').forEach(function (node) {
        if (node.parentNode) node.parentNode.removeChild(node);
      });
    }

    function pushFromPointer(el, radius, maxPush) {
      var appliedX = el._mx || 0;
      var appliedY = el._my || 0;
      var rect = el.getBoundingClientRect();
      var cx = rect.left + rect.width / 2 - appliedX;
      var cy = rect.top + rect.height / 2 - appliedY;
      var dx = cx - x;
      var dy = cy - y;
      var dist = Math.hypot(dx, dy);
      if (dist < radius && dist > 0.5) {
        var push = (1 - dist / radius) * maxPush;
        el._mx = (dx / dist) * push;
        el._my = (dy / dist) * push;
        el.style.transform = 'translate3d(' + el._mx.toFixed(2) + 'px,' + el._my.toFixed(2) + 'px,0)';
      } else if (el._mx || el._my) {
        el._mx = 0;
        el._my = 0;
        el.style.transform = '';
      }
    }

    function tick() {
      if (!active()) {
        running = false;
        return;
      }
      rx += (x - rx) * RING_EASE;
      ry += (y - ry) * RING_EASE;

      var ax = Math.min(0.65, Math.abs(vx) * 0.04);
      var ay = Math.min(0.65, Math.abs(vy) * 0.04);
      var targetSX = 1 + ax;
      var targetSY = 1 + ay;
      if (ax > ay) targetSY = Math.max(0.82, targetSY - ax * 0.45);
      else targetSX = Math.max(0.82, targetSX - ay * 0.45);
      targetSX = clamp(targetSX, 0.8, 1.65);
      targetSY = clamp(targetSY, 0.8, 1.65);
      stretchX += (targetSX - stretchX) * 0.22;
      stretchY += (targetSY - stretchY) * 0.22;
      vx *= 0.7;
      vy *= 0.7;

      place(dot, x, y);
      if (ring) {
        ring.style.transform = 'translate3d(' + rx.toFixed(2) + 'px,' + ry.toFixed(2) + 'px,0) translate(-50%,-50%) scale(' + stretchX.toFixed(3) + ',' + stretchY.toFixed(3) + ')';
      }
      if (label) {
        label.style.transform = 'translate3d(' + rx.toFixed(2) + 'px,' + (ry + 34).toFixed(2) + 'px,0) translate(-50%,0)';
      }
      if (coords) coords.style.transform = '';

      var leadX = x;
      var leadY = y;
      for (var i = 0; i < trails.length; i++) {
        var pos = trailPos[i];
        var ease = TRAIL_EASE[i] || 0.12;
        pos.x += (leadX - pos.x) * ease;
        pos.y += (leadY - pos.y) * ease;
        place(trails[i], pos.x, pos.y);
        leadX = pos.x;
        leadY = pos.y;
      }

      if (lettersHot) {
        letters.forEach(function (span) { pushFromPointer(span, LETTER_RADIUS, LETTER_PUSH); });
      }
      if (skillsHot) {
        pills.forEach(function (pill) { pushFromPointer(pill, SKILL_RADIUS, SKILL_PUSH); });
      }

      requestAnimationFrame(tick);
    }

    function enable() {
      if (!active()) {
        delete document.documentElement.dataset.pointer;
        root.hidden = true;
        running = false;
        resetAll();
        return;
      }
      document.documentElement.dataset.pointer = 'on';
      root.hidden = !primed;
      if (!running) {
        running = true;
        requestAnimationFrame(tick);
      }
    }

    function onMove(event) {
      if (!active() || event.pointerType === 'touch') return;
      var nextX = event.clientX;
      var nextY = event.clientY;
      if (!primed) {
        primed = true;
        x = nextX;
        y = nextY;
        rx = nextX;
        ry = nextY;
        vx = 0;
        vy = 0;
        trailPos.forEach(function (pos) {
          pos.x = nextX;
          pos.y = nextY;
        });
        root.hidden = false;
      } else {
        vx = clamp(nextX - x, -90, 90);
        vy = clamp(nextY - y, -90, 90);
        x = nextX;
        y = nextY;
      }
      place(dot, x, y);

      var target = event.target;
      var typing = !!closest(target, 'input, textarea, select');
      var modal = document.body.classList.contains('modal-open');
      var hide = typing || modal;
      root.classList.toggle('is-hidden', hide);

      var text = hide ? '' : contextLabel(target);
      if (label) label.textContent = text;
      root.classList.toggle('is-active', text !== '');
      root.classList.toggle('is-invert', !hide && !!closest(target, '[data-terminal]'));

      var hero = document.getElementById('hero');
      var inHero = !!closest(target, '#hero');
      if (hero && inHero) {
        var bounds = hero.getBoundingClientRect();
        hero.style.setProperty('--mx', (x - bounds.left) + 'px');
        hero.style.setProperty('--my', (y - bounds.top) + 'px');
      }
      if (inHero) lettersHot = true;
      else if (lettersHot) {
        lettersHot = false;
        resetLetters();
      }

      var showCoords = (inHero || !!closest(target, '#lab')) && !hide;
      root.classList.toggle('is-coords', showCoords);
      if (coords) {
        coords.textContent = showCoords ? 'x ' + Math.round(x) + '   y ' + Math.round(y) : '';
      }

      var inSkills = !!closest(target, '.skills-section');
      if (inSkills) skillsHot = true;
      else if (skillsHot) {
        skillsHot = false;
        resetSkills();
      }

      if (!running) {
        running = true;
        requestAnimationFrame(tick);
      }
    }

    function removeNode(node) {
      if (node.parentNode) node.parentNode.removeChild(node);
    }

    function onDown(event) {
      if (!active() || event.pointerType === 'touch') return;
      root.classList.add('is-down');
      if (root.querySelectorAll('.cursor-ripple').length >= RIPPLE_CAP) return;
      var ripple = document.createElement('span');
      ripple.className = 'cursor-ripple';
      ripple.setAttribute('aria-hidden', 'true');
      ripple.style.left = event.clientX + 'px';
      ripple.style.top = event.clientY + 'px';
      root.appendChild(ripple);
      ripple.addEventListener('animationend', function () { removeNode(ripple); });
      window.setTimeout(function () { removeNode(ripple); }, 500);
    }

    document.addEventListener('pointermove', onMove, { passive: true });
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('pointerup', function () { root.classList.remove('is-down'); });
    document.addEventListener('pointercancel', function () { root.classList.remove('is-down'); });
    document.addEventListener('portfolio:motion', enable);

    var media = window.matchMedia('(hover: hover) and (pointer: fine)');
    if (media.addEventListener) media.addEventListener('change', enable);
    else if (media.addListener) media.addListener(enable);

    document.querySelectorAll('.btn-hero-primary, .btn-hero-secondary').forEach(function (el) {
      el.addEventListener('pointermove', function (event) {
        if (!active() || event.pointerType === 'touch') return;
        var rect = el.getBoundingClientRect();
        var dx = event.clientX - (rect.left + rect.width / 2);
        var dy = event.clientY - (rect.top + rect.height / 2);
        el.classList.add('is-tracking');
        el.style.setProperty('--shift-x', clamp(dx * MAGNET_PULL, -MAGNET_MAX, MAGNET_MAX).toFixed(2) + 'px');
        el.style.setProperty('--shift-y', clamp(dy * MAGNET_PULL, -MAGNET_MAX, MAGNET_MAX).toFixed(2) + 'px');
      });
      el.addEventListener('pointerleave', function () {
        el.classList.remove('is-tracking');
        el.style.removeProperty('--shift-x');
        el.style.removeProperty('--shift-y');
      });
    });

    document.querySelectorAll('.work-card').forEach(function (el) {
      el.addEventListener('pointerenter', function (event) {
        if (!active() || event.pointerType === 'touch') return;
        el.setAttribute('data-edge', edgeFor(el, event));
      });
      el.addEventListener('pointermove', function (event) {
        if (!active() || event.pointerType === 'touch') return;
        var rect = el.getBoundingClientRect();
        var width = rect.width || 1;
        var height = rect.height || 1;
        var px = clamp((event.clientX - rect.left) / width, 0, 1);
        var py = clamp((event.clientY - rect.top) / height, 0, 1);
        var dx = event.clientX - (rect.left + width / 2);
        var dy = event.clientY - (rect.top + height / 2);
        el.classList.add('is-tracking');
        el.style.setProperty('--sx', (px * 100).toFixed(1) + '%');
        el.style.setProperty('--sy', (py * 100).toFixed(1) + '%');
        el.style.setProperty('--shift-x', clamp(dx * 0.06, -6, 6).toFixed(2) + 'px');
        el.style.setProperty('--shift-y', clamp(dy * 0.06, -6, 6).toFixed(2) + 'px');
        el.style.setProperty('--rx', ((py - 0.5) * -6).toFixed(2) + 'deg');
        el.style.setProperty('--ry', ((px - 0.5) * 6).toFixed(2) + 'deg');
      });
      el.addEventListener('pointerleave', function () {
        el.classList.remove('is-tracking');
        el.style.removeProperty('--rx');
        el.style.removeProperty('--ry');
        el.style.removeProperty('--sx');
        el.style.removeProperty('--sy');
        el.style.removeProperty('--shift-x');
        el.style.removeProperty('--shift-y');
        el.removeAttribute('data-edge');
      });
    });

    document.querySelectorAll('.hero-photo-frame').forEach(function (frame) {
      var img = frame.querySelector('img');
      if (!img) return;
      frame.addEventListener('pointermove', function (event) {
        if (!active() || event.pointerType === 'touch') return;
        var rect = frame.getBoundingClientRect();
        var width = rect.width || 1;
        var height = rect.height || 1;
        var px = clamp((event.clientX - rect.left) / width, 0, 1);
        var py = clamp((event.clientY - rect.top) / height, 0, 1);
        var dist = Math.hypot(px - 0.5, py - 0.5);
        var scale = Math.min(1.06, 1.02 + (0.5 - Math.min(dist, 0.5)) * 0.08);
        img.style.transformOrigin = (px * 100).toFixed(1) + '% ' + (py * 100).toFixed(1) + '%';
        img.style.transform = 'scale(' + scale.toFixed(3) + ')';
      });
      frame.addEventListener('pointerleave', function () {
        img.style.transform = '';
        img.style.transformOrigin = '';
      });
    });

    enable();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initCursor);
  else initCursor();
})();
