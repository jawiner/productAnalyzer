// The watch page (/process): a big play button over the cover, the player's own controls once it
// plays, and the WhatsApp button stirs when the film ends. Without this script the page still
// works: the video keeps its native controls.
(function () {
  var video = document.getElementById('film');
  var play = document.querySelector('.play');
  if (!video || !play) return;
  var started = false;
  var start = function () {
    if (started) return;
    started = true;
    play.hidden = true;
    video.controls = true;
  };
  video.controls = false;
  play.hidden = false;
  play.addEventListener('click', function () {
    start();
    var p = video.play();
    if (p && p.catch) p.catch(function () {});
  });
  video.addEventListener('play', start);
  video.addEventListener('ended', function () {
    var cta = document.querySelector('.cta');
    if (cta) cta.classList.add('is-ready');
  });
})();
