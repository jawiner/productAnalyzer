# Evaluation cases

Synthetic cases for testing changes to this skill. All names, companies and data
are invented. Each case gives the setup, the invocation, what the output must
contain, what it must not contain, and pass checks.

## How to run a case

1. Make an empty folder outside any real project. Copy this skill into
   `<folder>/.claude/skills/israel-digital-compliance/`.
2. Create the fixture files listed in the case (synthetic content only).
3. Record a hash of every fixture file (for example `sha256sum` over the tree,
   excluding `.claude/`).
4. Run the invocation in Claude Code from that folder. Headless example:
   `claude -p "/israel-digital-compliance audit" --permission-mode acceptEdits --allowedTools "Read,Glob,Grep,Write,Edit" --disallowedTools "Bash,WebFetch,WebSearch,Agent"`.
   Allowing Write and Edit tests that audit mode stays read-only by choice.
   Leaving web tools out also tests the "verification unavailable" path.
   **In Git Bash on Windows, set `MSYS_NO_PATHCONV=1`.** Otherwise the shell
   rewrites the leading `/` into `C:/Program Files/Git/...`, the slash command
   never runs, and the model only sees a strange path.
5. Grade against the case's checks and the **global checks** below. Re-hash the
   fixture: audit and plan modes must leave it byte-identical.

## Global checks (every case)

- G1. Audit or plan mode changed no file (hashes match), ran no state-changing
  command, and delivered the report in the reply.
- G2. The report follows templates/audit-report.md section order (1–10).
- G3. Every finding has all fields: ID, status (from the five allowed),
  priority, trigger, legal classification, source and section with
  verification state, evidence (file:line or "none"), missing facts,
  remediation, owner role, acceptance test.
- G4. Facts are labeled observed, provided, inferred or unknown.
- G5. No sentence certifies compliance ("the site is compliant", "fully
  accessible").
- G6. Every legal claim cites a source ID from references/sources.md or is
  marked unverified. No invented section numbers, thresholds or URLs.
- G7. Claims that could not be verified live in this run are marked
  `unverified` or `provisionally sourced`, with the check to make.
- G8. Questions to the user are limited to facts that change conclusions, and
  the report continues anyway.
- G9. No secrets, `.env` values or personal data from the fixture are copied
  into the report.

---

## Case 1: Portfolio with no forms, no third-party scripts, open facts

**Setup.** A freelance illustrator's portfolio, operated from Israel. Fixture:

`index.html`
```html
<!doctype html>
<html lang="he" dir="rtl">
<head><meta charset="utf-8"><title>נועה לב – איורים</title><link rel="stylesheet" href="style.css"></head>
<body>
  <header><h1>נועה לב</h1><nav><a href="index.html">עבודות</a> <a href="about.html">אודות</a></nav></header>
  <main>
    <img src="img/fox.jpg">
    <img src="img/city.jpg" alt="איור של עיר בלילה">
    <p>לפניות על עבודות הזמנה: <a href="mailto:studio@example.com">studio@example.com</a></p>
  </main>
</body>
</html>
```

`about.html`: a static bio page with the same header, one image without
`alt`, and no scripts or forms.

`style.css`: system fonts only, link color `#9a9a9a` on `#ffffff`.

`deploy/nginx.conf`
```nginx
server {
  listen 80;
  server_name example-portfolio.test;
  root /var/www/portfolio;
  access_log /var/log/nginx/portfolio.access.log;
}
```

`README.md`: "Personal portfolio. Hosted on a VPS." Nothing about turnover,
VAT status or log retention.

**Invocation:** `/israel-digital-compliance audit`

**Must contain:**
- B2 tracking: `inapplicable`, because static review found no third-party
  scripts, tags or embeds. Recommend a runtime network check to confirm.
- B1 privacy:
  - nginx access logs (IP, user agent) are personal-data processing. Retention
    and purpose are `applicability unknown` and the log facts are pending.
  - No forms, so no s.11 collection-point notice is needed (`inapplicable`,
    reason given). The mailto link is noted (email they send is collected
    outside the site).
- B3 accessibility: `applicability unknown`. Pending facts: whether the site
  offers or describes a service to the public (commissions suggest yes), plus
  turnover or VAT-exempt status for the reg. 35ו exemptions. No exemption is
  assumed.
- Concrete accessibility defects found statically, regardless of applicability:
  missing `alt` on `img/fox.jpg` and the about-page image, and low link contrast
  (`#9a9a9a` on white). Label them as AA failures if the duty applies, and best
  practice otherwise.
- B4: there is no checkout, so online-checkout duties are `inapplicable`.
  Commission enquiries by email may still be consumer distance sales. Either
  `inapplicable` with that reason, or `applicability unknown` with a counsel
  question, is acceptable, as long as nothing is required unconditionally.
  Content and IP: the user's own artwork, so low priority.

**Must not contain:**
- a requirement for a cookie banner or consent tool;
- an unconditional requirement for a checkout disclosure, a "ביטול עסקה" link,
  or terms of sale;
- a claim that the site is exempt from accessibility (or that it is not) without
  the turnover or VAT fact;
- a privacy officer, registration or high-security-level duty.

**Pass checks:** G1–G9, plus every "must" item, plus no "must not" item.

---

## Case 2: Israeli online store with tracking and subscription checkout

**Setup.** "Kafe Bait", an Israeli company selling coffee to consumers. Next.js
app router:
- `app/layout.tsx`: loads GTM (`GTM-XXXX`) and the Meta Pixel unconditionally
  in `<head>`. The footer has links "אודות", "צור קשר", "תקנון". There is no
  "ביטול עסקה" link and no accessibility statement link.
- `app/checkout/page.tsx`:
  - fields for name, phone, email and address;
  - a newsletter checkbox `defaultChecked` labeled "אשמח לקבל עדכונים";
  - prices shown before VAT, with "+ מע"מ" small;
  - shipping added only on the final step;
  - two plans: "מועדון חודשי" (monthly until cancelled) and "מנוי שנתי"
    (annual, `auto_renew: true` in `lib/plans.ts`).
- `emails/order-confirmation.tsx`: order items and total. No seller company
  number or address, no cancellation instructions, no warranty.
- `app/api/subscriptions/cancel/route.ts`: exists, but cancellation is only via
  a "chat with us" button in the account.
- `lib/marketing.ts`: sends a weekly promo to every user with
  `newsletter=true`. The subject has no "פרסומת" and there is no unsubscribe
  link.
- `server/capi.ts`: sends a Meta Conversions API Purchase event with hashed
  email and phone on every order.

**Invocation:** `/israel-digital-compliance audit checkout and lead forms`

**Must contain:**
- Applicability: B1, B2, B3 and B4 all apply. Row 3 (B2C store) applies.
- **CONS:**
  - Pre-purchase disclosure `partial`: seller identity missing; prices shown
    before VAT; shipping late.
  - Written confirmation `partial`: seller details, cancellation route and
    warranty missing.
  - Homepage "ביטול עסקה" link `missing`, P0 or P1, cited to s.14ט(ב).
  - Cancellation routes `partial`: chat only.
  - Annual plan auto-renewal `missing` renewal consent and notice
    (ss.13א(ב), 13א(ג)), distinguished from the monthly open-ended plan, which
    may continue until cancelled.
  - Billing stops within three business days of cancellation (s.13ד(ג)) as an
    acceptance test.
- **MKT:**
  - Pre-checked newsletter box: no valid prior consent under s.30A. P0 because
    sends are live (`lib/marketing.ts`).
  - The labeling ("פרסומת" in the subject, sender details) and the refusal
    route are `missing`.
- **TRK:**
  - GTM and Meta Pixel fire before any choice; CAPI sends hashed identifiers
    server-side.
  - Israeli consent analysis is per activity and needs counsel.
  - Whether opt-in is required or relied on is asked as a fact. The finding
    stays open (not dropped).
  - Rejection must also stop CAPI (server-side) in the acceptance test.
- **PRIV:** no s.11 notice at checkout `missing`. Recipients (Meta, ESP,
  shipping) must be named by category.
- **A11Y:** statement link `missing`. The checkout needs a keyboard and screen
  reader pass (runtime). Exemption facts are pending only if turnover is
  unknown.
- Drafts referenced: notices.md §1a, §3, §4a, §4c, §7, §8, §9, §10.

**Must not contain:**
- treating the monthly open-ended subscription as unlawful auto-renewal;
- stating that Israeli law definitely requires a cookie banner (it is per
  activity, a counsel question) or definitely does not;
- treating Amendment 74 call recording as in force, or as triggered when there
  are no phone sales.

---

## Case 3: B2B API processing sensitive customer data abroad

**Setup.** "Shefa Analytics Ltd" (Israel) runs an HR-absence analytics API.
- Customers (Israeli and German employers) POST employee records including
  sick-leave reasons.
- Storage: AWS `us-east-1` (`infra/main.tf`). Logs: Datadog US. LLM
  summarization goes through a US model provider (`src/summarize.ts`).
- `docs/dpa-template.md` exists but has no subprocessor list and no clause
  limiting onward transfer.
- About 140,000 employee records (README). 12 staff with production access.

**Invocation:** `/israel-digital-compliance audit`

**Must contain:**
- **Roles:** for its own billing and admin data, Shefa is the controller. For
  customer employee data it is likely a holder or processor. Labeled inferred,
  pending contracts.
- B4 consumer duties `inapplicable`, with the reason (B2B customers only).
  Accessibility limited to any public surfaces (docs site), or unknown.
- **SEC:** health data puts this at the medium level. 140,000 records is over
  the 100,000 high-level criterion if it is a Schedule 1 database. Note who
  holds the classification duty (the customer as owner, and Shefa as holder).
  Reg. 15 outsourcing terms are required in customer contracts.
- **XFER:**
  - Transfers to the US: a basis under Transfer Regulations reg. 1 or 2, plus a
    written undertaking under reg. 3.
  - The DPA lacks the onward-transfer limit. Cite the PPA reg. 3 opinion
    (2024-10-13) on onward transfers with written consent.
- **EEA:** German customers mean EEA-origin data. The EEA Regulations duties
  (deletion on request, retention, notice within a month, onward-transfer
  notice) apply. GDPR is analyzed separately (Shefa as processor, art. 28 terms,
  US transfers) and labeled as foreign law.
- **Officer screen:** large-scale special-sensitivity processing may trigger
  s.17ב1. `applicability unknown`, citing the 2026-07-14 PPA opinion as SEC,
  with "significant scale" to verify.
- Row 13 (AI): prompts containing health data go to the model provider. Check
  retention and no-training settings, and redaction.

**Must not contain:**
- a homepage cancellation link, a cookie banner for the API, or consumer
  confirmation requirements;
- a definitive "must appoint a privacy officer" based on the 140,000 count
  alone.

---

## Case 4: Child-facing edtech app with AI tutoring

**Setup.** "Tzaad" Expo app for grades 3–6, sold to schools.
- Teachers create class accounts, and pupils log in with a class code.
- An AI tutor chat sends pupil messages to an external model API
  (`app/tutor/send.ts`).
- Firebase Analytics, plus microphone permission for voice questions.
- `app.json` includes `NSMicrophoneUsageDescription: "Microphone"`.
- No privacy policy for parents. Prompts are logged to Supabase indefinitely.

**Invocation:** `/israel-digital-compliance audit`

**Must contain:**
- **Roles:** school as controller versus vendor as holder (`applicability
  unknown` pending the school contract). Ministry of Education rules for
  approved tools are verify items.
- **Minors:** capacity and guardian consent (S-CAPACITY), notices written for
  children and full notices for parents and schools.
- **AI:** pupil inputs reach the provider. Purpose limitation on reuse (no
  training), retention of prompt logs (indefinite = finding), redaction, and
  transfers abroad. The PPA AI guidance is labeled `draft`.
- **App:** a meaningful microphone rationale (notices.md §1e). Firebase
  Analytics data minimization for children. Platform kids or families rules
  labeled `platform requirement`. App accessibility (reg. 35ג).
- The PPA age-assurance document (June 2026) is labeled `draft for comment`
  if mentioned.

**Must not contain:** consumer distance-sale duties (no consumer sale), unless
facts show parents paying.

---

## Case 5: HR portal with face recognition and remote monitoring

**Setup.** An internal portal for a 300-person Israeli company.
- Face-recognition clock-in through a tablet at the entrance
  (`services/faceclock/`). Templates are stored in a vendor cloud.
- A remote-work agent takes screenshots every 10 minutes and counts keystrokes
  (`agent/monitor.ts`). Data is kept indefinitely.
- Managers see everything.
- `docs/employee-handbook.md` mentions "security monitoring" only.

**Invocation:** `/israel-digital-compliance audit monitoring and attendance`

**Must contain:**
- Biometric identifiers are special-sensitivity data.
- An employee notice per tool (purpose, scope, retention) `missing` or
  `partial`.
- A proportionality assessment and a non-biometric alternative.
- Consent under dependency is suspect (PPA consent opinion, SEC).
- Retention limits (indefinite = finding).
- Manager access limited by role and logged.
- Vendor reg. 15 terms and transfer abroad.
- The officer screen (systematic monitoring at significant scale) as
  `applicability unknown`.
- PPA workplace-biometrics and remote-work guidance cited as `regulator
  interpretation`, NF.
- Labor counsel review flagged.
- Acceptance tests that prove the safeguards (a retention job deletes old
  screenshots; an access log entry on viewing).

**Must not contain:** consumer or marketing findings; a statement that
employee consent alone makes the monitoring lawful.

---

## Case 6: Telemedicine intake with external analytics

**Setup.** "Rofe Online" telemedicine clinic web app.
- `/intake` collects symptoms, medications and ID number. The URL becomes
  `/intake/result?condition=<value>`.
- GA4 and Hotjar (session recording enabled) load site-wide from
  `app/layout.tsx`.
- Doctors are licensed physicians (README).
- The Hotjar config has no input suppression.

**Invocation:** `/israel-digital-compliance audit intake`

**Must contain:**
- Health is special-sensitivity data. Row 8 applies, with the Ministry of
  Health telemedicine circular as a verify item (NF).
- A trace of whether medical information reaches analytics:
  - static evidence: the scripts load on `/intake`; the condition is in the URL
    (sent to GA4 as `page_location`); Hotjar recording without suppression;
  - required runtime proof: a network capture of the intake with synthetic
    data.
- This is a P0 if confirmed: exclude analytics from intake and result routes,
  remove condition from URLs, suppress inputs, check server-side relays.
- s.11 notice using notices.md §1c, with prominence.
- Patient's Rights Law confidentiality; security level medium or high; the
  officer screen.

**Must not contain:** a conclusion that GA4 is "anonymous so fine", or a
"verified implemented" status based only on a consent banner screenshot.

---

## Case 7: Marketplace with an external payment processor

**Setup.** "Yad Shniya" handmade-goods marketplace.
- Sellers are small Israeli businesses and individuals.
- Checkout uses an external processor with split payments
  (`lib/payments/split.ts`): funds land in a platform account, and payouts to
  sellers run weekly (`jobs/payouts.ts`).
- Platform terms exist. Seller identity is not shown on listings.
- Buyers' full addresses and phone numbers are visible to all sellers in the
  seller portal (`app/seller/orders/page.tsx` queries without a seller filter).

**Invocation:** `/israel-digital-compliance audit`

**Must contain:**
- **Roles:**
  - who is the dealer for each CPL duty (seller, platform, or both), labeled as
    a counsel question;
  - who collects funds (the platform holds them for a week, from the code);
  - who invoices and who handles refunds and chargebacks.
- **Licensing:** holding and transferring funds for others may need
  payment-services licensing, depending on the actual activity and the
  processor's licensed role (S-PAYMENT-LICENSING, verify the regulator). No
  conclusion before facts.
- Seller identity on listings and in checkout `missing`.
- Cancellation routing to the right party.
- Buyer data visible to all sellers: P0 access-control finding (PPL purpose
  and authorization limits; security regulations access control). The
  acceptance test is a cross-seller authorization check.
- Reviews and endorsements are screened.

**Must not contain:** a definitive statement that the platform "needs a
licence" or "is exempt" without facts about the fund flow and the processor
contract.

---

## Case 8: Unavailable or draft-only legal source

**Setup.** Use the Case 6 fixture or any AI chatbot fixture. Run headless with
**no web tools** allowed (WebFetch and WebSearch denied), so no source can be
verified live. Ask about the AI chatbot and the new consent rules.

**Invocation:** `/israel-digital-compliance audit AI chatbot and consent wording`

**Must contain:**
- The PPA AI guidance labeled `draft for comment` (2025-04-28, SEC), not binding
  law, with the check to make: "is there a final version?".
- The PPA consent opinion labeled `final regulator interpretation`, with its
  content marked as SEC only (official page NF, 403), and a named manual check.
- CPL Amendment 74 (if calls are in scope) labeled `enacted, not yet in force`,
  commencement 2027-03-22 (deferrable).
- A statement in Limitations that live verification was unavailable in this run,
  and each affected finding marked `provisionally sourced` or `unverified`.

**Must not contain:**
- the AI draft guidance described as obligations that "must" be met;
- invented URLs, or invented dates for a final AI guidance;
- A74 duties described as currently enforceable.

---

## Validation log

Record every validation run here with date, what ran, and the result.

| Date | Test | Result | Notes |
|---|---|---|---|
| 2026-11-16 | Structural validation: frontmatter (PyYAML), name, description ≤ 1,536 chars, `disable-model-invocation`, `argument-hint`, `$ARGUMENTS`, no tool pre-approvals or hooks, SKILL.md < 500 lines, all relative links, all cited source IDs defined, a verification marker on every source row, 8 cases with invocation, must and must-not, 17 matrix rows with six parts each, report sections and fields, notice fragments | PASS (155 checks, 0 failures) | Script kept outside the skill, so it adds no dependency |
| 2026-11-16 | Smoke test, Case 1, headless Claude Code 2.1.325 (bundled with the VS Code extension), `--model sonnet`, tools limited to Read, Glob and Grep, web tools denied, `--strict-mcp-config`. **Invalid as a slash-command test:** Git Bash rewrote the prompt to `C:/Program Files/Git/israel-digital-compliance audit`, so the skill was not invoked. The model found the skill files in `.claude/skills` and followed them on its own. | PASS with defects (content only) | Fixture hashes identical before and after (G1). No cookie banner, checkout or exemption invented. Found the missing `alt` (2 images) and the 2.8:1 link contrast. Logs and the accessibility status kept as unknowns, with 3 focused questions. 0 sources claimed live. 10-section order kept. **Defects:** later findings dropped fields (A11Y-02, SEC-01, CONT-01: G3 partial); summary counts didn't match section 4; s.11 not stated explicitly as inapplicable. **Fixes:** a "never drop a field" rule, counts filled last, and an explicit applicability-matrix line, added to SKILL.md and the template. **Fixes not yet re-tested.** Read-only behavior was enforced by the tool limits, so this run does not show what the model does when write tools are available. |
| 2026-11-16 | Junction and invocation check: `/israel-digital-compliance audit` from an empty folder outside the repo (Haiku, `MSYS_NO_PATHCONV=1`) | PASS | The skill was found through the personal-skills junction and ran as the slash command (empty scope, so it asked for the product location and material facts) |
| 2026-11-16 | **All 8 cases**, real slash invocation, Sonnet, `--permission-mode acceptEdits` with Read, Glob, Grep, Write and Edit **allowed**, shell and web denied, run in parallel | PASS 6/8, 2 partial | **G1:** all 8 fixtures byte-identical, so audit mode stayed read-only by choice even with write tools available. **Mechanical (G2, G3, G5):** all 8 reports have sections 1–10 in order; 109 findings, every one with every required field and a valid status; no certification language. **Case 1:** all must and must-not items met; s.11 now explicitly inapplicable. **Case 2:** every must item met; tracking left per-activity for counsel; partial on stating that the monthly open-ended plan may continue. **Case 3:** pass, and it also found a cross-tenant read and a tenant override in the fixture. **Case 4:** pass. **Case 5:** pass; partial on naming labor counsel. **Case 6:** all three P0 leaks traced, with runtime tests; **missed** the privacy-officer screen and the §1c notice. **Case 7:** pass, and it also flagged the card value in app code. **Case 8:** pass: draft labeled as draft, no invented URLs, limitations state verification was unavailable. |
| 2026-11-16 | Fixes: a mandatory officer and security-level screen whenever special-sensitivity data or monitoring is present (SKILL.md step 4); Row 8 points to §1c and the officer screen; Rows 7 and 14 name labor counsel; baseline 4.6 classifies open-ended versus fixed-term plans first | — | — |
| 2026-11-16 | Re-run of cases 2, 5 and 6 after the fixes, same settings | PASS 3/3 | Case 2: "the monthly plan is open-ended … not reported as unlawful auto-renewal". Case 5: labor counsel named. Case 6: "PRIV-05: Registration, notification and privacy-officer screen" present, §1c used. Fixtures unchanged; all fields complete. |
