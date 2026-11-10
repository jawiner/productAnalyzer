// Minimal static file server with byte-range support for local previews.
// Usage: node tools/static_server.js <port> <directory>
const http = require('http');
const fs = require('fs');
const path = require('path');

const port = Number(process.argv[2]) || 8080;
const root = path.resolve(process.argv[3] || '.');

const types = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json', '.txt': 'text/plain; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
  '.ico': 'image/x-icon', '.mp4': 'video/mp4', '.webm': 'video/webm', '.mp3': 'audio/mpeg',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.pdf': 'application/pdf'
};

function statOrNull(file) {
  try { return fs.statSync(file); } catch (e) { return null; }
}

const server = http.createServer(function (req, res) {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let file = path.normalize(path.join(root, pathname));
    if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
    let st = statOrNull(file);
    if (st && st.isDirectory()) { file = path.join(file, 'index.html'); st = statOrNull(file); }
    if (!st || !st.isFile()) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('Not found'); }

    const size = st.size;
    let start = 0, end = size - 1, status = 200;
    const headers = {
      'Content-Type': types[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'no-cache'
    };
    const range = req.headers.range && /bytes=(\d*)-(\d*)/.exec(req.headers.range);
    if (range) {
      if (range[1] === '' && range[2] !== '') { start = Math.max(0, size - Number(range[2])); }
      else { if (range[1] !== '') start = Number(range[1]); if (range[2] !== '') end = Math.min(Number(range[2]), size - 1); }
      if (start > end || start >= size) { res.writeHead(416, { 'Content-Range': 'bytes */' + size }); return res.end(); }
      status = 206;
      headers['Content-Range'] = 'bytes ' + start + '-' + end + '/' + size;
    }
    headers['Content-Length'] = end - start + 1;
    res.writeHead(status, headers);
    if (req.method === 'HEAD') return res.end();

    const stream = fs.createReadStream(file, { start: start, end: end });
    stream.on('error', function () { res.destroy(); });
    res.on('close', function () { stream.destroy(); });
    stream.pipe(res);
  } catch (e) {
    try { res.writeHead(500); res.end('Server error'); } catch (_) {}
  }
});

server.on('clientError', function (err, socket) { try { socket.destroy(); } catch (e) {} });
process.on('uncaughtException', function (e) { console.error('uncaught:', e && e.message); });

server.listen(port, function () {
  console.log('Serving ' + root + ' at http://localhost:' + port + '/');
});
