// Legal pages: CSS already shows the right language for the hash (#en = English).
// This only keeps the tab title and the page's lang/dir in step with it.
(function () {
  function sync() {
    var en = location.hash === '#en' || location.hash.indexOf('#en-') === 0;
    var doc = document.querySelector('.doc[lang="' + (en ? 'en' : 'he') + '"]');
    if (!doc) return;
    document.documentElement.lang = en ? 'en' : 'he';
    document.documentElement.dir = en ? 'ltr' : 'rtl';
    if (doc.dataset.title) document.title = doc.dataset.title;
  }
  window.addEventListener('hashchange', sync);
  sync();
})();
