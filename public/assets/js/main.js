/* Vuong Gia Phu Solutions – tiny hash router + UI helpers (no dependencies) */
(function () {
  'use strict';

  var DEFAULT_ROUTE = 'trang-chu';
  var TITLES = {
    'trang-chu': 'Vuong Gia Phu Solutions – Giải pháp Công nghệ & Nội thất',
    'cong-nghe': 'Giải pháp Công nghệ – Vuong Gia Phu Solutions',
    'noi-that': 'Giải pháp Nội thất – Vuong Gia Phu Solutions',
    'chinh-sach-bao-mat': 'Chính sách bảo mật – Vuong Gia Phu Solutions'
  };

  var views = document.querySelectorAll('[data-view]');
  var navLinks = document.querySelectorAll('[data-route]');
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('site-nav');
  var navToggle = document.querySelector('.nav-toggle');
  var main = document.getElementById('main');
  var current = null;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function showView(name) {
    if (name === current) return false;
    views.forEach(function (v) { v.hidden = v.getAttribute('data-view') !== name; });
    navLinks.forEach(function (a) {
      var active = a.getAttribute('data-route') === name;
      a.classList.toggle('active', active);
      if (active) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    document.title = TITLES[name] || TITLES[DEFAULT_ROUTE];
    current = name;
    return true;
  }

  function scrollToEl(el) {
    requestAnimationFrame(function () {
      el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    });
  }

  function route() {
    var id = decodeURIComponent(location.hash.slice(1));

    // A top-level page
    if (!id || TITLES[id]) {
      showView(id || DEFAULT_ROUTE);
      window.scrollTo(0, 0);
      main.focus({ preventScroll: true });
      return;
    }

    // An anchor inside the page (e.g. #lien-he, #pp-3)
    var target = document.getElementById(id);
    if (!target) { showView(DEFAULT_ROUTE); window.scrollTo(0, 0); return; }

    var parentView = target.closest('[data-view]');
    if (parentView) showView(parentView.getAttribute('data-view'));
    else if (!current) showView(DEFAULT_ROUTE);
    scrollToEl(target);
  }

  window.addEventListener('hashchange', route);
  route();

  // Clicking a link to the hash we're already on should still scroll there
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    closeNav();
    if (a.getAttribute('href') === location.hash) {
      e.preventDefault();
      route();
    }
  });

  // ---------- Mobile navigation ----------
  function closeNav() {
    nav.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');
    navToggle.setAttribute('aria-label', 'Mở menu');
    navToggle.querySelector('use').setAttribute('href', '#i-menu');
  }
  navToggle.addEventListener('click', function () {
    var open = !nav.classList.contains('open');
    if (!open) return closeNav();
    nav.classList.add('open');
    navToggle.setAttribute('aria-expanded', 'true');
    navToggle.setAttribute('aria-label', 'Đóng menu');
    navToggle.querySelector('use').setAttribute('href', '#i-close');
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });

  // ---------- Header shadow + back-to-top ----------
  var toTop = document.querySelector('.fab-top');
  function onScroll() {
    var y = window.scrollY;
    header.classList.toggle('scrolled', y > 8);
    toTop.hidden = y < 600;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });

  // ---------- Lazy-load Google Maps ----------
  var mapFrame = document.querySelector('.map iframe[data-src]');
  if (mapFrame) {
    var loadMap = function () { mapFrame.src = mapFrame.getAttribute('data-src'); mapFrame.removeAttribute('data-src'); };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { loadMap(); io.disconnect(); }
      }, { rootMargin: '300px' });
      io.observe(mapFrame);
    } else {
      loadMap();
    }
  }

  // ---------- Contact form -> mailto ----------
  var form = document.getElementById('contact-form');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var data = new FormData(form);
    var name = (data.get('name') || '').trim();
    var phone = (data.get('phone') || '').trim();
    var topic = data.get('topic');
    var message = (data.get('message') || '').trim();
    var error = form.querySelector('.form-error');

    if (!name || !phone || !message) { error.hidden = false; return; }
    error.hidden = true;

    var subject = '[Website] ' + topic + ' – ' + name;
    var body = 'Họ tên: ' + name + '\nSố điện thoại: ' + phone + '\nQuan tâm: ' + topic + '\n\n' + message;
    window.location.href = 'mailto:vuong@vuonggiaphu.com?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(body);
  });

  document.getElementById('year').textContent = new Date().getFullYear();
})();
