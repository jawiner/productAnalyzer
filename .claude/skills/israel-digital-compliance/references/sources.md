# Source register

Skill written and sources last checked: **2026-11-16**. Every entry says how it
was verified. Nothing here is current law until a finding re-checks it (SKILL.md
step 5). Use the Hebrew official text where versions differ.

## Verification methods

| Code | Method | What it proves |
|---|---|---|
| `KO` | Knesset open data (OData), `KNS_IsraelLaw` and `KNS_Bill` | The law ID, validity (תקף/בטל), the latest publication date, and amendment summaries. Official metadata, not the text. |
| `WS` | Hebrew Wikisource consolidated text (he.wikisource.org) | Section wording and numbering, for orientation. **Unofficial.** Confirm against the official text before it backs a finding. |
| `GOV-PDF` | A gov.il BlobFolder PDF was read directly | That document's content and date |
| `SEC` | Secondary sources (law-firm alerts, Kol Zchut, press) | That the document exists and roughly what it says. Not its wording. |
| `HTTP` | The URL answered 200 to a plain request | Only that the URL resolves |
| `NF` | Not fetched: gov.il `pages/` and `service/` URLs returned HTTP 403 to automated clients on 2026-11-16, and Knesset legislation pages render only with JavaScript | Nothing. A person must open it in a browser. |
| `UNV` | Background knowledge | Nothing. Verify before use. |

Legal status vocabulary: `in force`; `enacted, not yet in force`; `final regulator
interpretation` (not binding law, but shows enforcement position); `draft for
comment`; `bill`; `consultation`; `platform policy`; `contract or industry
standard`.

## Privacy and data governance

| ID | Instrument | Sections relied on | Status | Effective | URL | Verified |
|---|---|---|---|---|---|---|
| S-PPL | חוק הגנת הפרטיות, התשמ"א-1981 (Privacy Protection Law). Knesset law ID 2000234 | s.1, 2, 3 (definitions incl. מידע בעל רגישות מיוחדת), 8א, 11, 13, 14, 17ב1, chapter B1 (direct mailing), chapter D (public bodies) | in force | Latest publication 2024-08-14 | https://main.knesset.gov.il/apps-lgs/legislation/main/laws/2000234 ; WS: https://he.wikisource.org/wiki/חוק_הגנת_הפרטיות | 2026-11-16 KO (status, date); WS (ss.3, 8א, 11, 13, 14, 17ב1). Chapter B1 and s.1–2: UNV |
| S-A13 | חוק הגנת הפרטיות (תיקון מס' 13), התשפ"ד-2024. Sefer HaChukim 3287 p.1430, Bill ID 2167975 | Whole amendment: definitions, processing limits, registration narrowed to public bodies and data traders (10,000+), privacy officer duty | in force | Published 2024-08-14 (KO); in force 2025-08-14 (SEC) | as S-PPL | 2026-11-16 KO (publication, official summary); commencement SEC |
| S-PPA-A13-GUIDE | PPA professional guide to Amendment 13 | Interpretation of A13 | regulator interpretation | UNV | https://www.gov.il/he/pages/guide_tikon13_professional | NF |
| S-PPA-S11 | PPA page on the s.11 duty to notify | s.11 practice | regulator interpretation | UNV | https://www.gov.il/he/pages/duty_to_notify | NF |
| S-PPA-CONSENT | PPA opinion on consent (גילוי דעת בנושא הסכמה) | Informed consent; notice as a minimum; specificity; prominence; dependency | final regulator interpretation | 2026-02-25 (SEC) | https://www.gov.il/he/pages/consent-2026 | NF; content SEC only (Shibolet, Goldfarb, Gornitzky alerts found by search 2026-11-16) |
| S-PPA-DPO | PPA opinion on appointing a privacy officer under A13 | Meaning of the s.17ב1 triggers | final regulator interpretation (SEC) | 2026-07-14 (SEC) | URL not located; search gov.il PPA publications | SEC |
| S-PPA-AGE | PPA draft on age-assurance methods | Children, age checks | draft for comment | June 2026 (SEC) | URL not located | SEC |
| S-PPA-AI | PPA draft guidance: application of the PPL to AI systems | Lawful basis, informed consent, transparency, officer, PIA | draft for comment (no final version found 2026-11-16) | Draft published 2025-04-28 (SEC) | https://www.gov.il/he/pages/ai_reg | NF; SEC |
| S-PPL-INSPECT-REGS | תקנות הגנת הפרטיות (תנאי עיון במידע וסדרי הדין בערעור), התשמ"א-1981 | Inspection timing and procedure | in force (UNV) | UNV | not located | UNV |
| S-SEC-REGS | תקנות הגנת הפרטיות (אבטחת מידע), התשע"ז-2017 | regs 2, 5, 10, 11, 15, 16, 17; schedules 1–2 (security levels) | in force | UNV: in force since 2018-05-08. WS shows no amendments; check whether A13 terminology changes affect it. | https://www.gov.il/he/pages/data_security_regulation ; WS: https://he.wikisource.org/wiki/תקנות_הגנת_הפרטיות_(אבטחת_מידע) | 2026-11-16 WS; gov.il NF |
| S-PPA-OUTSOURCING | PPA guidance on outsourcing and security (reg. 15) | Vendor terms | regulator interpretation | UNV | https://www.gov.il/he/pages/data_security_outsourcing | NF |
| S-TRANSFER-REGS | תקנות הגנת הפרטיות (העברת מידע אל מאגרי מידע שמחוץ לגבולות המדינה), התשס"א-2001. Kovetz HaTakanot 5761 p.900 | reg. 1 (adequate level), reg. 2 (alternatives), reg. 3 (written undertaking) | in force | Six months after publication in 2001 (WS) | WS: https://he.wikisource.org/wiki/תקנות_הגנת_הפרטיות_(העברת_מידע_אל_מאגרי_מידע_שמחוץ_לגבולות_המדינה) | 2026-11-16 WS (no amendments shown) |
| S-PPA-TRANSFER-INTERP | PPA opinion: interpretation of reg. 3 of the Transfer Regulations, dated 13 Oct 2024 | The bar on onward transfer does not apply if the Israeli database owner gave written consent. The onward transfer must itself meet reg. 1 or 2 as if made directly from Israel. The scope of the reg. 3 undertaking need not reach the "maintain Israeli conditions" contract of reg. 2(4). The undertaking may rely on other accepted guarantees, for example a commitment to GDPR or to the law of a country with an EU adequacy decision (para. 8). Where the transfer is part of outsourcing, or an external party gets access to the Israeli database, Security Regulations reg. 15 applies (para. 9). It refers to a separate July 2024 **draft** opinion on reg. 2(4), a 2023 PPA guide to implementing reg. 15, and PPA guideline 2/2011 on outsourcing. | final regulator interpretation | 2024-10-13 | https://www.gov.il/BlobFolder/reports/takana3/he/regulation3.pdf | 2026-11-16 GOV-PDF (both pages read) |
| S-EEA-REGS | תקנות הגנת הפרטיות (הוראות לעניין מידע שהועבר לישראל מהאזור הכלכלי האירופי), התשפ"ג-2023. Kovetz HaTakanot 5783 p.1720 | regs 2 (scope), 3 (deletion), 4 (retention), 5 (accuracy), 6 (notice, onward transfer), 9 (commencement) | in force | Published 2023-05-07. New data: +3 months. Existing data: +1 year. reg. 2(a)(2) deletion item: 2025-01-01 | https://www.gov.il/he/pages/europe_transfer ; WS: https://he.wikisource.org/wiki/תקנות_הגנת_הפרטיות_(הוראות_לעניין_מידע_שהועבר_לישראל_מהאזור_הכלכלי_האירופי) | 2026-11-16 WS; gov.il NF |
| S-PPA-REGISTRATION | PPA service page: database registration | s.8א procedure | regulator service page | n/a | https://www.gov.il/he/service/registration_in_the_database | NF |
| S-PPA-NOTICE | PPA service page: notice duty (100,000+ special-sensitivity) | s.8א(ב) procedure | regulator service page | n/a | https://www.gov.il/he/service/notice-obligation | NF |
| S-PPA-STUDENTS | PPA guide on student privacy | Children and edtech row | regulator interpretation | UNV | https://www.gov.il/he/pages/students_privacy_guide | NF |
| S-PPA-REMOTEWORK | PPA guidance on remote work | HR and monitoring row | regulator interpretation | UNV | https://www.gov.il/he/pages/remotework | NF |
| S-PPA-BIOMETRIC-WORK | PPA guidance on biometrics in the workplace | HR and biometrics rows | regulator interpretation | UNV | https://www.gov.il/he/pages/biometric_workplace | NF |
| S-PPA-RECRUITMENT | PPA guidelines on recruitment (PDF) | Applicant data | regulator interpretation | UNV | https://www.gov.il/BlobFolder/legalinfo/recruitment_guidelines/he/recruitment_guidelines_02..pdf | 2026-11-16 HTTP only |

## Tracking and marketing

| ID | Instrument | Sections relied on | Status | Effective | URL | Verified |
|---|---|---|---|---|---|---|
| S-COMM | חוק התקשורת (בזק ושידורים), התשמ"ב-1982 (Communications Law). Knesset law ID 2000002 | s.30א (advertisements: channels, consent, exceptions, nonprofit (ב1), labeling (ה), refusal (ד), damages (י)) | in force | Latest publication 2026-07-28 | https://main.knesset.gov.il/apps-lgs/legislation/main/laws/2000002 ; WS: https://he.wikisource.org/wiki/חוק_התקשורת_(בזק_ושידורים) | 2026-11-16 KO; WS (s.30א) |
| S-BROADCAST-2026 | חוק התקשורת (שידורים), התשפ"ו-2026 (new Broadcasting Law). Sefer HaChukim 3572 p.992 | **Open question:** whether it renames S-COMM, moves sections, or amends s.30א. WS still showed the old name on 2026-11-16. | enacted (commencement UNV) | Published 2026-07-28 | Knesset bill ID 1042100 | 2026-11-16 KO (publication only; no summary in open data) |
| S-SPAM-PAGE | gov.il page on the anti-spam rules (seed link; publisher not confirmed) | s.30א practice | regulator page | UNV | https://www.gov.il/he/pages/17052018_7 | NF |

## Consumer protection and contracts

| ID | Instrument | Sections relied on | Status | Effective | URL | Verified |
|---|---|---|---|---|---|---|
| S-CPL | חוק הגנת הצרכן, התשמ"א-1981 (Consumer Protection Law). Knesset law ID 2000237 | s.2, 7, 13א–13ד, 14ג, 14ג1, 14ה, 14ט; price provisions (UNV) | in force | Latest publication 2026-07-28 (KO). The WS consolidation cites amendments up to Sefer HaChukim 5786 p.1029. | https://m.knesset.gov.il/apps/legislation/main/laws/2000237 ; WS: https://he.wikisource.org/wiki/חוק_הגנת_הצרכן | 2026-11-16 KO; WS (13א, 13ג, 13ד, 14ג(א)(7), 14ג(ג), 14ג1(ג), 14ה, 14ט(א),(ב),(ה),(ו)). The full s.14ג(א) list, s.14ג(ב) and the distance-sale exceptions were not read (UNV). |
| S-CPL-A70 | Amendment 70 (emergency price gouging) | Price rises after an emergency declaration | in force (UNV) | Published 2024-07-04 (KO) | Knesset bill ID 2214887 | KO |
| S-CPL-A72 | Amendment 72: no minimum purchase for card payment | Card minimums | enacted. Commencement not checked: verify. | Published 2025-04-02 (KO) | Knesset bill ID 2210645 | KO |
| S-CPL-A74 | Amendment 74: recording consumer calls (Ninth Schedule; ILS 750+). Sefer HaChukim 3569 p.904 | Recording, announcement, retention 2 years or 6 months, delivery on request, evidentiary consequences; parallel duties for financial bodies | **enacted, not yet in force** | Commencement 2027-03-22. The minister may defer it by up to four months in total. | Knesset bill ID 2219317 | 2026-11-16 KO (full official summary read) |
| S-CANCEL-REGS | תקנות הגנת הצרכן (ביטול עסקה), התשע"א-2010 | reg. 4 (refund: up to 7 business days for transactions under these regs), reg. 5 (fee: lower of 5% or ILS 100), reg. 6 (excluded goods and services) | in force | Last amendment shown 2012 (WS) | WS: https://he.wikisource.org/wiki/תקנות_הגנת_הצרכן_(ביטול_עסקה) | 2026-11-16 WS |
| S-CPA-RETURNS | CPA page on returns and cancellation | Practice | regulator interpretation | UNV | https://www.gov.il/he/pages/returns | NF |
| S-CPA-PRICES | CPA page on price display | Price display rules | regulator interpretation | UNV | https://www.gov.il/he/pages/cpfta_display_of_prices | NF |
| S-SCL | חוק החוזים האחידים, התשמ"ג-1982 (Standard Contracts Law). Knesset law ID 2000295 | s.3–4 (unfair terms, presumptions) | in force | Latest publication 2014-12-17 | https://www.gov.il/he/pages/standard-contracts | KO; NF; section content UNV |
| S-COPYRIGHT | חוק זכות יוצרים, התשס"ח-2007. Knesset law ID 2000641 | Licensing, user content | in force | Latest publication 2026-07-28. No named amendment found; possibly a consequential change from S-BROADCAST-2026 (UNV). | Knesset legislation DB | KO |
| S-DEFAMATION | חוק איסור לשון הרע, התשכ"ה-1965. Knesset law ID 2000089 | Reviews, user content | in force | Latest publication 2017-06-08 | Knesset legislation DB | KO |

## Accessibility

| ID | Instrument | Sections relied on | Status | Effective | URL | Verified |
|---|---|---|---|---|---|---|
| S-ACC-LAW | חוק שוויון זכויות לאנשים עם מוגבלות, התשנ"ח-1998. Knesset law ID 2001218 | Service-accessibility chapter | in force | Latest publication 2024-07-18 | Knesset legislation DB | KO |
| S-ACC-REGS | תקנות שוויון זכויות לאנשים עם מוגבלות (התאמות נגישות לשירות), התשע"ג-2013 | regs 35, 35א (AA; 60-day fix), 35ב, 35ג (apps), 35ד (video), 35ה (statement), 35ו (exemptions) | in force | Last amendment shown 5782 (2022) (WS) | https://www.gov.il/en/pages/internet_accessibility_regulations ; https://www.gov.il/he/pages/website_accessibility ; https://www.gov.il/he/pages/declaration_website_accessibility ; WS: https://he.wikisource.org/wiki/תקנות_שוויון_זכויות_לאנשים_עם_מוגבלות_(התאמות_נגישות_לשירות) | 2026-11-16 WS (first 100k characters; the coordinator chapter was not read); gov.il NF |
| S-IS5568 | ת"י 5568 (Israeli Standard 5568, web content accessibility guidelines) | Level AA | standard incorporated by regulation | Edition in force and its WCAG version: UNV | Standards Institution of Israel | UNV |

## Sector laws (metadata only unless stated)

All entries: KO on 2026-11-16 (law ID, validity, latest publication date). The
content of each still needs reading when its row is triggered.

| ID | Instrument | Knesset ID | Latest publication | Verified |
|---|---|---|---|---|
| S-PATIENT | חוק זכויות החולה, התשנ"ו-1996 | 2000634 | 2025-04-03 | 2026-11-16 KO |
| S-PAYMENT-SERVICES | חוק שירותי תשלום, התשע"ט-2019 | 2078352 | 2024-07-04 | 2026-11-16 KO |
| S-PAYMENT-LICENSING | חוק הסדרת העיסוק בשירותי תשלום וייזום תשלום, התשפ"ג-2023 | 2206732 | 2026-03-31 | 2026-11-16 KO |
| S-FIN-INFO | חוק שירות מידע פיננסי, התשפ"ב-2021 | 2165295 | 2026-07-26 | 2026-11-16 KO |
| S-REG-FIN-SERVICES | חוק הפיקוח על שירותים פיננסיים (שירותים פיננסיים מוסדרים), התשע"ו-2016 | 2007081 | 2026-07-22 (likely the A74 parallel recording duties; verify) | 2026-11-16 KO |
| S-CREDIT-DATA | חוק נתוני אשראי, התשע"ו-2016 (Amendment 6 published 2026-07-26: SME credit database) | 2002363 | 2026-07-26 | 2026-11-16 KO |
| S-AML | חוק איסור הלבנת הון, התש"ס-2000 | 2000084 | 2026-07-27 | 2026-11-16 KO |
| S-CAPACITY | חוק הכשרות המשפטית והאפוטרופסות, התשכ"ב-1962 | 2000326 | 2026-01-18 | 2026-11-16 KO |
| S-FOI | חוק חופש המידע, התשנ"ח-1998 | 2000657 | 2026-04-29 | 2026-11-16 KO |
| S-DIGITAL-PUBLIC | חוק תקשורת דיגיטלית עם גופים ציבוריים (Amendment 5 published 2026-07-20: voice messages for phones without SMS; language reporting) | not looked up | 2026-07-20 (amendment) | 2026-11-16 KO (amendment only; law ID not looked up) |
| S-AMUTOT | חוק העמותות, התש"ם-1980 | 2000485 | 2024-09-15 | 2026-11-16 KO |
| S-AVIATION | חוק שירותי תעופה (פיצוי וסיוע בשל ביטול טיסה או שינוי בתנאיה), התשע"ב-2012 | 2001417 | 2025-02-11 | 2026-11-16 KO |

Other sector instruments. These were not verified. Look them up when the row is
triggered:

| ID | Instrument | Status | URL |
|---|---|---|---|
| S-MOH-TELEMED | Ministry of Health Director-General circular 06/2019 on telemedicine (title UNV) | binding sector rule for MoH-supervised bodies (UNV) | https://www.gov.il/he/pages/mk06-2019 (NF) |
| S-MOIST-AI | Ministry of Innovation, Science and Technology AI regulation and ethics policy (Dec 2023, UNV) | non-binding policy | locate on gov.il |
| — | Tobacco advertising law; alcohol restrictions; Penal Law gambling provisions; medicines advertising; Equal Employment Opportunities Law; Notice to Employee Law; Income Tax Ordinance s.46; VAT invoicing (Israel Invoices) | UNV | look up by name in Knesset open data |

## Foreign law and platform requirements

| ID | Instrument | Status | URL | Verified |
|---|---|---|---|---|
| S-GDPR | Regulation (EU) 2016/679 (GDPR), art. 3(2), 27, 44 onward | in force since 2018-05-25 | https://eur-lex.europa.eu/eli/reg/2016/679 | HTTP (202) only |
| S-APPLE | App Store Review Guidelines (incl. 5.1.1 data collection and account deletion) | platform policy | https://developer.apple.com/app-store/review/guidelines/ | HTTP only |
| S-GPLAY-DELETE | Google Play: account deletion requirements | platform policy | https://support.google.com/googleplay/android-developer/answer/13327111 | HTTP only |
| S-GPLAY-SAFETY | Google Play: Data safety section | platform policy | https://support.google.com/googleplay/android-developer/answer/10787469 | HTTP only |
| S-CWS | Chrome Web Store program policies (incl. Limited Use) | platform policy | https://developer.chrome.com/docs/webstore/program-policies/ | HTTP only |
| S-PCI | PCI DSS | contract or industry standard | https://www.pcisecuritystandards.org/ | HTTP only |

## Known changes after the skill's baseline research

Re-check these first in any `refresh`:

1. **CPL Amendment 74** comes into force 2027-03-22 (deferrable). After that
   date, re-label call-recording findings as `in force` and check the Ninth
   Schedule and any regulations extending the duty to chats.
2. **S-BROADCAST-2026**: confirm whether the Communications Law's name or s.30א
   moved.
3. **S-PPA-AI**: is the draft now final?
4. **S-PPA-AGE**: is the June 2026 draft now final?
5. **S-PPA-DPO** and **S-PPA-CONSENT**: read the official text and replace the
   SEC summaries in israel-baseline.md 1.2 and 1.9.
6. **S-CPL**: what changed on 2026-07-28 (latest publication)? A74 was 2026-07-22,
   so there is a later change.

## Refresh procedure (mode `refresh`, only when authorized)

1. **Status and dates (no credentials, public API):**
   - Law metadata:
     `https://knesset.gov.il/Odata/ParliamentInfo.svc/KNS_IsraelLaw(<ID>)?$format=json`.
     Compare `LatestPublicationDate` with the dates above.
   - Find a law by name:
     `KNS_IsraelLaw?$filter=substringof('<Hebrew name>',Name)&$format=json`.
   - Recent amendments with official summaries:
     `KNS_Bill?$filter=substringof('<law name> (תיקון',Name) and PublicationDate ge datetime'<YYYY-MM-DD>T00:00:00'&$orderby=PublicationDate desc&$format=json`.
     Read `SummaryLaw`. Omnibus laws with other names also amend laws, so list
     everything published around a changed date too
     (`PublicationDate ge ... and PublicationDate le ...`).
   - `KNS_IsraelLawBinding` was nearly empty for these laws in 2026-11. Don't
     rely on it.
2. **Wording:** read the official consolidated text where it is reachable. If
   only Wikisource is reachable, record `WS` and keep the claim flagged for
   official confirmation.
3. **Regulator pages:** gov.il `pages/` URLs block automated fetches (403). Try
   the `BlobFolder` PDF behind a page (those answered 200), or ask the user to
   open the page and paste the text. Record that as "verified by user in
   browser, <date>".
4. **Update in place:** change the status, effective date, verification code and
   date in this file, then the affected statements in israel-baseline.md and
   system-types.md. Add a line to "Known changes". Never delete history that
   explains an old finding. Mark it superseded instead.
5. **Report:** list each source checked, what changed, and what is still
   unverified.
