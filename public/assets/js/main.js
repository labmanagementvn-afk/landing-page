/* Vuong Gia Phu Solutions – tiny hash router, VI/EN switcher + UI helpers (no dependencies) */
(function () {
  'use strict';

  var DEFAULT_ROUTE = 'trang-chu';
  var ROUTES = ['trang-chu', 'cong-nghe', 'noi-that', 'chinh-sach-bao-mat'];

  var root = document.documentElement;
  var views = document.querySelectorAll('[data-view]');
  var navLinks = document.querySelectorAll('[data-route]');
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('site-nav');
  var navToggle = document.querySelector('.nav-toggle');
  var main = document.getElementById('main');
  var metaDescription = document.querySelector('meta[name="description"]');
  var canonical = document.querySelector('link[rel="canonical"]');
  var current = null;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Language ----------
  var EN = window.I18N_EN || {};
  // Vietnamese strings that only exist in JS (everything else is read from the HTML)
  var VI = {
    'js.title.trang-chu': 'Vuong Gia Phu Solutions – Giải pháp Công nghệ & Nội thất',
    'js.title.cong-nghe': 'Giải pháp Công nghệ – Vuong Gia Phu Solutions',
    'js.title.noi-that': 'Giải pháp Nội thất – Vuong Gia Phu Solutions',
    'js.title.chinh-sach-bao-mat': 'Chính sách bảo mật – Vuong Gia Phu Solutions',
    'js.description': metaDescription.getAttribute('content'),
    'js.menu.open': 'Mở menu',
    'js.menu.close': 'Đóng menu',
    'js.mail.name': 'Họ tên',
    'js.mail.phone': 'Số điện thoại',
    'js.mail.topic': 'Quan tâm'
  };
  var CANONICAL = { vi: canonical.href, en: canonical.href.replace(/\/?$/, '/') + '?lang=en' };
  var lang = 'vi';
  var originalHtml = new Map();   // element -> Vietnamese innerHTML
  var originalAttrs = new Map();  // element -> { attr: Vietnamese value }

  function t(key) {
    return lang === 'en' && EN[key] != null ? EN[key] : VI[key];
  }

  function readSavedLang() {
    var fromUrl = new URLSearchParams(location.search).get('lang');
    if (fromUrl === 'en' || fromUrl === 'vi') return fromUrl;
    try { return localStorage.getItem('lang') === 'en' ? 'en' : 'vi'; } catch (e) { return 'vi'; }
  }

  function applyLang(next) {
    lang = next;
    root.lang = next;

    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      if (!originalHtml.has(el)) originalHtml.set(el, el.innerHTML);
      var value = next === 'en' ? EN[el.getAttribute('data-i18n')] : null;
      var html = value != null ? value : originalHtml.get(el);
      if (el.innerHTML !== html) el.innerHTML = html;
    });

    document.querySelectorAll('[data-i18n-attr]').forEach(function (el) {
      if (!originalAttrs.has(el)) originalAttrs.set(el, {});
      var saved = originalAttrs.get(el);
      el.getAttribute('data-i18n-attr').split(';').forEach(function (pair) {
        var parts = pair.split(':');
        var attr = parts[0].trim();
        var key = parts[1].trim();
        if (!(attr in saved)) saved[attr] = el.getAttribute(attr);
        var value = next === 'en' ? EN[key] : null;
        el.setAttribute(attr, value != null ? value : saved[attr]);
      });
    });

    document.querySelectorAll('[data-set-lang]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(btn.getAttribute('data-set-lang') === next));
    });

    if (current) document.title = t('js.title.' + current);
    metaDescription.setAttribute('content', t('js.description'));
    canonical.href = CANONICAL[next];
    navToggle.setAttribute('aria-label', t(nav.classList.contains('open') ? 'js.menu.close' : 'js.menu.open'));
    root.classList.remove('i18n-pending');
  }

  function setLang(next) {
    if (next === lang) return;
    applyLang(next);
    try { localStorage.setItem('lang', next); } catch (e) { /* private mode: choice lasts this visit only */ }
    // Keep the URL shareable: ?lang=en for English, no parameter for Vietnamese
    var url = new URL(location.href);
    if (next === 'en') url.searchParams.set('lang', 'en'); else url.searchParams.delete('lang');
    history.replaceState(null, '', url);
  }

  document.querySelectorAll('[data-set-lang]').forEach(function (btn) {
    btn.addEventListener('click', function () { setLang(btn.getAttribute('data-set-lang')); });
  });

  // ---------- Router ----------
  function showView(name) {
    if (name === current) return;
    views.forEach(function (v) { v.hidden = v.getAttribute('data-view') !== name; });
    navLinks.forEach(function (a) {
      var active = a.getAttribute('data-route') === name;
      a.classList.toggle('active', active);
      if (active) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    current = name;
    document.title = t('js.title.' + name);
  }

  function scrollToEl(el) {
    requestAnimationFrame(function () {
      el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    });
  }

  // A privacy-policy anchor from the other language (#pp-3 <-> #pp-en-3) points to a hidden block
  function findTarget(id) {
    var target = document.getElementById(id);
    var block = target && target.closest('[data-lang]');
    if (block && block.getAttribute('data-lang') !== lang) {
      var twin = lang === 'en' ? id.replace(/^pp-(\d+)$/, 'pp-en-$1') : id.replace(/^pp-en-(\d+)$/, 'pp-$1');
      return document.getElementById(twin) || target;
    }
    return target;
  }

  function route() {
    var id = decodeURIComponent(location.hash.slice(1));

    // A top-level page
    if (!id || ROUTES.indexOf(id) !== -1) {
      showView(id || DEFAULT_ROUTE);
      window.scrollTo(0, 0);
      main.focus({ preventScroll: true });
      return;
    }

    // An anchor inside the page (e.g. #lien-he, #pp-3)
    var target = findTarget(id);
    if (!target) { showView(DEFAULT_ROUTE); window.scrollTo(0, 0); return; }

    var parentView = target.closest('[data-view]');
    if (parentView) showView(parentView.getAttribute('data-view'));
    else if (!current) showView(DEFAULT_ROUTE);
    scrollToEl(target);
  }

  applyLang(readSavedLang());
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
    navToggle.setAttribute('aria-label', t('js.menu.open'));
    navToggle.querySelector('use').setAttribute('href', '#i-menu');
  }
  navToggle.addEventListener('click', function () {
    var open = !nav.classList.contains('open');
    if (!open) return closeNav();
    nav.classList.add('open');
    navToggle.setAttribute('aria-expanded', 'true');
    navToggle.setAttribute('aria-label', t('js.menu.close'));
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
    var body = t('js.mail.name') + ': ' + name + '\n' + t('js.mail.phone') + ': ' + phone + '\n' +
      t('js.mail.topic') + ': ' + topic + '\n\n' + message;
    window.location.href = 'mailto:vuong@vuonggiaphu.com?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(body);
  });

  document.getElementById('year').textContent = new Date().getFullYear();
})();
