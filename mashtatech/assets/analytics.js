/* Visitor counting for the Mashtech site (Vercel Web Analytics).
   No cookies, nothing stored in the browser, no personal profile.
   It runs on the live site only: local previews and files opened from disk stay silent.
   What is sent: page views, and these events:
     whatsapp / email  a contact link was pressed (from: which part of the page, about: which message)
     film              a film was opened (film: which one)
     section           a section of the home page came into view (id), once per visit */
(function () {
  var live = /(^|\.)mashtech\.co\.il$/.test(location.hostname);
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  window.mTrack = function (name, data) {
    if (!live) return;
    try { window.va('event', { name: name, data: data || {} }); } catch (e) {}
  };
  if (!live) return;

  var s = document.createElement('script');
  s.defer = true;
  s.src = '/_vercel/insights/script.js';
  document.head.appendChild(s);

  function where(el) {
    if (el.id === 'fab') return 'floating button';
    if (el.closest('#mobileMenu')) return 'menu';
    if (el.closest('#filmModal')) return 'film';
    var box = el.closest('section[id],footer[id],nav[id]');
    return box ? box.id : 'page';
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var kind = href.indexOf('wa.me/') > -1 ? 'whatsapp' : href.indexOf('mailto:') === 0 ? 'email' : '';
    if (kind) window.mTrack(kind, { from: where(a), about: a.getAttribute('data-wa') || '' });
  }, true);

  function watchSections() {
    if (!('IntersectionObserver' in window)) return;
    var seen = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var id = en.target.id;
        if (!en.isIntersecting || seen[id]) return;
        seen[id] = true;
        io.unobserve(en.target);
        window.mTrack('section', { id: id });
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    document.querySelectorAll('main section[id]').forEach(function (sec) {
      if (sec.id !== 'top') io.observe(sec);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watchSections);
  else watchSections();
})();
