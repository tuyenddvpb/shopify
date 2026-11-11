/* VitalRay theme scripts */
/* VitalRay storefront effects: scroll reveal, number count-up, header shadow. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;

  function reveal(el) { el.classList.add('is-in'); }

  /* Stagger children inside a group */
  document.querySelectorAll('[data-vr-reveal-group]').forEach(function (group) {
    group.querySelectorAll('[data-vr-reveal]').forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i * 90, 450) + 'ms';
    });
  });

  var items = document.querySelectorAll('[data-vr-reveal]');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(reveal);
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { reveal(e.target); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
    /* Safety net: never leave content hidden */
    setTimeout(function () { items.forEach(reveal); }, 4000);
  }

  /* Count-up numbers: <span data-vr-count="660">660</span> */
  function countUp(el) {
    var target = parseFloat(el.getAttribute('data-vr-count'));
    if (isNaN(target)) return;
    var decimals = (el.getAttribute('data-vr-count').split('.')[1] || '').length;
    var start = null, dur = 1200;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(step); else el.textContent = el.getAttribute('data-vr-count');
    }
    requestAnimationFrame(step);
  }
  var counters = document.querySelectorAll('[data-vr-count]');
  if (!reduce && 'IntersectionObserver' in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { countUp(e.target); co.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { co.observe(el); });
  }

  /* Header shadow once the page is scrolled */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      root.classList.toggle('vr-scrolled', window.scrollY > 8);
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Bundle picker: sets the quantity sent by the product form */
  document.querySelectorAll('[data-vr-bundle]').forEach(function (box) {
    var info = box.closest('.product__info-container, .product') || document;
    function apply() {
      var checked = box.querySelector('input[name="vr-bundle"]:checked');
      var qty = checked ? checked.value : '1';
      box.querySelectorAll('.vr-bundle__opt').forEach(function (o) {
        o.classList.toggle('is-active', o.querySelector('input').checked);
      });
      info.querySelectorAll('product-form form[action*="/cart/add"]').forEach(function (form) {
        var input = form.querySelector('input[name="quantity"]');
        if (!input) {
          input = document.createElement('input');
          input.type = 'hidden'; input.name = 'quantity';
          form.appendChild(input);
        }
        input.value = qty;
      });
    }
    box.addEventListener('change', apply);
    apply();
    /* Dawn may re-render the buy box; re-apply after it does */
    setTimeout(apply, 1500);
  });

  /* FAQ accordion: smooth open/close */
  document.querySelectorAll('.vr-faq__item').forEach(function (d) {
    var summary = d.querySelector('summary');
    var body = d.querySelector('.vr-faq__answer');
    if (!summary || !body || reduce) return;
    summary.addEventListener('click', function (e) {
      e.preventDefault();
      if (d.open) {
        body.style.height = body.scrollHeight + 'px';
        requestAnimationFrame(function () { body.style.height = '0px'; });
        d.classList.remove('is-open');
        setTimeout(function () { d.open = false; body.style.height = ''; }, 300);
      } else {
        d.open = true;
        body.style.height = '0px';
        requestAnimationFrame(function () { body.style.height = body.scrollHeight + 'px'; d.classList.add('is-open'); });
        setTimeout(function () { body.style.height = ''; }, 320);
      }
    });
  });

  /* Timeline line fills as you scroll */
  var tracks = document.querySelectorAll('[data-vr-progress]');
  function progress() {
    var vh = window.innerHeight;
    tracks.forEach(function (t) {
      var r = t.getBoundingClientRect();
      var p = (vh * 0.65 - r.top) / r.height;
      t.style.setProperty('--vr-progress', Math.max(0, Math.min(1, p)).toFixed(3));
    });
  }
  if (tracks.length) {
    window.addEventListener('scroll', function () { requestAnimationFrame(progress); }, { passive: true });
    progress();
  }

  /* Video reviews: click-to-play with sound, one at a time, pause when scrolled away */
  var vcards = document.querySelectorAll('[data-vr-vcard]');
  if (vcards.length) {
    function stopCard(c) {
      var ov = c.querySelector('video');
      if (ov && !ov.paused) ov.pause();
      c.classList.remove('is-playing');
    }
    var vio = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (!e.isIntersecting) stopCard(e.target); });
    }, { threshold: 0.2 }) : null;
    vcards.forEach(function (card) {
      var v = card.querySelector('video');
      if (!v) return;
      v.removeAttribute('autoplay'); v.pause();
      v.muted = false; v.loop = false; v.setAttribute('playsinline', '');
      if (vio) vio.observe(card);
      v.addEventListener('ended', function () { card.classList.remove('is-playing'); v.currentTime = 0; });
      var media = card.querySelector('.vr-vcard__media');
      media.setAttribute('role', 'button');
      media.setAttribute('tabindex', '0');
      media.setAttribute('aria-label', 'Play video');
      function toggle() {
        if (v.paused) {
          vcards.forEach(function (c) { if (c !== card) stopCard(c); });
          v.muted = false;
          var p = v.play(); if (p && p.catch) p.catch(function () {});
          card.classList.add('is-playing');
          media.setAttribute('aria-label', 'Pause video');
        } else {
          v.pause(); card.classList.remove('is-playing');
          media.setAttribute('aria-label', 'Play video');
        }
      }
      media.addEventListener('click', toggle);
      media.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
  }

  /* Product gallery videos: autoplay muted + loop when scrolled into view */
  var mediaVideos = document.querySelectorAll('.product__media-list deferred-media, .product-media-modal deferred-media, .featured-product deferred-media');
  function prepTemplate(dm) {
    var tpl = dm.querySelector('template');
    var v = tpl && tpl.content.querySelector('video');
    if (!v) return false;
    v.muted = true;
    ['muted', 'playsinline', 'loop', 'autoplay'].forEach(function (a) { v.setAttribute(a, ''); });
    v.setAttribute('preload', 'auto');
    return true;
  }
  function startVideo(dm) {
    if (!dm.getAttribute('loaded') && typeof dm.loadContent === 'function') dm.loadContent(false);
    var v = dm.querySelector('video');
    if (!v) return;
    v.muted = true; v.loop = true; v.playsInline = true;
    var p = v.play(); if (p && p.catch) p.catch(function () {});
  }
  if (mediaVideos.length && !reduce && 'IntersectionObserver' in window) {
    var mio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var dm = e.target;
        if (e.isIntersecting) { startVideo(dm); }
        else { var v = dm.querySelector('video'); if (v) v.pause(); }
      });
    }, { threshold: 0.5 });
    mediaVideos.forEach(function (dm) {
      if (dm.closest('.product-media-modal')) return; /* lightbox keeps normal controls */
      if (prepTemplate(dm)) mio.observe(dm);
    });
  }

  /* Silent looping videos in feature/step cards: play only while visible */
  var autoVids = document.querySelectorAll('[data-vr-autoplay] video');
  autoVids.forEach(function (v) {
    v.muted = true; v.loop = true; v.playsInline = true;
    v.removeAttribute('controls'); v.setAttribute('playsinline', ''); v.setAttribute('muted', '');
  });
  if (autoVids.length && 'IntersectionObserver' in window) {
    var aio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting && !reduce) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        else { v.pause(); }
      });
    }, { threshold: 0.25 });
    autoVids.forEach(function (v) { aio.observe(v); });
  }

  /* Welcome popup: email signup → first-order code. Shown at most once a week; never again after signup. */
  (function () {
    var wp = document.querySelector('[data-vr-welcome]');
    if (!wp) return;
    var KEY = 'vrWelcome';
    var store = {
      get: function () { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } },
      set: function (v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} }
    };
    var state = store.get() || {};
    var done = wp.querySelector('[data-vr-welcome-done]');
    var hasError = !!wp.querySelector('.vr-wp__err');
    var lastFocus = null, isOpen = false;

    function open() {
      if (isOpen) return;
      isOpen = true; lastFocus = document.activeElement;
      wp.hidden = false; document.documentElement.style.overflow = 'hidden';
      var f = wp.querySelector('input[type=email], [data-vr-welcome-copy], .vr-wp__close');
      if (f) setTimeout(function () { f.focus(); }, 60);
    }
    function close() {
      wp.hidden = true; isOpen = false; document.documentElement.style.overflow = '';
      if (state.s !== 'subscribed') { state = { s: 'dismissed', t: Date.now() }; store.set(state); }
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    wp.querySelectorAll('[data-vr-welcome-close]').forEach(function (b) { b.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (isOpen && e.key === 'Escape') close(); });

    var form = wp.querySelector('form');
    if (form) form.addEventListener('submit', function () { state.pending = Date.now(); store.set(state); });

    var copy = wp.querySelector('[data-vr-welcome-copy]');
    if (copy) copy.addEventListener('click', function () {
      var code = wp.querySelector('[data-vr-welcome-code]').textContent.trim();
      var ok = function () { copy.textContent = 'Copied'; };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(ok, ok); else ok();
    });

    var justPosted = state.pending && Date.now() - state.pending < 10 * 60 * 1000;
    if (justPosted && done) { state = { s: 'subscribed', t: Date.now() }; store.set(state); open(); return; }
    if (justPosted && hasError) { delete state.pending; store.set(state); open(); return; }
    if (state.s === 'subscribed') return;
    if (state.s === 'dismissed' && Date.now() - state.t < 7 * 24 * 3600 * 1000) return;

    var delay = (parseInt(wp.getAttribute('data-delay'), 10) || 12) * 1000;
    var timer = setTimeout(open, delay);
    var onScroll = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      if (h > 0 && window.scrollY / h > 0.45) { window.removeEventListener('scroll', onScroll); clearTimeout(timer); open(); }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    document.addEventListener('mouseout', function (e) {
      if (!e.relatedTarget && e.clientY <= 0 && window.innerWidth >= 990) { clearTimeout(timer); open(); }
    });
  })();

  /* Delivery estimate: business-day ranges from data attributes, shown as dates */
  document.querySelectorAll('[data-vr-eta]').forEach(function (el) {
    function addBiz(d, n) {
      var r = new Date(d.getTime());
      while (n > 0) { r.setDate(r.getDate() + 1); var w = r.getDay(); if (w !== 0 && w !== 6) n--; }
      return r;
    }
    var fmt;
    try { fmt = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }); } catch (e) { return; }
    var f = function (d) { return fmt.format(d); };
    var now = new Date();
    var n = function (k) { return parseInt(el.getAttribute('data-' + k), 10) || 0; };
    var set = function (sel, txt) { var t = el.querySelector(sel); if (t) t.textContent = txt; };
    set('[data-vr-eta-today]', f(now));
    set('[data-vr-eta-ship]', f(addBiz(now, n('ship-min'))) + ' – ' + f(addBiz(now, n('ship-max'))));
    set('[data-vr-eta-arrive]', f(addBiz(now, n('arrive-min'))) + ' – ' + f(addBiz(now, n('arrive-max'))));
  });
})();

