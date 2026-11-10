#!/usr/bin/env node
// Captures a business's current website as raw material for a redesign
// concept: screenshots (desktop + phone, first screen and full page), the real
// text, contacts, social links, colours, fonts and photos, from the homepage
// plus a few key inner pages (about / services / contact...).
//
// Usage:
//   node tools/capture_site.mjs <url> [--out .tmp/rebuild/<name>] [--pages 4] [--no-images]
//
// Output (in --out, default .tmp/rebuild/<host>):
//   desktop-fold.png, desktop-full.png, phone-fold.png, phone-full.png
//   content.json   everything extracted, machine-readable
//   content.md     the same, readable (feed this to the build)
//   assets/        downloaded photos and logo (skipped with --no-images)
//
// Playwright comes from saas/booking-platform/.playwright-cli (override with
// PLAYWRIGHT_DIR). One visit per page, sequential: a person browsing, not a crawl.
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PW_DIR = process.env.PLAYWRIGHT_DIR || path.join(ROOT, "saas/booking-platform/.playwright-cli");
const MAX_SHOT_HEIGHT = 8000;
const MAX_IMAGES = 20;
const MAX_IMAGE_BYTES = 5_000_000;

const PAGE_KEYWORDS = [
  /about|אודות|מי אנחנו|הסיפור/i,
  /service|שירות|טיפול|treatment|what we do|מה אנחנו/i,
  /contact|צור קשר|יצירת קשר|צרו קשר/i,
  /team|staff|צוות|הרופאים/i,
  /price|pricing|מחיר|תעריף/i,
  /faq|שאלות/i,
  /gallery|portfolio|גלריה|עבודות|פרויקטים/i,
];

function parseArgs(argv) {
  const args = { url: "", out: "", pages: 4, images: true };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") args.out = argv[++i];
    else if (a === "--pages") args.pages = Math.max(0, Number(argv[++i]) || 0);
    else if (a === "--no-images") args.images = false;
    else if (!a.startsWith("--")) args.url = a;
  }
  if (!args.url) {
    console.error("Usage: node tools/capture_site.mjs <url> [--out dir] [--pages 4] [--no-images]");
    process.exit(1);
  }
  if (!/^https?:\/\//i.test(args.url)) args.url = `https://${args.url}`;
  if (!args.out) {
    const host = new URL(args.url).hostname.replace(/^www\./, "");
    args.out = path.join(ROOT, ".tmp/rebuild", host);
  }
  return args;
}

async function loadPlaywright() {
  const require = createRequire(path.join(PW_DIR, "package.json"));
  const pw = await import(pathToFileURL(require.resolve("playwright")).href);
  return pw.chromium ? pw : pw.default;
}

// Scroll to the bottom and back so lazy-loaded images and sections render.
async function settle(page) {
  await page.waitForLoadState("load", { timeout: 15000 }).catch(() => {});
  await page.evaluate(async () => {
    const step = Math.max(400, window.innerHeight * 0.8);
    for (let y = 0; y < document.documentElement.scrollHeight && y < 30000; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 120));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(600);
}

async function shots(page, prefix, outDir) {
  await page.screenshot({ path: path.join(outDir, `${prefix}-fold.png`) });
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  const width = page.viewportSize().width;
  await page.screenshot({
    path: path.join(outDir, `${prefix}-full.png`),
    fullPage: true,
    clip: { x: 0, y: 0, width, height: Math.min(height, MAX_SHOT_HEIGHT) },
  });
  return height;
}

// Runs in the page: everything a rebuild needs to keep the business's real content.
function extract() {
  const clean = (s) => String(s || "").replace(/\s+/g, " ").trim();
  const uniq = (arr) => [...new Set(arr.filter(Boolean))];
  const abs = (href) => { try { return new URL(href, location.href).href; } catch { return ""; } };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  };

  const headings = uniq([...document.querySelectorAll("h1, h2, h3")].filter(visible)
    .map((h) => `${h.tagName.toLowerCase()}: ${clean(h.innerText)}`).filter((s) => s.length > 4)).slice(0, 80);
  const text = uniq([...document.querySelectorAll("p, li, blockquote, td, dd")].filter(visible)
    .filter((el) => !el.closest("nav, header nav, script, style"))
    .map((el) => clean(el.innerText)).filter((s) => s.length >= 25)).slice(0, 200);

  // <area> covers old image-map menus, where every link is a hotspot on one picture.
  const links = [...document.querySelectorAll("a[href], area[href]")].map((a) => ({
    text: clean(a.innerText || a.getAttribute("aria-label") || a.title || a.getAttribute("alt") || a.querySelector("img")?.alt),
    href: abs(a.getAttribute("href")),
  }));
  const navLinks = uniq([...document.querySelectorAll("nav a[href], header a[href]")]
    .map((a) => JSON.stringify({ text: clean(a.innerText), href: abs(a.getAttribute("href")) })))
    .map((s) => JSON.parse(s)).filter((l) => l.text).slice(0, 40);
  const sameSite = (href) => { try { return new URL(href).hostname.replace(/^www\./, "") === location.hostname.replace(/^www\./, ""); } catch { return false; } };
  const internal = uniq(links.filter((l) => sameSite(l.href) && !/\.(pdf|jpe?g|png|gif|webp|zip|docx?)(\?|$)/i.test(l.href))
    .map((l) => JSON.stringify({ text: l.text, href: l.href.split("#")[0] }))).map((s) => JSON.parse(s)).slice(0, 200);

  const bodyText = document.body ? document.body.innerText : "";
  const phones = uniq([
    ...links.filter((l) => l.href.startsWith("tel:")).map((l) => decodeURIComponent(l.href.slice(4))),
    // WhatsApp links are often the only contact on Israeli small-business sites.
    ...links.map((l) => l.href.match(/wa\.me\/(\d{9,15})|whatsapp\.com\/send\?phone=(\d{9,15})/)).filter(Boolean).map((m) => `+${m[1] || m[2]} (WhatsApp)`),
    ...(bodyText.match(/(?:\+972[-\s]?|0)(?:[23489]|5\d|7\d)[-\s]?\d{3}[-\s]?\d{4}|\*\d{4}/g) || []),
  ].map(clean)).slice(0, 10);
  const emails = uniq([
    ...links.filter((l) => l.href.startsWith("mailto:")).map((l) => l.href.slice(7).split("?")[0]),
    ...(bodyText.match(/[\w.+-]+@[\w-]+\.[\w.-]+/g) || []),
  ].map((e) => e.toLowerCase())).slice(0, 10);
  const socials = uniq(links.map((l) => l.href).filter((h) =>
    /facebook\.com|instagram\.com|wa\.me|whatsapp\.com|tiktok\.com|youtube\.com|linkedin\.com|waze\.com|twitter\.com|x\.com\//i.test(h))).slice(0, 20);

  const images = [];
  for (const img of document.querySelectorAll("img")) {
    const src = abs(img.currentSrc || img.src);
    if (!src || src.startsWith("data:")) continue;
    const hint = `${img.alt} ${img.className} ${img.id} ${src}`.toLowerCase();
    const logo = /logo/.test(hint);
    if (!logo && (img.naturalWidth < 200 || img.naturalHeight < 120)) continue;
    images.push({ src, alt: clean(img.alt), width: img.naturalWidth, height: img.naturalHeight, logo, kind: "img" });
  }
  for (const el of document.querySelectorAll("header, section, div, a")) {
    const r = el.getBoundingClientRect();
    if (r.width < 600 || r.height < 250) continue;
    const m = getComputedStyle(el).backgroundImage.match(/url\(["']?([^"')]+)["']?\)/);
    if (m && !m[1].startsWith("data:")) images.push({ src: abs(m[1]), alt: "", width: Math.round(r.width), height: Math.round(r.height), logo: false, kind: "background" });
  }
  const seen = new Set();
  const uniqImages = images.filter((i) => !seen.has(i.src) && seen.add(i.src)).slice(0, 60);

  // Brand colours: the most used non-grey colours on headings, links, buttons and bars.
  const counts = {};
  const grey = (c) => {
    const m = c.match(/\d+(\.\d+)?/g);
    if (!m) return true;
    const [r, g, b, a = 1] = m.map(Number);
    return a < 0.5 || (Math.max(r, g, b) - Math.min(r, g, b) < 18);
  };
  for (const el of document.querySelectorAll("h1, h2, h3, a, button, header, nav, footer, [class*=btn], [class*=button]")) {
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    for (const c of [cs.color, cs.backgroundColor]) if (!grey(c)) counts[c] = (counts[c] || 0) + 1;
  }
  const colors = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([c, n]) => ({ color: c, uses: n }));

  const meta = (name) => document.querySelector(`meta[name="${name}"], meta[property="${name}"]`)?.content || "";
  const footer = document.querySelector("footer");
  return {
    url: location.href,
    title: document.title,
    description: meta("description") || meta("og:description"),
    lang: document.documentElement.lang || "",
    dir: document.documentElement.dir || getComputedStyle(document.body).direction,
    generator: meta("generator"),
    fonts: { body: getComputedStyle(document.body).fontFamily, heading: (() => { const h = document.querySelector("h1, h2"); return h ? getComputedStyle(h).fontFamily : ""; })() },
    headings, text, navLinks, internal, phones, emails, socials, images: uniqImages, colors,
    footer: footer ? clean(footer.innerText).slice(0, 1500) : "",
  };
}

function pickInnerPages(home, limit) {
  const picked = [];
  for (const re of PAGE_KEYWORDS) {
    if (picked.length >= limit) break;
    const hit = home.internal.find((l) =>
      (re.test(l.text) || re.test(decodeURIComponent(l.href))) &&
      l.href.replace(/\/$/, "") !== home.url.replace(/\/$/, "") &&
      !picked.some((p) => p.href === l.href));
    if (hit) picked.push(hit);
  }
  return picked;
}

async function downloadImages(context, images, dir) {
  fs.mkdirSync(dir, { recursive: true });
  const ordered = [...images.filter((i) => i.logo), ...images.filter((i) => !i.logo)];
  let n = 0;
  for (const img of ordered) {
    if (n >= MAX_IMAGES) break;
    try {
      const resp = await context.request.get(img.src, { timeout: 15000 });
      if (!resp.ok()) continue;
      const type = resp.headers()["content-type"] || "";
      if (!type.startsWith("image/")) continue;
      const body = await resp.body();
      if (body.length > MAX_IMAGE_BYTES) continue;
      const ext = (type.split("/")[1] || "bin").split(";")[0].replace("jpeg", "jpg").replace("svg+xml", "svg");
      n++;
      const file = `${img.logo ? "logo" : "img"}-${String(n).padStart(2, "0")}.${ext}`;
      fs.writeFileSync(path.join(dir, file), body);
      img.file = `assets/${file}`;
    } catch { /* skip images that won't download */ }
  }
  return n;
}

function toMarkdown(data) {
  const h = data.home;
  const lines = [
    `# ${h.title || data.url}`,
    "",
    `- URL: ${h.url}`,
    `- Captured: ${data.captured_at}`,
    `- Language / direction: ${h.lang || "?"} / ${h.dir}`,
    h.generator ? `- Built with: ${h.generator}` : "",
    `- Fonts: body ${h.fonts.body}; headings ${h.fonts.heading}`,
    `- Page height: desktop ${data.heights.desktop}px, phone ${data.heights.phone}px`,
    `- Made for phones: ${data.phone_unfit ? "NO (shrunk or wider than the screen)" : "yes"}`,
    h.description ? `- Meta description: ${h.description}` : "",
    "",
    "## Contacts",
    `- Phones: ${h.phones.join(", ") || "none found"}`,
    `- Emails: ${h.emails.join(", ") || "none found"}`,
    `- Social / maps: ${h.socials.join(", ") || "none found"}`,
    "",
    "## Colours (most used, non-grey)",
    ...h.colors.map((c) => `- ${c.color} (${c.uses})`),
    "",
    "## Navigation",
    ...h.navLinks.map((l) => `- ${l.text} → ${l.href}`),
    "",
    "## Homepage headings",
    ...h.headings.map((s) => `- ${s}`),
    "",
    "## Homepage text",
    ...h.text.map((s) => `- ${s}`),
    "",
    "## Footer",
    h.footer || "(none)",
  ];
  for (const p of data.pages) {
    lines.push("", `## Page: ${p.title || p.url}`, `URL: ${p.url}`, "");
    if (p.error) { lines.push(`(could not open: ${p.error})`); continue; }
    lines.push(...p.headings.map((s) => `- ${s}`), "", ...p.text.map((s) => `- ${s}`));
  }
  lines.push("", "## Images");
  for (const i of h.images) lines.push(`- ${i.logo ? "[logo] " : ""}${i.file || "(not downloaded)"} ${i.width}x${i.height} ${i.alt ? `"${i.alt}" ` : ""}${i.src}`);
  return lines.filter((l) => l !== undefined).join("\n") + "\n";
}

const args = parseArgs(process.argv.slice(2));
fs.mkdirSync(args.out, { recursive: true });
const pw = await loadPlaywright();
const browser = await pw.chromium.launch();
const data = { url: args.url, captured_at: new Date().toISOString(), heights: {}, pages: [] };

try {
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "he-IL" });
  const page = await desktop.newPage();
  try {
    await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (e) {
    data.error = String(e.message).split("\n")[0];
    fs.writeFileSync(path.join(args.out, "content.json"), JSON.stringify(data, null, 2));
    console.error(`Could not open ${args.url}: ${data.error}`);
    process.exitCode = 2;
    throw e;
  }
  await settle(page);
  data.heights.desktop = await shots(page, "desktop", args.out);
  data.home = await page.evaluate(extract);

  for (const link of pickInnerPages(data.home, args.pages)) {
    try {
      await page.goto(link.href, { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.waitForLoadState("load", { timeout: 10000 }).catch(() => {});
      const p = await page.evaluate(extract);
      data.pages.push({ url: p.url, title: p.title, link_text: link.text, headings: p.headings, text: p.text, phones: p.phones, emails: p.emails });
    } catch (e) {
      data.pages.push({ url: link.href, link_text: link.text, error: String(e.message).split("\n")[0] });
    }
  }

  const phoneCtx = await browser.newContext({ ...pw.devices["iPhone 13"], locale: "he-IL" });
  const phone = await phoneCtx.newPage();
  await phone.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 });
  await settle(phone);
  data.heights.phone = await shots(phone, "phone", args.out);
  // Never made for phones: the browser lays it out at desktop width and shrinks
  // it (no viewport tag), or it's wider than the screen.
  data.phone_unfit = await phone.evaluate(() =>
    window.innerWidth > screen.width + 2 || document.documentElement.scrollWidth > window.innerWidth + 2);

  data.images_downloaded = args.images ? await downloadImages(desktop, data.home.images, path.join(args.out, "assets")) : 0;
  fs.writeFileSync(path.join(args.out, "content.json"), JSON.stringify(data, null, 2));
  fs.writeFileSync(path.join(args.out, "content.md"), toMarkdown(data));

  console.log(`Captured ${data.home.url}`);
  console.log(`  out: ${args.out}`);
  console.log(`  screenshots: desktop-fold, desktop-full (${data.heights.desktop}px), phone-fold, phone-full (${data.heights.phone}px)${data.phone_unfit ? "  [not made for phones: shrunk or wider than the screen]" : ""}`);
  console.log(`  homepage: ${data.home.headings.length} headings, ${data.home.text.length} text blocks, ${data.home.images.length} images (${data.images_downloaded} downloaded)`);
  console.log(`  inner pages: ${data.pages.map((p) => `${p.link_text || p.url}${p.error ? " (failed)" : ""}`).join(", ") || "none"}`);
  console.log(`  phones: ${data.home.phones.join(", ") || "none"}; emails: ${data.home.emails.join(", ") || "none"}`);
} catch (e) {
  if (!process.exitCode) {
    console.error(`Capture failed: ${String(e.message).split("\n")[0]}`);
    process.exitCode = 1;
  }
} finally {
  await browser.close();
}
