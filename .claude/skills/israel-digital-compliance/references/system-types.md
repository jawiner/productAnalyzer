# System and sector matrix

These rows are research instructions, not conclusions. Decide whether a row
applies from facts and from current authoritative sources, then verify each
trigger (see [sources.md](sources.md) and SKILL.md step 5). Rows add up. Run
every row the product matches, together with the four baseline modules in
[israel-baseline.md](israel-baseline.md) (B1 Privacy, B2 Tracking and marketing,
B3 Accessibility, B4 Consumer and contracts).

Markers (`WS`, `KO`, `SEC`, `UNV`) mean the same as in israel-baseline.md. A
law marked `KO` was found in Knesset open data on 2026-11-16, along with its
latest publication date. Its content still needs checking.

## Summary

| # | System or feature | Baseline modules usually engaged | Main authorities (verify) |
|---|---|---|---|
| 1 | Static site, portfolio, blog, landing page | B1 (logs, embeds), B3, B4 (content) | PPA, Accessibility Commission |
| 2 | Leads, CRM, newsletter, support, call center | B1, B2, B4 (call recording) | PPA, CPA, courts (spam claims) |
| 3 | B2C store, digital goods, bookings, memberships | B1–B4 | CPA, PPA, Accessibility Commission |
| 4 | Marketplace, gig platform, classifieds, seller portal | B1–B4 | CPA, PPA, payment regulators, Tax Authority |
| 5 | B2B SaaS, API, cloud or managed service | B1 (processor role), B3 if public-facing | PPA, INCD (sector cyber), customers' regulators |
| 6 | Mobile, desktop, browser extension, PWA | B1, B2, B3 (reg. 35ג) | PPA; app stores (platform requirements) |
| 7 | Internal admin, ERP, HR, recruitment, monitoring | B1 (employees) | PPA, labor courts, Equal Employment Opportunities Commission |
| 8 | Health, therapy, telemedicine, pharmacy, wellness | B1 (special sensitivity), B2, B3, B4 | Ministry of Health, PPA |
| 9 | Finance, payments, lending, investing, insurance, crypto | B1, B2, B4 | Bank of Israel, CMISA, ISA, IMPA |
| 10 | Schools, edtech, games, services used by children | B1, B2, B3, B4 | Ministry of Education, PPA |
| 11 | Government, municipalities, nonprofits, donations | B1 (public body), B2 (donation messages), B3 | National Digital Agency, PPA, Registrar of Amutot, Tax Authority |
| 12 | Community, messaging, chat, forums, uploads | B1, B4 (content) | PPA, courts |
| 13 | AI, chatbots, scoring, profiling | B1 (inference, transfers), B2 | PPA (draft AI guidance), MoIST policy, the sector regulator |
| 14 | Cameras, biometrics, IoT, location, physical access | B1 (special sensitivity, monitoring) | PPA, Ministry of Labor (workplace) |
| 15 | Travel, ticketing, hospitality, delivery | B1, B4 (special cancellation rules) | CPA, Ministry of Tourism, Civil Aviation Authority |
| 16 | Age-restricted or regulated offers and advertising | B2, B4 | Ministry of Health, police, Gambling Regulation Authority |
| 17 | Cross-border and multilingual services | B1 (transfers, EEA data), B3, B4 (language) | PPA plus foreign regulators |

Abbreviations: PPA = Privacy Protection Authority (הרשות להגנת הפרטיות). CPA =
Consumer Protection and Fair Trade Authority (הרשות להגנת הצרכן ולסחר הוגן).
Accessibility Commission = Commission for Equal Rights of Persons with
Disabilities (נציבות שוויון זכויות לאנשים עם מוגבלות). INCD = Israel National
Cyber Directorate (מערך הסייבר הלאומי). CMISA = Capital Market, Insurance and
Savings Authority (רשות שוק ההון, ביטוח וחיסכון). ISA = Israel Securities
Authority (רשות ניירות ערך). IMPA = Israel Money Laundering and Terror Financing
Prohibition Authority (הרשות לאיסור הלבנת הון ומימון טרור). MoIST = Ministry of
Innovation, Science and Technology.

---

## 1. Static site, portfolio, blog, landing page

- **Intake questions:**
  - Who operates it, and does it describe a service offered to the public?
  - Is there a hosting provider or CDN, and are access logs on (with IP and user
    agent)? How long are they kept?
  - Any forms, embeds (YouTube, Maps, social), fonts loaded from third parties,
    analytics?
  - Any sponsored or affiliate content?
  - Whose images, fonts and text are these?
- **Legal triggers to verify:**
  - Accessibility, if it supplies or describes a public service, with any
    exemption evidenced (B3).
  - PPL, if logs or embeds process personal data (B1).
  - CPL s.2 and s.7 on claims (B4).
  - Copyright Law on assets (S-COPYRIGHT).
- **Customer-facing surfaces:**
  - an accessibility statement, if bound;
  - a privacy notice only if personal data is actually processed (logs,
    embeds);
  - sponsored-content labels.
- **Operational controls:** log retention setting; embed privacy modes (for
  example youtube-nocookie with click-to-load); asset license records.
- **Authorities to consult:** Accessibility Commission; PPA.
- **Concrete test:**
  - Load every page with network capture and list third-party requests. An
    empty list plus logs off supports "no tracking, no consent tool needed".
  - Run axe and a keyboard pass on each template.
  - **Do not** invent a cookie-banner or checkout requirement when there is no
    tracking and no sale.

## 2. Leads, CRM, newsletter, support, call center

- **Intake questions:**
  - What does each form or channel collect, and where does it go (CRM, ESP,
    spreadsheet, WhatsApp)?
  - Are calls recorded or transcribed? What do the scripts say?
  - How is consent captured, and where is it stored?
  - Is there a suppression list? Do vendors (call centers, CRM admins) have
    access?
  - Are leads bought or enriched? What are the retention rules?
- **Legal triggers to verify:**
  - s.11 at every capture point (B1 1.2).
  - s.30A for promotional sends (B2 2.4).
  - Direct mailing when segmenting by characteristics (B2 2.5).
  - Security regulations for the CRM: medium level if it is a direct-mailing
    database (B1 1.6).
  - Outsourcing to vendors (reg. 15).
  - Purpose limitation on reusing support data (B1 1.3).
  - CPL Amendment 74 call recording for covered sales of ILS 750 or more, from
    2027-03-22 (B4 4.9).
- **Customer-facing surfaces:**
  - a notice under each form;
  - a separate, unchecked marketing opt-in;
  - "פרסומת" labeling and an unsubscribe route in every send;
  - a recording announcement at call start.
- **Operational controls:**
  - consent records (text version, time, channel);
  - suppression checked in the send path;
  - CRM roles and access reviews;
  - retention jobs for stale leads;
  - recording retention (2 years or 6 months under A74);
  - vendor DPAs.
- **Authorities to consult:** PPA; CPA (A74); counsel on class-action exposure
  under s.30A.
- **Concrete test:**
  - Submit a synthetic lead without ticking opt-in, then trigger a campaign
    send in staging. The lead must not receive it.
  - Unsubscribe from an email. The next scheduled send must skip the address,
    as shown in the ESP log.

## 3. B2C online store, digital goods, bookings, memberships

- **Intake questions:**
  - Who is the dealer, and are its legal name, ID and address shown?
  - What is sold (physical goods, digital, services, bookings)?
  - Price composition (VAT, shipping, fees)? Trials, subscriptions, renewal?
  - Payment provider, and who sends the confirmation?
  - Delivery terms, warranty, cancellation handling, refund method?
- **Legal triggers to verify:**
  - Distance-sale disclosure (s.14ג(א)) and the written document (s.14ג(ב)).
  - Cancellation windows and exceptions (s.14ג(ג), s.14ג1, the regulations).
  - Consequences (s.14ה) and the homepage link (s.14ט).
  - Ongoing transactions (ss.13א–13ד).
  - Price display (B4 4.2) and the card-minimum ban (A72).
  - Accessibility of checkout (B3).
  - Tracking on checkout pages (B2).
- **Customer-facing surfaces:**
  - seller details and the total price before payment;
  - cancellation terms near the buy button;
  - a "ביטול עסקה" homepage link with a working form;
  - a confirmation email with the required details;
  - renewal notices;
  - an in-account cancellation option.
- **Operational controls:**
  - the cancellation intake queue with time limits;
  - refund execution within the statutory period;
  - a renewal-reminder job;
  - billing stops within three business days of cancellation;
  - category-exception tagging on products (for example perishable, or made to
    order).
- **Authorities to consult:** CPA; Accessibility Commission; PPA.
- **Concrete test:**
  - Place a synthetic order and check the email holds every required field.
  - Submit the homepage cancellation form as a guest and confirm a record and a
    confirmation.
  - Cancel a test subscription and confirm no further charge in the billing
    sandbox.

## 4. Marketplace, gig platform, classifieds, seller portal

- **Intake questions:**
  - Who is the seller of record?
  - Who collects funds: the platform, a payment facilitator, or the seller
    directly?
  - Who issues invoices or receipts? Who handles refunds, disputes and
    chargebacks?
  - How are sellers and gig workers verified, and what buyer data goes to
    sellers?
  - How are reviews moderated?
- **Legal triggers to verify:**
  - Which party is the "dealer" for each CPL duty (it can be both).
  - Payment-services licensing if the platform holds or transfers funds for
    others (S-PAYMENT-LICENSING, KO; check the activity against the law and the
    regulator).
  - Tax invoicing duties (UNV: Israel Invoices allocation numbers for B2B
    invoices over a falling threshold; verify with the Tax Authority).
  - Sharing buyer data with sellers (B1 1.3, recipients in s.11).
  - Misleading or fake reviews (B4 4.2).
- **Customer-facing surfaces:**
  - "Sold by {{SELLER}}" on the listing and in checkout;
  - each seller's identity and cancellation policy;
  - platform terms kept separate from seller terms;
  - a dispute route;
  - review authenticity labels.
- **Operational controls:**
  - seller onboarding (KYC where required);
  - payout flows;
  - who receives cancellation notices and how they are routed;
  - seller access limited to their own orders;
  - review moderation logs.
- **Authorities to consult:** CPA; ISA or the Bank of Israel for payment
  activity (verify which); Tax Authority; PPA.
- **Concrete test:**
  - Trace one synthetic order's money flow through the code and config: which
    account receives funds and who triggers the refund.
  - Confirm a seller account cannot read another seller's buyer data (an
    authorization test against the API).

## 5. B2B SaaS, API, cloud or managed service

- **Intake questions:**
  - For each data flow: is the operator the controller (its own account and
    billing data) or a holder or processor (the customer's data)?
  - Are tenants isolated? Who are the subprocessors, and where?
  - Do customers send EEA data? What do DPAs promise?
  - Who are the customers (regulated sectors, public bodies)?
- **Legal triggers to verify:**
  - Holder duties under the security regulations, and outsourcing terms from
    the customer's side (reg. 15).
  - Transfers abroad (B1 1.7) and EEA-origin data (B1 1.8).
  - The privacy officer screen (s.17ב1) where the operator itself does
    large-scale sensitive processing.
  - Sector cyber rules flowing down from regulated customers (`contract
    requirement`).
  - Consumer law usually does not apply to B2B. Verify the customer types and
    do not import B2C obligations.
- **Customer-facing surfaces:**
  - a DPA or processing terms;
  - a subprocessor list with change notices;
  - a security and trust page (state only verified controls);
  - a public status and incident communication route.
- **Operational controls:**
  - tenant isolation (RLS, scoped keys);
  - an admin access log;
  - support access by just-in-time grant;
  - per-tenant deletion and export;
  - backup expiry;
  - an incident notification runbook aligned to customer contracts.
- **Authorities to consult:** PPA; INCD guidance (`best practice` unless a sector
  rule binds); the customers' sector regulators.
- **Concrete test:**
  - Run a cross-tenant read attempt with tenant A's token on tenant B's resource
    ID. It must return 403 or 404.
  - Run a tenant deletion job against synthetic data and confirm rows, files
    and search entries are removed, with a stated backup-expiry period.

## 6. Mobile, desktop, browser extension, PWA

- **Intake questions:**
  - Which OS permissions are requested, when, and why?
  - Any background collection (location, sensors, contacts)? Which SDKs?
  - Can users delete their account in the app? What happens on uninstall?
  - Extension host permissions and data handling? Push notifications?
- **Legal triggers to verify:**
  - s.11 at each permission request (B1 1.2) and special sensitivity for
    location (B1 1.1).
  - Tracking SDKs (B2).
  - Accessibility of apps (reg. 35ג).
  - Platform rules as `platform requirement`: App Store account deletion and
    privacy labels, Google Play Data safety and account deletion, Chrome Web
    Store Limited Use. Verify current policy text.
- **Customer-facing surfaces:**
  - a pre-permission explanation screen;
  - store privacy labels that match the SDK inventory;
  - in-app account deletion and its web link;
  - notification settings.
- **Operational controls:**
  - SDK inventory checked in CI against store labels;
  - no SDK initialization before consent where opt-in is relied on;
  - a server-side deletion job.
- **Authorities to consult:** PPA; Apple and Google policy pages.
- **Concrete test:**
  - Install a fresh build and capture traffic before any prompt or choice:
    list SDK calls.
  - Deny location and confirm no location fields in outgoing requests.
  - Request deletion and confirm the server record is gone or scheduled, per
    stated policy.

## 7. Internal admin, ERP, HR, recruitment and monitoring

- **Intake questions:**
  - Whose data is it: employees, applicants, contractors?
  - What monitoring happens: email, screens, keystrokes, geolocation, cameras,
    biometrics?
  - Are devices shared? Who can see audit logs? What are the retention rules
    for applicants?
- **Legal triggers to verify:**
  - PPL duties toward employees (B1).
  - Labor case law on monitoring (UNV: the National Labor Court's Isakov
    principles of legitimacy, transparency, proportionality and purpose).
  - PPA guidance on remote work (S-PPA-REMOTEWORK, not fetched) and workplace
    biometrics (S-PPA-BIOMETRIC-WORK, not fetched).
  - PPA recruitment guidance (S-PPA-RECRUITMENT, not fetched).
  - Equal Employment Opportunities Law on applicant questions (UNV).
  - Consent under dependency is suspect (S-PPA-CONSENT, SEC).
- **Customer-facing surfaces:**
  - an employee privacy notice describing each monitoring tool, its purpose,
    scope and retention;
  - an applicant notice on the job form;
  - camera signage where relevant;
  - an alternative to biometrics.
- **Operational controls:**
  - a proportionality assessment for each monitoring tool;
  - access to monitoring data restricted and logged;
  - retention limits (applicant data deleted after the stated period);
  - no monitoring of private spaces or private accounts;
  - a works-council or union process where relevant.
- **Authorities to consult:** PPA; labor counsel (name "labor counsel"
  specifically in each finding's Review needed field, not just "counsel"); Equal
  Employment Opportunities Commission.
- **Concrete test:**
  - Search the code for monitoring hooks (screenshot timers, location pings) and
    confirm each matches the notice.
  - Confirm an HR viewer role cannot export monitoring data without an audit
    log entry.

## 8. Health, therapy, telemedicine, pharmacy and wellness

- **Intake questions:**
  - Is it a clinical service (licensed practitioners, diagnosis, treatment) or
    wellness?
  - Who are the providers and what licences do they hold?
  - What intake questions are asked? Where are records stored?
  - Do analytics or ad tools run on intake or result pages? Is it
    prescription-related?
- **Legal triggers to verify:**
  - Health data is special-sensitivity data (B1 1.1).
  - Patient's Rights Law on confidentiality and medical records (S-PATIENT, KO,
    latest publication 2025-04-03).
  - Ministry of Health circular on telemedicine (S-MOH-TELEMED, not fetched).
  - Licensing of practitioners and pharmacies.
  - Advertising limits for medical services and medicines (UNV).
  - The privacy officer screen (large-scale health processing).
  - Security regulations: medium or high level.
- **Customer-facing surfaces:**
  - an intake notice with prominent special-sensitivity disclosure
    (notices.md §1c, placed before the first health question);
  - an explicit statement of clinical versus wellness scope;
  - records access route;
  - no misleading health claims.
- **Operational controls:**
  - no health context in URLs, page titles or event names sent to vendors;
  - analytics and pixels excluded from intake and result routes;
  - access by treating role;
  - audit logs;
  - record retention per medical-records rules (verify);
  - encryption.
- **Authorities to consult:** Ministry of Health; PPA; professional councils.
  Always record the privacy-officer and notification screen (baseline 1.9) as a
  finding for this row.
- **Concrete test:**
  - Fill a synthetic intake with network capture on. Confirm no request to
    analytics or ad domains contains form values, condition names or
    identifying route parameters.
  - Check server-side event relays too.

## 9. Finance, payments, lending, investing, insurance and crypto

- **Intake questions:**
  - What is the exact activity: payment processing, holding funds, payment
    initiation, credit, P2P lending, investment advice or management, insurance
    distribution, virtual assets?
  - Which licences does the operator or its partners hold?
  - Does card data ever touch the servers?
  - What KYC and AML is in place?
- **Legal triggers to verify:**
  - Licensing by activity (S-REG-FIN-SERVICES, S-PAYMENT-LICENSING,
    S-PAYMENT-SERVICES, S-FIN-INFO; all KO with 2026 updates).
  - Credit data rules (S-CREDIT-DATA, KO, Amendment 6 published 2026-07-26).
  - AML duties for the activity (S-AML, KO, updated 2026-07-27).
  - Financial disclosure and marketing rules.
  - Parallel call-recording duties added by CPL A74 for banks, card companies,
    insurers, institutional bodies and extended-license providers, from
    2027-03-22 (S-CPL-A74, KO).
  - Sector cyber directives.
  - PCI DSS as `contract requirement`.
- **Customer-facing surfaces:**
  - licence disclosures;
  - fee and interest disclosures;
  - risk warnings;
  - the regulated entity's identity where a partner is licensed;
  - recording notices.
- **Operational controls:**
  - card data only in provider-hosted fields or iframes (tokenization);
  - a KYC workflow;
  - transaction monitoring;
  - recording retention;
  - an outsourcing register for regulated outsourcing;
  - segregation of client funds.
- **Authorities to consult:** Bank of Israel (Supervisor of Banks, payment
  systems); CMISA; ISA; IMPA. Verify which regulator licenses the exact activity.
- **Concrete test:**
  - Grep the code and logs for PAN-like patterns and card fields in your own
    forms. Confirm checkout uses the provider's hosted component.
  - Map each financial activity to a licence number or a licensed partner.

## 10. Schools, edtech, games and services accessed by children

- **Intake questions:**
  - Who is the operator: the school, the ministry, or the vendor?
  - Is it child-directed or general-audience with known children?
  - Ages? Do parents or teachers create accounts? Are there chat, ads or
    in-app purchases?
  - Does the AI tutor see student inputs? Where is data stored?
- **Legal triggers to verify:**
  - Capacity of minors and guardian consent (S-CAPACITY, KO, latest
    publication 2026-01-18; check the amendment).
  - PPA student privacy guide (S-PPA-STUDENTS, not fetched).
  - Ministry of Education rules for approved tools and data (UNV).
  - PPA draft on age assurance (June 2026, `draft`, SEC).
  - Targeted ads to children.
  - Purchases by minors (CPL plus capacity).
  - AI inputs (row 13).
- **Customer-facing surfaces:**
  - age-appropriate notices for children and full notices for parents and
    schools;
  - no dark patterns;
  - parental controls;
  - purchase confirmations aimed at a guardian.
- **Operational controls:**
  - data minimization (no precise location, no contact lists);
  - ads off or contextual only;
  - chat moderation and abuse reporting (Penal Law reporting duties, UNV);
  - student data not reused for model training;
  - school data processing agreements.
- **Authorities to consult:** Ministry of Education; PPA.
- **Concrete test:**
  - Create a synthetic child account and confirm no ad SDK or third-party
    tracker loads.
  - Confirm tutor prompts sent to the AI provider exclude names and IDs where
    possible, and that the provider's retention and training settings are off,
    as shown in the API configuration.

## 11. Government, municipalities, nonprofits and donations

- **Intake questions:**
  - Is the operator a public body (including government companies)? Under what
    statutory authority does it collect data?
  - Data sharing between bodies? Freedom of information duties?
  - For nonprofits: donations online, receipts, solicitations by email or SMS?
- **Legal triggers to verify:**
  - Public-body duties under the PPL (registration, privacy officer, sharing
    between bodies; UNV: PPL chapter D).
  - Accessibility, including video (reg. 35ד applies to public bodies).
  - Freedom of Information Law (S-FOI, KO, updated 2026-04-29).
  - Digital Communication with Public Bodies Law, Amendment 5 published
    2026-07-20 (KO).
  - Amutot Law (S-AMUTOT, KO).
  - Donation receipts (UNV: Income Tax Ordinance s.46; check the Tax
    Authority's digital receipt rules).
  - s.30A donation messages and the nonprofit email exception (B2 2.4).
- **Customer-facing surfaces:**
  - a statutory-authority statement in s.11 notices (is disclosure mandatory?);
  - an accessibility statement with coordinator details;
  - donation terms;
  - receipt information;
  - "בקשת תרומה" labeling.
- **Operational controls:**
  - records management;
  - a data-sharing approvals log;
  - a donation receipt issuance flow;
  - restricted-donation tracking.
- **Authorities to consult:** National Digital Agency; PPA; Registrar of Amutot;
  Tax Authority.
- **Concrete test:**
  - Make a synthetic donation and confirm a receipt with the required fields
    (verify the fields with the Tax Authority).
  - Check that the SMS and email templates carry the correct label and refusal
    route.

## 12. Community, messaging, chat, forums and user uploads

- **Intake questions:**
  - What is public, what is private, and who can see what?
  - How do reporting and moderation work, and how fast are takedowns?
  - Can minors use it? Can users export or delete content?
  - Do uploads keep EXIF metadata? Are DMs end-to-end encrypted or readable by
    staff?
- **Legal triggers to verify:**
  - PPL on publishing personal information (UNV: infringement includes
    publishing private matters).
  - Intimate image offenses (UNV: Prevention of Sexual Harassment Law).
  - Defamation Law (S-DEFAMATION).
  - Copyright Law on uploads (S-COPYRIGHT).
  - Child protection reporting duties (UNV: Penal Law).
  - Retention and export (B1 1.4).
- **Customer-facing surfaces:**
  - visibility labels at post time;
  - a report button on every item;
  - community rules;
  - a takedown and contact route;
  - export and deletion controls.
- **Operational controls:**
  - a moderation queue with service levels and logs;
  - EXIF stripped on upload;
  - staff access to private messages restricted and logged;
  - a legal-request handling procedure;
  - deletion propagated to backups and CDN caches.
- **Authorities to consult:** PPA; counsel for takedown and unmasking
  requests.
- **Concrete test:**
  - Upload a synthetic image with GPS EXIF, download it from the public URL,
    and confirm the metadata is gone.
  - Report a post and confirm it reaches the queue with a timestamp.

## 13. AI, chatbots, scoring and profiling

- **Intake questions:**
  - Which models and providers, and in which regions? What personal data goes
    into prompts, retrieval indexes and fine-tuning?
  - Are prompts and outputs logged? Do providers train on them?
  - Are there automated decisions with significant effects (credit, hiring,
    pricing)? Is there human review?
  - Is the user told they are talking to a bot?
- **Legal triggers to verify:**
  - The PPL applies to personal data in training and in use, and to inferences
    (`regulator interpretation`; PPA draft guidance of 2025-04-28 is a `draft`,
    SEC; check whether it has been finalized, S-PPA-AI).
  - Purpose limitation on reusing data for training (B1 1.3).
  - Transfers to providers abroad (B1 1.7).
  - Sector rules (finance, health, employment).
  - The MoIST AI policy is non-binding (`regulator interpretation`, UNV).
  - EU AI Act if offered in the EU (row 17).
- **Customer-facing surfaces:**
  - a bot disclosure;
  - a notice on what is sent to which provider;
  - a human-contact route;
  - a statement of limits;
  - an opt-out of training where data is reused.
- **Operational controls:**
  - redaction before prompts;
  - provider zero-retention or no-training settings;
  - prompt-log retention and access;
  - an evaluation and bias review for scoring;
  - human review of significant decisions;
  - a model and provider register.
- **Authorities to consult:** PPA; the sector regulator; MoIST policy pages.
- **Concrete test:**
  - Send a synthetic message containing an ID number and a phone number, then
    inspect the outgoing provider request: is redaction applied as documented?
  - Check the retention configuration of the prompt log against the stated
    period.

## 14. Cameras, biometrics, IoT, location and physical access

- **Intake questions:**
  - What is captured (video, audio, face templates, fingerprints, location
    traces)? Where, and is it necessary?
  - Do workers and bystanders appear? Is there remote vendor access?
  - Retention? Signage?
- **Legal triggers to verify:**
  - Biometric identifiers and location are special-sensitivity data (B1 1.1).
  - PPA guidance on workplace biometrics (S-PPA-BIOMETRIC-WORK) and on cameras
    (UNV: the PPA guidance on surveillance cameras in workplaces and public
    spaces).
  - The privacy officer screen (systematic monitoring at significant scale).
  - Security regulations: likely high level.
  - Safety rules for physical devices where relevant.
- **Customer-facing surfaces:**
  - signage at entrances;
  - a worker notice;
  - an app permission rationale;
  - an alternative to biometric enrollment.
- **Operational controls:**
  - a necessity and proportionality assessment;
  - templates stored instead of images, where possible;
  - encryption;
  - retention limits;
  - vendor remote access by named account and logged;
  - firmware update policy.
- **Authorities to consult:** PPA; Ministry of Labor and labor counsel for
  workplace use.
- **Concrete test:**
  - Confirm the retention job deletes footage or templates older than the
    stated period (on synthetic data).
  - Confirm vendor support access needs an approval step and leaves a log
    entry.

## 15. Travel, ticketing, hospitality and delivery

- **Intake questions:**
  - Is the operator the provider or an intermediary (agent, OTA, reseller)?
  - Is the service in Israel or abroad? Flights?
  - Cancellation policy per supplier? Delivery and location tracking of
    couriers and customers?
- **Legal triggers to verify:**
  - CPL cancellation exceptions and special rules for accommodation, travel
    and leisure, and for services performed abroad (B4 4.4;
    S-CANCEL-REGS reg. 6(א)(12), WS: the exclusion applies only if the
    cancellation terms were disclosed before the contract).
  - Aviation Services Law on flight cancellation compensation (S-AVIATION, KO,
    updated 2025-02-11).
  - Travel agent licensing (UNV: Ministry of Tourism).
  - Location data (B1 1.1).
- **Customer-facing surfaces:**
  - who the provider is;
  - cancellation terms per booking, before payment;
  - flight-rights information where relevant;
  - a tracking-link privacy notice.
- **Operational controls:**
  - supplier terms mapped to the booking;
  - refund routing between intermediary and supplier;
  - courier location data retention limits.
- **Authorities to consult:** CPA; Ministry of Tourism; Civil Aviation
  Authority.
- **Concrete test:**
  - Book a synthetic abroad-only package and confirm the cancellation terms
    are displayed before payment and repeated in the confirmation.
  - Confirm courier location stops being collected after delivery.

## 16. Age-restricted or regulated offers and advertising

- **Intake questions:**
  - What exactly is offered: tobacco or e-cigarettes, alcohol, gambling or
    betting, cannabis, medicines, firearms, financial products?
  - Is it a sale, advertising only, or both? Which channels?
  - How is age verified?
- **Legal triggers to verify:**
  - Tobacco advertising and marketing restrictions (UNV: the Tobacco
    Advertising and Marketing Restriction Law).
  - Alcohol sale and advertising limits (UNV).
  - Gambling is prohibited except by licensed bodies (UNV: Penal Law).
  - Medicines advertising (UNV).
  - Each depends on product classification and channel. Verify the current
    law for the exact product.
- **Customer-facing surfaces:**
  - an age gate where sale is permitted;
  - mandatory warnings;
  - removed advertising where prohibited.
- **Operational controls:**
  - age verification at delivery;
  - ad-platform category settings;
  - geo restrictions.
- **Authorities to consult:** Ministry of Health; Israel Police; Gambling
  Regulation Authority (UNV); the relevant licensing body.
- **Concrete test:**
  - Attempt a checkout of a restricted product with a synthetic underage
    profile and confirm it is blocked server-side, not only in the UI.

## 17. Cross-border and multilingual services

- **Intake questions:**
  - Where are the operator, users, servers and vendors?
  - Is the product offered to EU or UK users (currency, language, shipping)?
  - Does EEA data come in? Which languages are offered (Hebrew, Arabic,
    English, Russian)?
- **Legal triggers to verify:**
  - Israeli nexus per regime (applicability tests in israel-baseline.md).
  - GDPR art. 3(2), art. 27 representative, and art. 44 onward (S-GDPR, UNV).
  - EEA-origin data rules in Israel (B1 1.8).
  - Transfers abroad (B1 1.7).
  - Consumer document language: Hebrew or the language of marketing (B4 4.3).
  - Accessibility of every language version (B3).
- **Customer-facing surfaces:**
  - language versions of notices that match each other;
  - a jurisdiction-specific section where foreign law applies;
  - RTL correctness.
- **Operational controls:**
  - a data map by country;
  - transfer basis per vendor;
  - translation review by a legal-language reviewer.
- **Authorities to consult:** PPA; the foreign regulator (an EU lead supervisory
  authority if established there).
- **Concrete test:**
  - Compare the Hebrew and English policies section by section. The facts
    (vendors, retention, rights) must match.
  - Switch the language to Hebrew and run the RTL and screen reader pass on
    the checkout.

---

## Unlisted activity route

For an industry with no row:

1. **Name the activity precisely**, as a verb: "arranges loans", "dispenses
   medicine", "brokers real estate", "sells ammunition".
2. **Find the licensing or supervising authority.** Search official sources
   (gov.il ministries, the Knesset legislation database) for "רישיון" plus the
   activity.
3. **Find the primary law and its regulations.** Use the Knesset open-data
   lookup in [sources.md](sources.md) and record the law ID and latest
   publication date.
4. **Map the activity to baseline modules** and to the closest rows above.
5. **Record every element** as `applicability unknown` until verified, and name
   who must confirm it (counsel or the regulator).
