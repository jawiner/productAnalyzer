# Israel baseline: applicability tests and baseline requirements

This file is a research map. Every rule below cites a source ID from
[sources.md](sources.md) and a verification marker:

| Marker | Meaning |
|---|---|
| `WS` | Wording cross-checked on 2026-11-16 against the unofficial consolidated text on he.wikisource. Good for orientation; confirm against official text before relying on it in a finding. |
| `KO` | Status or date checked on 2026-11-16 in Knesset open data (official metadata, not the text itself). |
| `SEC` | Taken from secondary summaries (law firms, Kol Zchut, press). The official document was not read. |
| `UNV` | Background knowledge only. Unverified. Must be checked before a finding relies on it. |

The legal classification labels (`statute`, `regulation`, `binding sector rule`,
`regulator interpretation`, `platform requirement`, `contract requirement`,
`best practice`) are defined in [SKILL.md](../SKILL.md). Thresholds and periods
here are cached values. Treat them as prompts to verify, never as answers.

---

## 0. Applicability tests (run before each module)

Each regime has its own test. One nexus does not trigger them all.

| Regime | Ask | Typical trigger | Typically not triggered by |
|---|---|---|---|
| Privacy Protection Law (PPL) | Is there a "database" (מאגר מידע) of personal information, or other personal-information processing, under Israeli jurisdiction? Who is the controller (בעל שליטה) and who is a holder (מחזיק)? | Israeli operator or controller; Israeli users' data processed by an Israeli entity; a database managed in Israel | A foreign operator with no Israeli establishment and no Israeli processing (verify: the territorial reach is not settled; flag for counsel) |
| Communications Law s.30A (spam) | Are covered "advertisements" sent by fax, automated dialing, electronic message or SMS to recipients in Israel, or by an Israeli advertiser? | Newsletters, promotional SMS, WhatsApp or email campaigns, donation appeals | Transactional messages with no promotional content (check mixed messages) |
| Consumer Protection Law (CPL) | Is there a dealer (עוסק) selling to a consumer (צרכן) for personal, household or family use? Is it a distance sale (no physical meeting)? Is it an ongoing transaction? | B2C store, bookings, memberships, subscriptions, digital goods sold to Israeli consumers | Pure B2B sales (verify each contract: small businesses are sometimes treated as consumers), free services with no transaction (other CPL parts may still apply, e.g. misleading claims) |
| Accessibility (Equal Rights Law and regulation 35) | Does the surface supply a service to the public, or information about one? Is the operator a body bound by the service-accessibility chapter? | Public websites and apps of businesses, public bodies and nonprofits that serve the public | Purely internal staff tools (other duties, such as employment accessibility, may apply), with every exemption verified individually |
| Sector law | Does the activity need a licence, or is it supervised (health, finance, education, insurance, gambling, tobacco, travel)? | See [system-types.md](system-types.md) | Nothing. Always screen the activity itself |
| Foreign law | Is the product offered to people in, or monitoring people in, the EU or other markets? | EU offering or monitoring triggers GDPR art. 3(2) analysis (S-GDPR, UNV) | Analyze it separately and never blend it into the Israeli conclusion |

Record each test's outcome in the report's applicability matrix with the facts it
relied on.

---

## 1. Privacy and data governance

### 1.1 Data inventory (always build it)

For every flow, record: data category; source (user, device, third party,
inferred); collection point (file:line); purpose; legal basis or consent
mechanism; recipients and vendors; storage location and country; access roles;
transfers abroad; reuse or secondary purposes; retention period and the job that
enforces it; deletion behavior (including in backups).

Look beyond forms. Also check:
- server and CDN access logs, error and crash reports (Sentry and similar),
  APM traces, debug logging of request bodies;
- account records, audit logs, support tickets, call recordings and transcripts;
- lead data, CRM syncs, enrichment services, inferred profiles, scores and
  segments;
- cookie IDs, device IDs, advertising IDs, fingerprinting, IP addresses;
- uploads (images carry EXIF and location), documents, voice;
- background, scheduled or server-side events (Conversions API, server-side
  tagging, webhooks to vendors);
- AI prompts and outputs sent to model providers, and their retention there.

Flag special-sensitivity data. The PPL definition includes, among other things:
family privacy and sexual orientation; health; genetic data; biometric
identifiers; origin; criminal record; political opinions and religious beliefs;
personality assessments; location and traffic data; salary and financial
activity; and information under a legal duty of secrecy (S-PPL s.3, WS; read the
full list in the official text).

### 1.2 Section 11 notice at the point of collection (`statute`)

When a person is asked to provide personal information for processing in a
database, the request must come with a notice (S-PPL s.11 as amended by S-A13,
WS). The notice states:

1. whether there is a legal duty to provide the information, or whether it
   depends on the person's will and consent;
2. the purpose for which the information is requested;
3. the recipients of the information and the purposes of delivering it to them;
4. the identity of the database controller and how to contact them;
5. the consequence of refusing (listed in the brief; confirm the wording in the
   official text);
6. the rights to inspect and to request correction (ss.13–14).

Implementation:
- Map the notice to every collection point: each form, sign-up, checkout field
  group, permission prompt, intake wizard, chatbot that asks for details, call
  script, and API that accepts personal data from end users on a customer's
  behalf.
- Put a short notice next to the request (under the submit button or inside the
  permission rationale), with a link to the full policy section. A policy linked
  only from the footer does not meet a "near the request" acceptance test.
- Mark which fields are mandatory, and say why each is mandatory, beside the
  field or in the notice.
- **Regulator interpretation (S-PPA-CONSENT, final opinion of 2026-02-25, SEC):**
  - The s.11 notice is a minimum.
  - Consent is valid only if the information was actually presented
    adequately.
  - Do not describe data types or purposes with "among others" (בין היתר).
  - Recipients may be described by category, but not with overly generic
    labels.
  - Sensitive or unexpected processing (for example continuous location) needs
    special prominence and cannot be left to the terms or the policy.
  - Consent given under dependency (employment, a conditioned essential service)
    is suspect.

  Read the official opinion before citing specifics.

Whether s.11 covers passive collection (cookies, SDK telemetry) is an open
question. Treat it as a `regulator interpretation` question and flag it for
counsel. Disclose passive collection in the policy whatever the answer.

### 1.3 Processing limits after Amendment 13 (`statute`)

Amendment 13 restricts processing personal information (S-A13 summary, KO):
- for a purpose other than the one it was provided for;
- without authorization, or beyond the controller's authorization;
- when the information was created, received, accumulated or collected in
  breach of the law.

Check:
- reuse of support or lead data for model training, enrichment or ad audiences;
- staff access beyond their role;
- data pulled from third-party sources without a lawful basis.

Amendment 13 was published 2024-08-14 (KO) and came into force 2025-08-14
(SEC). It also expanded the regulator's enforcement powers. Verify the current
administrative-fine provisions before you describe risk levels.

### 1.4 Data subject rights

- **Inspection (s.13, `statute`, WS):** any person may inspect information about
  them, in person, through a representative authorized in writing, or through a
  guardian. The manner, conditions and timing are set by regulations
  (S-PPL-INSPECT-REGS, UNV: the response period is commonly cited as 30 days).
  Check that there is a request route, identity verification, a response
  procedure and a log.
- **Correction (s.14, `statute`, WS):** a request to correct or delete
  information that is not correct, complete, clear or up to date. Refusal and
  onward notification follow regulations.
- **Deletion:** Israeli law has no general GDPR-style right to erasure. Do not
  draft "you can delete all your data at any time" unless the operator chooses to
  offer it, or one of these applies:
  - removal from a direct-mailing database (S-PPL chapter B1, UNV: verify the
    section after Amendment 13);
  - EEA-origin data (S-EEA-REGS reg. 3, WS);
  - a platform requirement (account deletion in app stores: `platform
    requirement`);
  - a contract (a DPA with a business customer).
- Check the full path. Does "delete account" delete from the primary DB, search
  indexes, analytics, the CRM, vendors and backups (with a stated expiry)? Or
  does it only flag the account?

### 1.5 Full privacy policy (sections to draft from actual practice)

Draft only sections that match observed or provided facts. Label the basis of
each required disclosure:

| Section | Basis |
|---|---|
| Controller identity and contact | s.11 (statute) for collection points; also best practice for the policy |
| What is collected, including automated collection (logs, cookies, SDKs) | s.11 for requested data (statute); consent opinion (regulator interpretation); passive data is best practice or open (see 1.2) |
| Purposes | s.11 (statute) |
| Recipients and their purposes, vendors by category | s.11 (statute); consent opinion on specificity |
| Processing abroad and the transfer basis | S-TRANSFER-REGS (regulation); disclosure of it is best practice unless consent is the basis |
| Retention criteria | Best practice; mandatory for EEA-origin data (S-EEA-REGS reg. 4, WS) |
| Rights and how to use them | ss.13–14 (statute) |
| Marketing choices and refusal | s.30A (statute) and direct-mailing rules |
| Privacy officer contact | Only where s.17ב1 requires an officer (statute) or one is appointed voluntarily |
| Children | See system-types, Children row |
| Changes to the policy | Best practice |

### 1.6 Database security (`regulation`: S-SEC-REGS, WS)

Classify each database:

| Level | Criteria (WS; confirm in the official schedules) |
|---|---|
| Managed by an individual | Run by one person, or a company owned by that person, where at most two other authorized people can use it. Excludes databases whose main purpose is delivering information to others, databases with information on 10,000 people or more, and databases under professional secrecy. |
| Basic | Neither in Schedule 1 nor Schedule 2, and not individual-managed. |
| Medium | Schedule 1 types: among others, direct-mailing databases, public-body databases, and databases with sensitive data such as medical, genetic, criminal, biometric or financial data. Some drop to basic when they have no more than 10 authorized users or meet other listed conditions. |
| High | Schedule 1 types with information on 100,000 people or more, or more than 100 authorized users. |

Controls to check, with the evidence to collect:

| Control | Requirement (WS) | Evidence |
|---|---|---|
| Database definitions document | Purposes, data types, transfers abroad, processor activities, main risks, and the names of the manager, holder and security officer. Updated on significant change and reviewed every year, including whether more data is held than the purposes need. | The document and its review date |
| Security procedure and mapping | Required by the regulations | Written procedure, system map |
| Access control and least privilege | Authorizations by role, reviewed periodically | Role definitions in code (RLS policies, middleware), an access review record |
| Logging | Medium and high: access logs kept at least 24 months | Log config, retention setting |
| Incidents | Record incidents. Report a severe incident to the regulator immediately. The regulator may order notice to the people affected. Review incidents yearly (medium) or quarterly (high). | Incident runbook, contact route, a drill record |
| Risk survey and penetration test | High level: at least every 18 months | The last reports |
| Periodic audit | Medium and high: an independent auditor at least every 24 months | The audit report |
| Outsourcing (reg. 15) | A risk assessment before engagement. The contract states: data and purposes; systems accessed; processing types; duration; return or destruction with confirmation; security obligations; staff confidentiality; subcontractors; at least yearly compliance reports; prompt incident notice. | The DPA or contract, the vendor list |
| Backup and restore | Required at medium and high | Backup config, restore test |

Use the PPA outsourcing guidance (S-PPA-OUTSOURCING, not fetched) to interpret
reg. 15. Mark it `regulator interpretation`.

### 1.7 Transfers abroad (`regulation`: S-TRANSFER-REGS, WS)

- **Reg. 1:** transfer is permitted where the destination's law gives a level of
  protection not lower than Israel's, measured against five listed principles.
- **Reg. 2:** alternatives, any one of which suffices:
  1. consent;
  2. a vital health or body-integrity need where consent cannot be obtained;
  3. a corporation controlled by the database owner that has guaranteed
     protection;
  4. a recipient contractually bound to meet Israeli conditions;
  5. information lawfully made public;
  6. public safety or security;
  7. a duty under Israeli law;
  8. countries party to the Council of Europe convention, countries that
     receive EU data on similar terms, or countries named by the regulator.
- **Reg. 3:** the owner must obtain a **written undertaking** from the recipient
  to take adequate measures and not to pass the information on, in the same
  country or anywhere else. Check that each foreign vendor's terms or DPA
  contains an equivalent clause.
- **PPA opinion on reg. 3 (S-PPA-TRANSFER-INTERP, 2024-10-13, GOV-PDF,
  `regulator interpretation`):**
  - The foreign recipient may pass the information on to a third party if the
    Israeli database owner consents in writing. That onward transfer must
    itself meet reg. 1 or 2, as if it were made directly from Israel.
  - The undertaking may rely on other accepted guarantees, such as a commitment
    to GDPR or to the law of a country with an EU adequacy decision.
  - If the transfer is part of outsourcing, or gives an external party access
    to the Israeli database, security reg. 15 (1.6) also applies.
  - In practice: check that each vendor's DPA allows subprocessors only with
    the operator's written authorization, and that subprocessors sit in
    countries or under terms that meet reg. 1 or 2.
- List every storage and processing country. Do not forget the regions used by
  analytics, error tracking, email, AI and support vendors.

### 1.8 Information transferred to Israel from the EEA (`regulation`: S-EEA-REGS, WS)

These rules apply to databases holding information transferred from the EEA
(apart from information a person sent about themselves) and to other data mixed
into the same database. The duties:
- **Delete on written request** when the information was obtained unlawfully or
  is no longer needed (reg. 3, with exceptions).
- **Retention limits** (reg. 4).
- **Accuracy mechanisms** (reg. 5).
- **Notice** to the data subject within one month of receiving the information
  when it was not collected from them directly, and before any onward transfer
  (reg. 6).

Dates: published 2023-05-07. The rules applied to new data after three months
and to existing data after one year. The provision for data under reg. 2(a)(2)
applies from 2025-01-01. Trigger this check when a B2B customer, partner or
parent company sends data from the EU.

### 1.9 Registration, notification and privacy officer screening (`statute`, WS; verify triggers)

- **Registration (s.8א):** required for a database whose main purpose is
  collecting personal information to deliver to others as a business or for
  consideration, with information on more than 10,000 people, and for public
  bodies (S-A13 summary, KO). Since Amendment 13, most ordinary businesses no
  longer register.
- **Notification (s.8א(ב)(1)):** when a database that does not need registration
  holds special-sensitivity information on more than 100,000 people, the
  controller notifies the regulator within 30 days. The notice includes the
  controller's details and the privacy officer's details where one is required
  (S-PPA-NOTICE, not fetched).
- **Privacy officer (s.17ב1):** required for:
  - public bodies (except security bodies);
  - databases whose main purpose is collection for delivery for consideration,
    with more than 10,000 people;
  - bodies whose main activity involves systematic monitoring of people at
    significant scale;
  - bodies whose main activity involves processing special-sensitivity
    information at significant scale (the text gives examples such as banks,
    insurers, hospitals and HMOs).

  The PPA published an opinion on appointing officers on 2026-07-14
  (S-PPA-DPO, SEC). Read it for the meaning of "significant scale" before you
  conclude anything.
- A threshold alone never decides the duty. You also need the main purpose,
  the main activity, the type of data, and whether the body is public. Record
  counts as **observed**, **provided** or **unknown**. Never guess a count.

### 1.10 Call recording (cross-reference)

From 2027-03-22, certain dealers must record consumer phone calls and disclose
the recording (S-CPL-A74, KO). See 4.9. For any call recording, apply the PPL
too: a notice at the start of the call, purpose, retention, access control, and
vendor transcription.

---

## 2. Tracking and marketing

### 2.1 Tracker inventory

For each tracker or integration, record: name and vendor; where it loads (file:line,
tag manager container, SDK init); data sent (identifiers, events, page or
content context, form contents); purpose (essential, analytics, advertising,
personalization, replay, embed); recipient and country; when it fires (page
load, after a choice, server side); the choice mechanism and its default;
whether rejection and withdrawal reach it.

Include:
- essential storage (session, CSRF, cart);
- analytics (GA4, Plausible, PostHog);
- ad tags and pixels (Meta, Google Ads, TikTok, LinkedIn);
- session replay and heatmaps (Hotjar, Clarity, FullStory);
- embeds (YouTube, Maps, social widgets, chat widgets);
- mobile SDKs (Firebase, AppsFlyer, Adjust);
- server-side conversion events (Meta CAPI, Google Enhanced Conversions,
  server-side GTM).

### 2.2 Israeli consent analysis (activity by activity)

- No Israeli statute dedicated to cookies was identified when this skill was
  written (UNV; re-check in `refresh`). The analysis runs through:
  - the PPL: consent as the defence to an infringement of privacy (S-PPL s.1
    definition of consent and s.2, UNV);
  - s.11 notice;
  - the processing limits of Amendment 13;
  - the special-sensitivity rules;
  - the 2026 consent opinion (`regulator interpretation`, SEC).
- Judge it by activity, and mark each conclusion as needing counsel:
  - Session replay that captures form inputs, cross-site advertising pixels,
    sharing identifiers together with health, financial or child context, and
    precise location are the strongest cases for prior opt-in.
  - First-party, aggregate, privacy-preserving analytics are the weakest.
- If the operator **relies on** opt-in (for example because it also serves the
  EU), the implementation must hold up whatever the Israeli conclusion is.
- EU and other markets: analyze them separately. In the EU, ePrivacy art. 5(3)
  needs consent for non-essential storage or access on the device, plus GDPR
  (S-GDPR, UNV). Never write "required by Israeli law" for an EU requirement.

### 2.3 Technical verification of choices (runtime evidence required)

Where opt-in is required or relied on:
1. Fresh profile, no choice made: no optional tracker request on the network,
   no optional cookies or localStorage keys, no optional server-side events in
   the server log.
2. Reject: the same as step 1, persisting across reloads and routes. In the app,
   no SDK initialization before the choice.
3. Accept, then withdraw from a persistent link ("הגדרות פרטיות"): new requests
   stop, the server-side relay stops, and vendor consent signals update (for
   example Google Consent Mode).
4. The choice is logged with its timestamp, notice version and choice. The log
   holds no extra personal data.

A banner screenshot alone fails this test.

### 2.4 Advertising messages: Communications Law s.30A (`statute`: S-COMM, WS)

- **Scope.** An advertisement (דבר פרסומת) is any of:
  - a commercial message promoting a product or service;
  - a message to the public seeking a donation or propaganda;
  - a message to the public offering to call a number to receive a message
    (with exclusions for government and emergency bodies).

  It is covered when sent by fax, automated dialing system, electronic message
  (email, and per common reading also messaging apps; verify) or SMS.
- **Consent.** Prior, explicit consent, in writing, including by electronic
  message or a recorded call. An automated call made without consent is a
  breach even if it is cut off before it is answered.
- **One-time approach.** A single approach to a business recipient, or to a
  recipient for donation or propaganda, is allowed if it only offers to receive
  future ads.
- **Nonprofits (s.30A(ב1)).** An amuta or public-benefit company may send
  donation or propaganda emails without prior consent unless the recipient has
  refused. Verify whether this extends beyond email.
- **Existing-customer exception (narrow, all conditions required).** The
  recipient gave their details while buying or negotiating to buy. They were
  told the details would be used for ads. They were offered a chance to refuse
  and did not. The ad is for a similar product or service. The advertiser
  carries the burden of proving this (SEC).
- **Labeling (s.30A(ה)).**
  - The ad clearly states that it is an ad: "פרסומת", or "בקשת תרומה" or
    "תעמולה" as relevant, at the start of the message, and in the email
    subject line.
  - It shows the advertiser's name, address and contact details, the right to
    refuse and a simple way to refuse.
  - Email needs a working web address for refusal.
  - Automated voice messages must offer immediate removal.
  - SMS needs only the advertiser's name and contact method.
- **Refusal (s.30A(ד)).**
  - Refusal is possible at any time, generally or for one type of ad, and
    withdraws any earlier consent.
  - It costs nothing beyond the cost of sending it.
  - It can be sent in writing or by the same channel as the ad.
  - When a continuing business relationship ends, the recipient is treated as
    having refused.
- **Exposure.** A criminal fine; a civil wrong; and, where sent knowingly, up to
  ILS 1,000 per ad without proof of damage. Class actions are common.
- **Transactional versus promotional.** Receipts, order and delivery updates,
  security alerts and service notices are not ads. A transactional message that
  carries a promotion becomes an ad. Check templates for upsell blocks.

Evidence to collect: the consent checkbox (unchecked by default, separate from
accepting terms); consent records (who, when, which text, which channel);
suppression list enforcement before every send (look at the send code path, not
only the ESP setting); the unsubscribe handler; template headers and subjects.

### 2.5 Direct mailing using a database (`statute`: S-PPL chapter B1, UNV)

When a database is used to target people by a characteristic (age, gender,
location, purchase history, segment), the direct-mailing provisions apply. Check:
- the required statements in each direct mailing (that it is direct mailing,
  the right to be removed, the source of the information);
- that removal requests are honored;
- any registration duty for direct-mailing services after Amendment 13.

Verify the section numbers and content against the official consolidated text.
Amendment 13 changed registration, and the direct-mailing chapter may have
changed with it.

---

## 3. Accessibility

### 3.1 Applicability (`statute`: S-ACC-LAW; `regulation`: S-ACC-REGS, WS)

The service-accessibility chapter binds whoever supplies a service to the
public. Regulation 35 and the following regulations set the duties for internet
services. Ask:
- Does the site or app supply a public service, or information about one
  (including a business's own services)?
- Who is the bound party, and is it a public body?
- What is the average annual turnover? This is needed to evaluate exemptions
  and the video duty, never to assume them.
- Is the surface an app, a website, documents, video, or third-party content?

### 3.2 Standard and level (WS)

The web accessibility standard is Israeli Standard 5568 (ת"י 5568), at level
**AA** (reg. 35א(א)). IS 5568 adopts WCAG with Israeli changes. Confirm which
WCAG version the edition in force adopts (UNV) before you cite success-criterion
numbers.

Related provisions:
- **Apps (reg. 35ג):** apps are covered. An app may be exempt if the same
  service is offered on a compliant website and the app links to it.
- **Video (reg. 35ד):** captions apply to bodies that are public bodies or have
  average turnover above ILS 5 million. Conference and lecture recordings may
  use a transcript instead.
- **Documents:** documents created from 2017-10-26 must comply. Personal
  documents behind a login must comply from 2022-01-01.
- **Third-party content (reg. 35ב):** the operator is not responsible for content
  it hosts but did not create, but must provide an accessible infrastructure.
- **Defects (reg. 35א(ד)):** after notice of a defect, fix it within at most 60
  days, and provide an alternative as soon as possible.

### 3.3 Exemptions (reg. 35ו, WS): never infer one

| Exemption | Conditions to evidence |
|---|---|
| Small business | VAT-exempt dealer (עוסק פטור), or average annual turnover of no more than ILS 100,000 (reg. 35ו(ז)) |
| Legacy low-turnover sites | Average turnover of no more than ILS 1,000,000, for sites or apps launched before the regulations came into force, with contact methods published. Lasts three years and is renewable (reg. 35ו(ט)). Check dates and renewal. |
| Closed services | Pre-registration required and at most 500 simultaneous participants, unless a person with a disability asks for the adjustment (reg. 35ו(ה)) |
| Technical impossibility | Granted by an authorized person on an expert opinion, for up to three years, renewable once (reg. 35ו(א)–(ב),(ד)) |
| Advertisements | Excluded if an accessible alternative exists for the service information (reg. 35ו(י)) |
| Expired | The ILS 300,000 transitional exemption ended on 2020-10-26 |

Every exemption needs evidence: turnover statements, the dates the site
launched, the exemption document. The accessibility statement must disclose any
exemption and the alternative arrangements (reg. 35ו(ג)). Size or business
status alone is never an exemption.

### 3.4 Audit checklist (automated plus manual)

Automated tools (axe, Lighthouse, Pa11y) find only part of the problem. Run them,
then verify the rest by hand:

- **Keyboard:** every flow can be completed without a mouse. The focus order is
  logical in RTL. Focus is visible. No keyboard traps (check modals, menus and
  the cookie banner).
- **Screen reader** (NVDA plus Chrome, VoiceOver plus Safari): names, roles and
  states; `lang="he"` and `dir="rtl"`; headings; landmarks; announcements for
  errors and status changes; accessible names on icon-only buttons.
- **Contrast** of text, UI components and focus indicators. Text resizes to 200%
  without loss. Reflow at 320 CSS px.
- **Forms:** visible labels; errors in text (not only color) tied to fields;
  instructions before the input; no time limits, or adjustable ones.
- **RTL:** mirrored layout where meaningful; numbers, phone numbers, emails and
  mixed Hebrew and English fields display correctly; icons point the right way.
- **Flows:** sign-up, checkout (including an embedded payment iframe from a
  provider; test it and record vendor responsibility), the cancellation form,
  the consent banner, the account and deletion screens.
- **Documents and media:** PDFs tagged, captions, transcripts, no autoplay
  without controls.
- **Mobile:** touch target size, orientation, zoom not disabled, the screen
  reader on real devices.
- **Third-party critical services:** booking widgets, chat, maps, payment. Test
  them and note whose fix each one is.

An "accessibility overlay" widget is not evidence of conformance.

### 3.5 Accessibility statement (reg. 35ה, WS)

The statement must be published prominently on the site and in any app. It
follows the standard's guidance and includes:
- the accessibility adjustments actually made;
- the accessibility coordinator's details and contact methods, where the
  operator must appoint one (verify the coordinator trigger in the regulations,
  UNV);
- contact details for reporting a missing adjustment or requesting one;
- any exemption and the alternative arrangements;
- where relevant, the accessibility arrangements of the physical service
  (branches, clinic, venue).

Draft from [../templates/notices.md](../templates/notices.md), section 6. List
only accommodations you verified. Never claim "fully accessible".

---

## 4. Consumer protection, contracting and content

### 4.1 Applicability

There must be a dealer (עוסק) and a consumer (צרכן). A distance sale (עסקת מכר
מרחוק) is marketing without the parties meeting, including online, by phone, and
through apps (S-CPL s.14ג, WS; confirm the definition). Ongoing transactions
(עסקה מתמשכת) have their own rules (s.13א onward). Identify the dealer for each
sale: the platform, the seller, or both (see the Marketplace row).

### 4.2 Before the purchase: disclosure (s.14ג(א), WS for (7); confirm the full list)

Surface these before the purchase, on the product page or the checkout step,
not only in the terms:
- the dealer's name, ID or company number, business address and contact
  details;
- the main characteristics of the product or service;
- the total price, including VAT and every mandatory charge; delivery cost;
  payment terms;
- delivery or performance dates and terms;
- how long the offer is valid;
- the warranty;
- the cancellation right under s.14ג(ג) or s.14ג1(ג), with its conditions;
- anything else in the official list.

Price display: show the full price including VAT to consumers, with mandatory
charges included (S-CPL price provisions and S-CPA-PRICES guidance, UNV; verify
the sections). Check "from" prices, fees that appear only at the last step, and
currency.

Also check:
- **Amendment 72** (published 2025-04-02, KO; check its commencement): a
  dealer accepting debit or credit cards may not set a minimum purchase amount
  for card payment.
- **Misleading conduct** (s.2, UNV): crossed-out "was" prices, countdown
  timers, fake scarcity, "free" trials that convert, hidden recurring fees.
- **Paid endorsements, influencer posts and reviews:** check the CPA's position
  (`regulator interpretation`, UNV) and label sponsored content.

### 4.3 Written disclosure document (s.14ג(ב), UNV; confirm the timing and contents)

Send the consumer a written document (usually the confirmation email or a PDF)
in Hebrew or in the language of marketing. It is due by the time required by law
(commonly: no later than delivery of the goods or the start of the service). It
includes:
- the pre-purchase details;
- manufacturer, importer and country-of-origin details where applicable;
- the warranty;
- how the consumer cancels;
- any other required terms.

Evidence: the email template and its send trigger in code. Is it sent for every
order path (guest, app, phone)?

### 4.4 Cancellation right and its consequences

- **Windows (s.14ג(ג), WS).**
  - Goods: from the transaction until 14 days after receiving the goods or the
    disclosure document, whichever is later.
  - Services: within 14 days of the transaction or of receiving the document,
    whichever is later. There are conditions about cancelling shortly before
    the service date; confirm them in the official text.
- **Special populations (s.14ג1(ג), WS).** People with disabilities, senior
  citizens and new immigrants may cancel within four months of the transaction,
  if it included a conversation between the dealer and the consumer (including
  electronic). Confirm the age and immigrant definitions.
- **Excluded categories.**
  - Distance sales have statutory exceptions in s.14ג (UNV: commonly perishable
    goods; accommodation, travel and leisure services close to their date;
    information as defined in the Computers Law; goods made to order; and
    copyable goods whose packaging was opened).
  - The Cancellation Regulations list further categories for transactions
    under them (S-CANCEL-REGS reg. 6, WS): custom-made goods; food; medicines
    and supplements; perishables; computer information; opened copyable goods;
    underwear and swimwear; gas; jewelry over ILS 3,000; services performed
    entirely abroad (only if the terms were disclosed before the contract); and
    vouchers and gift cards.
  - Decide which instrument governs the transaction before you cite an
    exception.
- **Consequences (s.14ה, WS).**
  - Cancellation for a defect, nonconformity or non-delivery: refund within 14
    days of the cancellation notice, and no cancellation fee.
  - Other cancellations: the fee may not exceed 5% of the price. The
    regulations cap it at the lower of 5% or ILS 100 (S-CANCEL-REGS reg. 5(א),
    WS).
  - The regulations set a refund within seven business days for transactions
    under them (reg. 4(א), WS). That differs from the 14 days in s.14ה, so
    confirm which applies.
  - Refund by the same payment method. Cancel the credit card charge.

### 4.5 Cancellation route: s.14ט (`statute`, WS)

- When a consumer has a right to cancel under the law or the contract, the
  dealer must let them cancel by the listed means (s.14ט(א)).
- **Homepage link:** a dealer with a website must put on its main page a
  dedicated link through which a cancellation notice can be sent, placed
  prominently and clearly (s.14ט(ב)). Use the label "ביטול עסקה". Check the
  official text for the exact required wording.
- The cancellation information goes on the site's main page, together and with
  special prominence (s.14ט(ה)(2), (ו)).

Acceptance tests:
- the link is visible on the homepage without logging in, on desktop and
  mobile;
- it opens a working form, not a mailto link or a PDF;
- the form needs only identifying details, not a reason;
- submitting it creates a record, sends the consumer a confirmation, and
  notifies the business;
- it works for guests and for logged-in users.

### 4.6 Ongoing transactions, renewals and trials (ss.13א–13ד, WS)

- **First classify every plan** as open-ended (runs until cancelled, with no end
  date) or fixed-term (for example an annual plan), and say which one each plan
  is in the finding.
  - An open-ended plan may keep billing until the consumer cancels. It needs
    clear pre-purchase disclosure and a working cancellation route. Do not
    report it as unlawful auto-renewal.
  - The end-of-term notice and renewal-consent rules below are for fixed-term
    deals.
- **Notice before the end of a fixed term** (s.13א(ב)): where a fixed-term deal
  is billed by standing authorization, the dealer notifies the consumer of the
  end date during the "notice period" in s.13א(א). The text quoted starts it 60
  days before the end; confirm the exact window.
- **No silent auto-renewal** (s.13א(ג)(1)): a term that automatically continues
  the deal after its end date has no effect.
- **Renewals** (s.13א(ג)(2)): an extension needs the consumer's agreement. In
  the first 30 days of an extension the dealer may not raise the price or worsen
  terms, and the consumer may withdraw.
- **Oral disclosure** (s.13ג(ב)(1)): disclose the right to cancel an ongoing
  transaction, including an open-ended one, before the deal is made (check how
  this applies to online sign-ups).
- **Ending** (s.13ד(ג)): an ongoing transaction ends within three business days
  of a cancellation notice given under s.14ט.
- **Trials and introductory prices:** check the benefit-period rules (UNV:
  s.13ב; confirm it).
- **Evidence:** renewal and billing jobs (cron, Stripe or Cardcom
  subscriptions), the reminder email and its timing, cancellation in the
  account settings by the same channel the user joined through, proration and
  refund logic, and that billing stops within three business days.

### 4.7 Terms of service and standard contracts (`statute`: S-SCL)

Draft terms only for the product that actually exists. For account or paid
services cover:
- service scope and availability;
- charges, renewal and price changes;
- termination by either side;
- support;
- user content license and moderation;
- the consumer rights that apply (cancellation, refund);
- governing law and venue.

Screen every clause against the Standard Contracts Law's unfair-term
presumptions (UNV: for example unilateral changes, broad liability exclusions,
waiving rights, and venue that disadvantages the customer; confirm the list in
s.4). A consumer term cannot remove statutory rights. Keep platform terms
(platform to user) separate from seller terms (seller to buyer) where both
exist.

### 4.8 Content and intellectual property

- **Copyright Law 2007 (S-COPYRIGHT, KO; latest publication 2026-07-28, check
  what changed):** licensing of fonts, images, music and footage; user-content
  licenses in the terms; takedown handling. There is no statutory DMCA-style
  safe harbor (UNV: Israeli practice is driven by case law).
- **Defamation Law (S-DEFAMATION):** reviews and user posts.
- **Sponsored content and affiliate links:** label them (CPL s.7 and CPA
  positions, UNV).

### 4.9 Call recording for certain sales: CPL Amendment 74 (`statute`, enacted, not yet in force, KO)

Published 2026-07-22 (Sefer HaChukim 3569, p. 904). Commencement **2027-03-22**.
The minister may defer it by up to four months in total, for some or all dealers.

The obligations:
- Record voice calls to a phone number between dealer and consumer, for
  transactions with a total price of **ILS 750 or more**, whether or not the
  deal was concluded, of the types in the Ninth Schedule:
  - product sales (other than food) that involved a marketing approach by the
    dealer, unless it was a call-back the consumer asked for;
  - phone, internet or TV services;
  - gas supply;
  - loan brokerage.
- At the start of the call, tell the consumer it is recorded and that they may
  get the recording.
- Keep recordings for two years if the deal was concluded, or six months if
  not.
- Give the recording or the call details on request, free the first time.
- If the dealer fails to provide them, courts treat the dealer as admitting the
  consumer's version unless justified. The dealer needs court permission to use
  its own recording as evidence.
- Regulations may extend the duty to written chats.
- Parallel duties were added for banks, card companies, insurers, insurance
  agents, institutional bodies and extended-license financial service providers
  (see the Finance row).

Before commencement, label any finding about it "enacted, commencement
2027-03-22 (deferrable)". After commencement, re-verify the status, the Ninth
Schedule and any regulations.
