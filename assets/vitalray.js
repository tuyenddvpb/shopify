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
})();
