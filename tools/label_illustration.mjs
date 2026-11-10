#!/usr/bin/env node
// Writes short handwritten labels (Hebrew or any language) and little hand-drawn
// arrows onto a generated illustration, so the words are always spelled right:
// image models garble Hebrew, the browser doesn't. Also crops (e.g. a 3:2
// render down to 16:9) and turns near-white paper (>= 246) into pure white.
//
// Usage:
//   node tools/label_illustration.mjs <spec.json>
//
// spec.json (paths relative to the spec file; coordinates in the cropped image):
//   {
//     "image": "assets/img-flood.png",
//     "out": "final/01-flood.png",
//     "crop": [0, 96, 1536, 864],            // optional [x, y, w, h]
//     "font": "Playpen Sans Hebrew",         // optional, any Google Font
//     "labels": [
//       { "text": "87 הודעות", "x": 250, "y": 190, "color": "red", "size": 38,
//         "rotate": -3, "arrow": [250, 215, 280, 290] }   // arrow: x1 y1 x2 y2
//     ]
//   }
// x/y is the centre of the label. color: red | orange | blue | black | any CSS colour.
//
// Playwright comes from saas/booking-platform/.playwright-cli (override with
// PLAYWRIGHT_DIR). Fonts load from Google Fonts; the run fails if the font doesn't.
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PW_DIR = process.env.PLAYWRIGHT_DIR || path.join(ROOT, "saas/booking-platform/.playwright-cli");
const COLORS = { red: "#e3342f", orange: "#f28a24", blue: "#2c6fd8", black: "#1b1b1b" };

async function loadPlaywright() {
  const require = createRequire(path.join(PW_DIR, "package.json"));
  const pw = await import(pathToFileURL(require.resolve("playwright")).href);
  return pw.chromium ? pw : pw.default;
}

const escapeHtml = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// A slightly bent stroke with a two-line head, like a quick pen arrow.
function arrowSvg([x1, y1, x2, y2], color) {
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
  const bend = len * 0.08;
  const cx = (x1 + x2) / 2 - (dy / len) * bend, cy = (y1 + y2) / 2 + (dx / len) * bend;
  const angle = Math.atan2(y2 - cy, x2 - cx), head = Math.min(14, len * 0.35);
  const hx = (a) => (x2 - head * Math.cos(angle + a)).toFixed(1);
  const hy = (a) => (y2 - head * Math.sin(angle + a)).toFixed(1);
  return `<path stroke="${color}" d="M${x1} ${y1} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${x2} ${y2}" />` +
    `<path stroke="${color}" d="M${hx(0.45)} ${hy(0.45)} L${x2} ${y2} L${hx(-0.45)} ${hy(-0.45)}" />`;
}

const specPath = process.argv[2];
if (!specPath) {
  console.error("Usage: node tools/label_illustration.mjs <spec.json>");
  process.exit(1);
}
const specDir = path.dirname(path.resolve(specPath));
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const font = spec.font || "Playpen Sans Hebrew";
const imageFile = path.resolve(specDir, spec.image);
const outFile = path.resolve(specDir, spec.out);
const imageData = `data:image/png;base64,${fs.readFileSync(imageFile).toString("base64")}`;

const labels = (spec.labels || []).map((l) => {
  const color = COLORS[l.color] || l.color || COLORS.black;
  const style = `left:${l.x}px;top:${l.y}px;color:${color};font-size:${l.size || 34}px;` +
    `transform:translate(-50%,-50%) rotate(${l.rotate || 0}deg)`;
  return { html: `<div class="label" dir="auto" style="${style}">${escapeHtml(l.text)}</div>`,
    arrow: l.arrow ? arrowSvg(l.arrow, color) : "" };
});

const html = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=${encodeURIComponent(font)}:wght@400;500&display=block">
<style>
  html,body{margin:0;background:#fff}
  #stage{position:relative;overflow:hidden}
  canvas{display:block}
  .label{position:absolute;white-space:nowrap;font-family:"${font}",cursive;font-weight:500;line-height:1}
  svg{position:absolute;inset:0}
  svg path{fill:none;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
</style></head><body><div id="stage"><canvas></canvas>
<svg>${labels.map((l) => l.arrow).join("")}</svg>${labels.map((l) => l.html).join("")}</div></body></html>`;

const pw = await loadPlaywright();
const browser = await pw.chromium.launch();
try {
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle" });
  const size = await page.evaluate(async ({ src, crop }) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    const [x, y, w, h] = crop || [0, 0, img.naturalWidth, img.naturalHeight];
    const canvas = document.querySelector("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(img, x, y, w, h, 0, 0, w, h);
    const px = ctx.getImageData(0, 0, w, h);
    for (let i = 0; i < px.data.length; i += 4) {
      if (px.data[i] >= 246 && px.data[i + 1] >= 246 && px.data[i + 2] >= 246) px.data[i] = px.data[i + 1] = px.data[i + 2] = 255;
    }
    ctx.putImageData(px, 0, 0);
    const stage = document.getElementById("stage");
    stage.style.width = `${w}px`;
    stage.style.height = `${h}px`;
    document.querySelector("svg").setAttribute("viewBox", `0 0 ${w} ${h}`);
    return { w, h };
  }, { src: imageData, crop: spec.crop });
  await page.setViewportSize({ width: size.w, height: size.h });
  const sample = (spec.labels || []).map((l) => l.text).join("");
  const fontOk = labels.length === 0 || await page.evaluate(async ({ f, text }) => {
    await document.fonts.load(`500 34px "${f}"`, text);
    await document.fonts.ready;
    return document.fonts.check(`500 34px "${f}"`, text);
  }, { f: font, text: sample });
  if (!fontOk) throw new Error(`Font "${font}" did not load (check the name on Google Fonts and the network).`);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  await page.locator("#stage").screenshot({ path: outFile });
  console.log(`Wrote ${path.relative(process.cwd(), outFile)} (${size.w}x${size.h}, ${labels.length} labels, ${font})`);
} finally {
  await browser.close();
}
