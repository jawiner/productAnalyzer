# Workflow: Rebuild Their Site (redesign-preview outreach)

## Objective
Land web-design clients by leading with value: find local businesses whose website is
dated, build **one** strong concept of their own site, put it on a live preview link, and
send the owner a short personal message with the link. The owner sees the result, not a
promise. Quality of fit beats volume every time.

## Ground rules (read before anything else)
- **Small numbers.** A few concepts a week, for businesses you'd genuinely want as
  clients. Never generate sites for a whole scan.
- **The user sends every message, one by one.** The agent drafts; it never sends emails,
  never fills contact forms, never DMs. Bulk or automated pitches are spam: they get
  accounts banned and domains blacklisted, and Israel's anti-spam law (Communications Law
  §30A) allows up to ₪1,000 per unsolicited ad message without proof of harm. A phone call
  first is the safest opening.
- **Find with Mapflow, not a scraper.** Mapflow's scan uses Google's official Places API.
  Scraping Google Maps (e.g. `gosom/google-maps-scraper`) breaks Google's terms. Don't
  install it.
- **Ask the user before publishing.** Deploying a concept creates a public URL. Ask before
  every deploy, and before taking one down.
- **A concept is never mistaken for the real site.** Every page is noindexed and carries a
  "concept by Mashtech, not the official site" ribbon. Never use their domain.
- **Only their real content.** Business name, services, phone, address, hours, their own
  photos and logo. Never invent reviews, awards, staff, prices or years in business.

## Inputs
- A lead in Mapflow from a "Website that looks dated" scan (name, website, phone,
  category, reviews, the site-check reasons), or a website URL the user names.

## Tools
| Tool | Use |
|------|-----|
| Mapflow CRM (`saas/mapflow-crm`, live at mapflow-crm.vercel.app) | Scan, shortlist, Demo Link, cold email, follow-up dates |
| `tools/capture_site.mjs` | Screenshots + real text, contacts, colours, fonts and photos of their current site |
| `tools/static_server.js` | Local preview of the concept |
| `tools/sync_intake_spec.js` | Sync the concept's `intake-spec.json` to Intake Studio once they sign |
| Vercel CLI (`vercel`, logged in, team `mashtatech`) | Preview link |
| Past builds | `websites/dental-clinic-template` (dental + booking widget), `websites/tnufa-physio` (physio + booking), `websites/ashcroft-vale`, `websites/barukh-law` (law), `websites/art-rock-dental` |
| Skills | `redesign-existing-projects`, `design-taste-frontend`, `high-end-visual-design`, `premium-website-generator` |

## Steps

### 1. Find (Mapflow → Settings)
- **Which businesses:** "Website that looks dated". The scan opens each homepage (free, one
  GET) and adds only sites that look dated or broken, most dated first, each with its
  reasons.
- **Categories:** one niche that clearly makes money: dentists, lawyers, accountants,
  physiotherapists, private clinics, aesthetic clinics, real-estate agents.
- **Location:** one city. **Minimum reviews:** 30+ (a busy business). **Minimum rating:** 4.0.
- **Places per scan:** 10–20. Then **Run scan now**.
- The settings are shared with the daily 8am scan. Switching to dated mode switches the
  daily scan too; turn off "Enable daily scan" if you only want manual runs.
- Cost: about $0.032 per Places text search (up to 3 pages per category) plus $0.04 per
  lead added. The site check costs nothing.

### 2. Shortlist (3–5), then pick one
1. In the pipeline, look at the cards with the **Dated site · score** badge. Hover it for
   the reasons. The strongest pitches are "Not built for phones", "Secure version is
   broken" and "Didn't open".
2. Capture each shortlisted site:
   `node tools/capture_site.mjs <website> --out .tmp/rebuild/<slug>`
   (`--pages 4` inner pages by default; `--no-images` skips downloading photos.)
3. Read `desktop-fold.png` and `phone-fold.png`. The scan reads code, not looks, so confirm
   with your own eyes that the site really looks dated. Drop the ones that don't.
4. Not a fit → **Mark irrelevant** in Mapflow (it blocklists them for future scans).
5. Pick **one** to build. Tell the user which one and why before building.

### 3. Build the concept
- Folder: `websites/<slug>-concept/` (`<slug>` = short Latin name, e.g. `cohen-dental`), with
  its own `git init` like the other client sites.
- Start from the closest past build when the niche matches (dental → copy
  `dental-clinic-template` without `.git` and follow its README; law → `ashcroft-vale`'s
  structure). Otherwise build fresh static HTML/CSS/JS with the design skills.
- Content comes from `.tmp/rebuild/<slug>/content.md` and `assets/`. Keep their language
  (usually Hebrew, RTL). Where content is missing, leave the section out or use an obvious
  placeholder. Use stock photos only to fill gaps, and list them in `intake-spec.json`.
- Make the upgrade visible and tie it to the site-check reasons: phone-first layout,
  click-to-call and WhatsApp buttons, https, fast load, clear services, map and hours. For
  clinics, show where online booking would go (the booking-platform widget is an upsell;
  the concept keeps its phone fallback card).
- **Concept marking, on every page:**
  - `<meta name="robots" content="noindex, nofollow">`
  - A small fixed ribbon: "קונספט לעיצוב מחדש · הוכן על ידי Mashtech · זה אינו האתר הרשמי"
    (English on English pages).
  - No form that collects visitor data. Contact buttons may call or WhatsApp the
    business's real number.
  - `vercel.json` in the folder:
    ```json
    { "headers": [{ "source": "/(.*)", "headers": [{ "key": "X-Robots-Tag", "value": "noindex, nofollow" }] }] }
    ```
- Write `intake-spec.json` as you build (see the intake-spec convention): every
  placeholder, stock photo and unconfirmed fact.
- Check it: `node tools/static_server.js 8095 websites/<slug>-concept`, then take Playwright
  screenshots at 1440px and 390px and read them next to the capture screenshots. The bar:
  it must obviously be a better version of **their** business, not a template with their
  name on it.

### 4. Preview link (ask the user first)
1. Get the user's OK to publish.
2. Deploy from the concept folder (the folder name becomes the project name):
   `cd websites/<slug>-concept && vercel deploy --prod --yes --scope mashtatech`
   Use `--prod`: Vercel's deployment protection puts non-production URLs behind a Vercel
   login by default, while the production alias `https://<slug>-concept.vercel.app` is
   public.
3. Verify logged out: `curl -sI https://<slug>-concept.vercel.app` → `200` and an
   `x-robots-tag: noindex, nofollow` header. A `401` or a redirect to vercel.com means
   protection covers it; ask the user before changing the project's Deployment Protection.
4. Paste the URL into the lead's **Demo Link** in Mapflow (card → Links, or Research tab).

### 5. Reach out (the user sends)
- On the lead page, **Generate cold email** now writes around the Demo Link (in Hebrew
  when the app is in Hebrew) and can mention one site-check reason gently. The user edits
  it to sound like themselves.
- For WhatsApp or after a call, a short version works best:
  "היי, כאן [שם] מ-Mashtech. הכנתי גרסה מודרנית לאתר של [עסק], בלי שום התחייבות, אפשר
  לראות כאן: [קישור]. אם תרצו לדבר על זה, אשמח."
- Calling first with Mapflow's call script (the "We have one, but it's old" →
  redesign path) and then sending the link converts better than a cold link.
- In Mapflow: move the stage, log the activity, set **one** follow-up about 4–5 days out.
  No reply after the follow-up → let it go.

### 6. After
- **Yes:** it's a client. Continue in the same folder (rename to `websites/<slug>` if you
  like). At launch, remove the ribbon, the noindex meta and `vercel.json` header, then run
  the `prelaunch-website-audit` skill and sync `intake-spec.json`.
- **No, asked to remove it, or no answer in 30 days:** with the user's OK, take it down:
  `vercel project remove <slug>-concept --scope mashtatech`. Mark the lead lost. A strong
  build can become a de-branded niche template, like `dental-clinic-template`.

## Edge cases
- **"Couldn't be checked"** (bot wall, 403/429/Cloudflare): the scan skips these. Use
  "Everyone" mode and judge by screenshots if the niche is worth it.
- **"Didn't open":** it may be temporary. Open it yourself before pitching. If it's really
  down, that's the strongest pitch there is.
- **Facebook-only "website"** (`Ad site`): the pitch is their first real site, not a
  redesign.
- **Looks bad but passes the check** (a clean-but-dated Wix site): the check can't judge
  taste. "Everyone" mode + `capture_site.mjs` screenshots is the way to find these.
- **Capture fails** (site down): build from the Google Maps listing and photos the user
  supplies, or skip.
- **They link to an outside booking system:** keep that link in the concept.

## Changelog
- 2026-11-03: Created. Mapflow got the "Website that looks dated" scan mode
  (`_shared/siteAudit.ts`), a minimum-reviews filter, the Site check block, Demo Link, and
  the demo angle in the cold email. `tools/capture_site.mjs` added.
