#!/usr/bin/env node
// Bakes the Mashtech site's script-rendered Hebrew text into mashtatech/index.html,
// so crawlers and AI agents that don't run JavaScript can read it, and generates
// mashtatech/llms.txt and mashtatech/pricing.md from the same text.
//
// The page's dictionary (the t() function in its inline script) stays the only
// source of truth: run this after changing FAQ, pricing, process or work copy.
//     node tools/bake_mashtech_static.mjs
// Safe to run repeatedly. In the browser the page's script empties these
// containers and renders them as before, so what visitors see doesn't change.
// Needs Playwright (from talentflow-promo/node_modules).
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const siteDir = join(repo, 'mashtatech');
const indexPath = join(siteDir, 'index.html');
const SITE = 'https://www.mashtech.co.il';
const today = new Date().toISOString().slice(0, 10);

const require = createRequire(join(repo, 'talentflow-promo', 'package.json'));
const { chromium } = require('playwright');

const browser = await chromium.launch();
let dict;
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(indexPath).href, { waitUntil: 'load' });
  dict = await page.evaluate(() => ({ tr: t(), work: workData.map((w) => w.key) }));
} finally {
  await browser.close();
}
const { tr, work } = dict;

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const plain = (html) => String(html).replace(/<\/p>\s*<p>/g, ' ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
const mark = (html) => `<!--baked-->${html}<!--/baked-->`;

const STEPS = [1, 2, 3, 4];
const TIERS = [1, 2, 3];
const PRODUCTS = [1, 2];
const productText = (n) =>
  [tr[`prod${n}_lede`], tr[`prod${n}_f1`], tr[`prod${n}_f2`], tr[`prod${n}_f3`], tr[`prod${n}_micro`]].join(' ');

const faq = tr.faq_items.map((i) => `<div class="faq-row"><h3>${esc(i.q)}</h3>${i.a}</div>`).join('');
const steps = STEPS.map((n) => `<div><h3>${esc(tr[`step${n}_title`])}</h3><p>${esc(tr[`step${n}_body`])}</p></div>`).join('');
const workList = work
  .map((k) => `<li><a href="${esc(tr[`${k}_url`])}" target="_blank" rel="noopener noreferrer">${esc(tr[`${k}_name`])} — ${esc(tr[`${k}_tag`])}</a></li>`)
  .join('');

let html = readFileSync(indexPath, 'utf8');

function bake(openTagPattern, closeTag, inner) {
  const re = new RegExp(`(${openTagPattern})(?:<!--baked-->[\\s\\S]*?<!--/baked-->)?(${closeTag})`);
  if (!re.test(html)) throw new Error(`container not found or not empty: ${openTagPattern}`);
  html = html.replace(re, (_, open, close) => `${open}${mark(inner)}${close}`);
}

bake('<div id="faqList"[^>]*>', '</div>', faq);
bake('<div id="stepsContainer"[^>]*>', '</div>', steps);
bake('<ul id="workAccessibleList"[^>]*>', '</ul>', workList);
for (const n of TIERS) {
  const key = `tier${n}_features`;
  bake(`<ul data-t-list="${key}"[^>]*>`, '</ul>', tr[key].map((f) => `<li>${esc(f)}</li>`).join(''));
}

// The FAQ's structured data follows the dictionary too, so the two can't disagree.
const ldRe = /(<script type="application\/ld\+json">)([\s\S]*?)(<\/script>)/;
const ld = JSON.parse(html.match(ldRe)[2]);
const faqLd = ld.find((x) => x['@type'] === 'FAQPage');
faqLd.mainEntity = tr.faq_items.map((i) => ({
  '@type': 'Question',
  name: i.q,
  acceptedAnswer: { '@type': 'Answer', text: plain(i.a) },
}));
// The studio's own products (section 02), as early-access software offers.
const biz = ld.find((x) => x['@type'] === 'ProfessionalService');
biz.makesOffer = biz.makesOffer
  .filter((o) => o.itemOffered['@type'] !== 'SoftwareApplication')
  .concat(PRODUCTS.map((n) => ({
    '@type': 'Offer',
    availability: 'https://schema.org/PreOrder',
    url: tr[`prod${n}_url`],
    itemOffered: {
      '@type': 'SoftwareApplication',
      name: tr[`prod${n}_name`],
      applicationCategory: 'BusinessApplication',
      description: productText(n),
    },
  })));
html = html.replace(ldRe, (_, a, __, c) => `${a}${JSON.stringify(ld).replace(/</g, '\\u003c')}${c}`);

writeFileSync(indexPath, html);

const services = [1, 2, 3, 4].map((n) => `- ${tr[`service${n}_title`]}: ${tr[`service${n}_body`]}`).join('\n');
const products = PRODUCTS.map((n) => `- ${tr[`prod${n}_name`]} (${tr.prod_status}): ${productText(n)} עמוד המוצר: ${tr[`prod${n}_url`]}`).join('\n');
const process = STEPS.map((n) => `${n}. ${tr[`step${n}_title`]}: ${tr[`step${n}_body`]}`).join('\n');
const plans = TIERS.map(
  (n) => `- ${tr[`tier${n}_name`]}: ${tr[`tier${n}_price`]} + ${tr[`tier${n}_monthly`]}. ${tr[`tier${n}_sub`]}`
).join('\n');
const projects = work.map((k) => `- [${tr[`${k}_name`]}](${tr[`${k}_url`]}): ${tr[`${k}_tag`]}`).join('\n');
const faqText = tr.faq_items.map((i) => `### ${i.q}\n\n${plain(i.a)}`).join('\n\n');

writeFileSync(
  join(siteDir, 'llms.txt'),
  `# Mashtech

> Mashtech הוא סטודיו של אדם אחד בישראל, בהובלת יניר משטא, לפיתוח אתרים, מערכות ווב, אוטומציות ופתרונות AI בהתאמה אישית לעסקים. החבילות מתחילות ב-${tr.tier1_price}.

Mashtech is a one-person software studio in Israel, led by Yanir Mashta, building websites, custom web systems, business automation and AI solutions for businesses. Packages start at ${tr.tier1_price}.

עודכן לאחרונה: ${today}

## שירותים

${services}

## מוצרים

${tr.products_sub}

${products}

## תמחור

${tr.pricing_sub}

${plans}

פירוט מלא: [pricing.md](${SITE}/pricing.md)

## תהליך העבודה

${process}

## עבודות

${projects}

## קשר

- אימייל: mashtatech@gmail.com
- וואטסאפ וטלפון: 054-996-1663
- אתר: ${SITE}/

## שאלות נפוצות

${faqText}
`
);

const planSections = TIERS.map(
  (n) => `## ${tr[`tier${n}_name`]}

- מחיר התחלתי: ${tr[`tier${n}_price`]}
- מנוי חודשי: ${tr[`tier${n}_monthly`]}
- למי זה מתאים: ${tr[`tier${n}_sub`]}
- כולל:
${tr[`tier${n}_features`].map((f) => `  - ${f}`).join('\n')}`
).join('\n\n');

writeFileSync(
  join(siteDir, 'pricing.md'),
  `# Pricing: Mashtech

Prices in Israeli shekels (ILS).
${tr.pricing_sub}

עודכן לאחרונה: ${today}

${planSections}

פרטים והזמנה: ${SITE}/#pricing
`
);

console.log(`baked ${tr.faq_items.length} FAQ answers, ${STEPS.length} steps, ${TIERS.length} price lists, ${work.length} projects, ${PRODUCTS.length} products; wrote llms.txt and pricing.md`);
