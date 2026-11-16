# Notice fragments (Hebrew first, then English)

Modular drafts for counsel to review. Use only the fragments the audit found to
apply, and fill them from facts, never from guesses.

## Rules for every fragment

- **Placeholders** look like `{{UPPER_SNAKE}}`, sometimes with a hint:
  `{{CHANNELS_HE: דוא"ל / SMS}}`. Before release, search the output for `{{`
  and `[[`. Every hit is unresolved. List them in the report's copy checklist.
  Nothing ships with one left in.
- **Optional parts** are in `[[double square brackets]]` with a condition.
  Delete the brackets, or the whole part, once you have decided.
- **Applicability:** each fragment says when to use it and its legal basis. Do
  not add a fragment "to be safe" if the facts don't trigger it (for example no
  tracking banner on a site with no optional tracking).
- **Language:** the Hebrew is RTL-ready, short, and avoids gendered verb forms
  where it can (infinitives, impersonal forms, plural address). Keep exact UI
  labels as written; tests look for them. Product names, URLs and emails inside
  Hebrew text need `<bdi>` or `dir="auto"` wrapping in HTML.
- **Accuracy:** list only vendors, purposes, retention periods and features that
  exist. Never write "among others" (בין היתר) for data types or purposes.
- **Not legal advice:** mark drafts "טיוטה לבדיקה משפטית" until counsel approves
  them.

---

## 1. Section 11 notice at a collection point

**Use when:** any form, sign-up, intake, chat or permission asks a person for
personal information. **Basis:** PPL s.11 (`statute`); PPA consent opinion
(`regulator interpretation`). **Placement:** directly under the fields or above
the submit button, visible before submitting, with a link to the full policy
section. Mark mandatory fields with `*` and say why they are needed.

### 1a. Contact or lead form (short)

```text
אנחנו ({{OPERATOR_LEGAL_NAME}}) נשתמש בפרטים שמסרת כדי {{PURPOSE_HE}}.
אין חובה חוקית למסור אותם, אבל בלי השדות המסומנים ב-* לא נוכל {{CONSEQUENCE_HE}}.
[[if shared]] נעביר אותם ל{{RECIPIENT_CATEGORIES_HE}} לצורך {{RECIPIENT_PURPOSES_HE}}.
אפשר לעיין במידע ולבקש לתקן אותו: {{PRIVACY_CONTACT}}. פרטים נוספים במדיניות הפרטיות.
```

```text
{{OPERATOR_LEGAL_NAME}} will use the details you give us to {{PURPOSE_EN}}.
You are not legally required to provide them, but without the fields marked * we cannot {{CONSEQUENCE_EN}}.
[[if shared]] We share them with {{RECIPIENT_CATEGORIES_EN}} for {{RECIPIENT_PURPOSES_EN}}.
You can inspect your information and ask us to correct it: {{PRIVACY_CONTACT}}. More in our Privacy Policy.
```

Link label: **"מדיניות הפרטיות"** / **"Privacy Policy"**, pointing to the
anchor of the matching section, not only to the top of the policy.

### 1b. Account sign-up

```text
כדי לפתוח חשבון נשתמש בשם, בכתובת הדוא"ל {{OTHER_FIELDS_HE}} לניהול החשבון, לאבטחתו ולמתן השירות.
מסירת הפרטים אינה חובה לפי חוק, אך בלעדיהם אי אפשר לפתוח חשבון.
בעל השליטה במאגר: {{OPERATOR_LEGAL_NAME}}, {{OPERATOR_CONTACT}}.
המידע נשמר אצל {{HOSTING_VENDOR_CATEGORY_HE}} ב{{STORAGE_COUNTRIES_HE}}. אפשר לעיין במידע ולבקש לתקן אותו בהגדרות החשבון או ב-{{PRIVACY_CONTACT}}.
```

```text
To open an account we use your name, email {{OTHER_FIELDS_EN}} to run and secure your account and provide the service.
You are not legally required to provide them, but we cannot open an account without them.
Database controller: {{OPERATOR_LEGAL_NAME}}, {{OPERATOR_CONTACT}}.
Data is stored with {{HOSTING_VENDOR_CATEGORY_EN}} in {{STORAGE_COUNTRIES_EN}}. You can inspect and correct it in account settings or at {{PRIVACY_CONTACT}}.
```

### 1c. Special-sensitivity intake (health, biometrics, finance, children)

**Extra rule:** the consent opinion asks for special prominence. Put this
notice in a highlighted box before the first sensitive question, not under the
submit button.

```text
בשאלון הזה נבקש מידע על {{SENSITIVE_CATEGORY_HE}}, שהוא מידע בעל רגישות מיוחדת.
נשתמש בו רק כדי {{PURPOSE_HE}}. [[if shared]] הוא יועבר רק ל{{RECIPIENTS_HE}} לצורך {{RECIPIENT_PURPOSES_HE}}.
הוא לא יועבר לגורמי פרסום או מדידה.
אין חובה חוקית למסור אותו; בלעדיו {{CONSEQUENCE_HE}}.
בעל השליטה במאגר: {{OPERATOR_LEGAL_NAME}}. עיון ותיקון: {{PRIVACY_CONTACT}}.
```

```text
This questionnaire asks about {{SENSITIVE_CATEGORY_EN}}, which is information of special sensitivity.
We use it only to {{PURPOSE_EN}}. [[if shared]] It goes only to {{RECIPIENTS_EN}} for {{RECIPIENT_PURPOSES_EN}}.
It is never sent to advertising or analytics providers.
You are not legally required to provide it; without it {{CONSEQUENCE_EN}}.
Database controller: {{OPERATOR_LEGAL_NAME}}. Inspection and correction: {{PRIVACY_CONTACT}}.
```

Release check: the sentence "לא יועבר לגורמי פרסום או מדידה" ships only after
a runtime network test proves it (see the Health row in system-types.md).

### 1d. Job application

```text
נשתמש בפרטים ובקורות החיים כדי לבחון את מועמדותך למשרה {{ROLE_HE}}[[ ולמשרות דומות, אם סימנת זאת]].
מסירתם אינה חובה לפי חוק, אך בלעדיהם לא נוכל לבחון את המועמדות.
יעיינו בהם {{REVIEWER_ROLES_HE}}[[ ו{{RECRUITMENT_VENDOR_HE}}]]. נשמור אותם {{RETENTION_HE}} ואז נמחק אותם.
בעל השליטה במאגר: {{OPERATOR_LEGAL_NAME}}. עיון ותיקון: {{PRIVACY_CONTACT}}.
```

```text
We use your details and CV to assess your application for {{ROLE_EN}}[[ and similar roles, if you ticked the box]].
You are not legally required to provide them, but we cannot assess your application without them.
They are seen by {{REVIEWER_ROLES_EN}}[[ and {{RECRUITMENT_VENDOR_EN}}]]. We keep them for {{RETENTION_EN}} and then delete them.
Database controller: {{OPERATOR_LEGAL_NAME}}. Inspection and correction: {{PRIVACY_CONTACT}}.
```

### 1e. App permission rationale (shown before the OS prompt)

```text
כותרת: גישה ל{{PERMISSION_HE}}
האפליקציה משתמשת ב{{PERMISSION_HE}} כדי {{PURPOSE_HE}}, {{WHEN_HE: רק כשהאפליקציה פתוחה / גם ברקע}}.
המידע {{SHARING_HE: לא יוצא מהמכשיר / נשלח ל{{RECIPIENT_HE}}}}. אפשר לסרב ולהמשיך להשתמש ב{{FEATURES_WITHOUT_HE}}.
כפתורים: "המשך" · "לא עכשיו"
```

```text
Title: Access to {{PERMISSION_EN}}
{{APP_NAME}} uses {{PERMISSION_EN}} to {{PURPOSE_EN}}, {{WHEN_EN}}.
The data {{SHARING_EN}}. You can decline and keep using {{FEATURES_WITHOUT_EN}}.
Buttons: "Continue" · "Not now"
```

---

## 2. Privacy policy modules

**Use when:** the product processes personal data. **Basis:** see
israel-baseline.md 1.5 for the basis of each section. Draft only the sections
whose facts exist. Title: **"מדיניות פרטיות"**. Show a "last updated" date at
the top.

| # | Hebrew heading | English heading | Content to fill |
|---|---|---|---|
| 2.1 | מי אנחנו ואיך פונים אלינו | Who we are and how to reach us | {{OPERATOR_LEGAL_NAME}}, company or ID number, address, privacy email, [[privacy officer {{DPO_NAME}} {{DPO_CONTACT}} if appointed]] |
| 2.2 | איזה מידע אנחנו אוספים | What we collect | One row per category from the data inventory: what, from where (you / your device / third parties), mandatory or optional |
| 2.3 | מידע שנאסף אוטומטית | Information collected automatically | Logs (IP, browser, time), cookies and SDKs by name and purpose, retention |
| 2.4 | למה אנחנו משתמשים במידע | Why we use it | One purpose per line, tied to the data in 2.2. No catch-all purposes. |
| 2.5 | למי אנחנו מעבירים מידע | Who we share it with | Recipient categories specific enough to be meaningful (for example "ספק שליחת דוא"ל (Resend)"), with each purpose |
| 2.6 | העברת מידע לחו"ל | Transfers abroad | Countries, vendors, and the basis (for example contractual undertakings under the Transfer Regulations) |
| 2.7 | כמה זמן אנחנו שומרים מידע | How long we keep it | Criteria or periods per category; backups and their expiry |
| 2.8 | אבטחת מידע | Security | Verified measures only, in plain terms. No "bank-grade" claims. |
| 2.9 | הזכויות שלך | Your rights | Inspection (s.13) and correction (s.14) and how to use them. [[Deletion only if offered or required, see baseline 1.4]] |
| 2.10 | פרסום ודיוור | Marketing | Channels, opt-in, how to opt out, direct-mailing statement if relevant |
| 2.11 | ילדים | Children | Only if relevant (system-types row 10) |
| 2.12 | שינויים במדיניות | Changes | How users are told about material changes |

Sample for 2.9:

```text
הזכויות שלך
• עיון: אפשר לבקש לעיין במידע שאנחנו מחזיקים עליך, ב-{{PRIVACY_CONTACT}}. נשיב תוך {{RESPONSE_DAYS}} ימים.
• תיקון: אם המידע אינו נכון, שלם, ברור או מעודכן, אפשר לבקש לתקן או למחוק אותו.
[[if offered]] • מחיקת חשבון: אפשר למחוק את החשבון ב{{DELETE_PATH_HE}}. נמחק את {{DELETED_DATA_HE}} תוך {{DELETE_DAYS}} ימים; {{RETAINED_DATA_HE}} יישמר {{RETAINED_PERIOD_HE}} כי {{RETENTION_REASON_HE}}.
כדי להגן עליך, נבקש לאמת את זהותך לפני שנמסור או נשנה מידע.
```

```text
Your rights
• Inspection: you can ask to see the information we hold about you at {{PRIVACY_CONTACT}}. We reply within {{RESPONSE_DAYS}} days.
• Correction: if information is incorrect, incomplete, unclear or out of date, you can ask us to correct or delete it.
[[if offered]] • Account deletion: delete your account in {{DELETE_PATH_EN}}. We delete {{DELETED_DATA_EN}} within {{DELETE_DAYS}} days; {{RETAINED_DATA_EN}} is kept for {{RETAINED_PERIOD_EN}} because {{RETENTION_REASON_EN}}.
To protect you, we verify your identity before we disclose or change information.
```

`{{RESPONSE_DAYS}}` must match the regulation in force (verify; see sources.md
S-PPL-INSPECT-REGS).

---

## 3. Optional tracking choice

**Use when:** optional trackers exist and the operator needs or relies on prior
opt-in (israel-baseline.md 2.2). **Do not use** on sites with only essential
storage. **Basis:** PPL consent analysis (`statute` plus `regulator
interpretation`); EU ePrivacy where the EU is targeted (`statute`, foreign).
**Placement:** a banner on first visit that does not block reading, plus a
persistent footer link. "Accept" and "Reject" have equal size and weight. Nothing
optional loads until a choice is made.

```text
כותרת: עוגיות וכלי מדידה
אנחנו משתמשים בכלים הכרחיים כדי שהאתר יעבוד. בהסכמתך נפעיל גם {{OPTIONAL_CATEGORIES_HE}} של {{VENDORS_SHORT_HE}}, שמקבלים מידע על השימוש שלך באתר לצורך {{PURPOSES_HE}}.
אפשר לשנות את הבחירה בכל עת ב"הגדרות פרטיות" בתחתית העמוד.
כפתורים: "אישור הכול" · "דחיית הכול" · "בחירה לפי סוג"
```

```text
Title: Cookies and measurement tools
We use essential tools to make the site work. With your consent we also turn on {{OPTIONAL_CATEGORIES_EN}} from {{VENDORS_SHORT_EN}}, which receive information about your use of the site for {{PURPOSES_EN}}.
You can change your choice at any time under "Privacy settings" at the bottom of the page.
Buttons: "Accept all" · "Reject all" · "Choose by type"
```

Preferences panel: one toggle per category (off by default), with the vendor
list, purpose and retention for each, and a save button **"שמירת הבחירה"** /
**"Save choices"**. Footer link label: **"הגדרות פרטיות"** / **"Privacy
settings"**.

---

## 4. Marketing messages (s.30A)

**Basis:** Communications Law s.30A (`statute`); direct mailing (PPL chapter B1).

### 4a. Opt-in checkbox (unchecked, separate from accepting terms)

```text
☐ אני רוצה לקבל מ{{BRAND_HE}} עדכונים ומבצעים ב{{CHANNELS_HE: דוא"ל / SMS / וואטסאפ}}. אפשר להסיר את עצמי בכל עת.
```

```text
☐ Send me news and offers from {{BRAND_EN}} by {{CHANNELS_EN}}. I can unsubscribe at any time.
```

Store the consent record: the text version, timestamp, channel, source form,
and IP or user ID.

### 4b. Existing-customer notice at checkout (only if relying on the exception)

```text
נשתמש בדוא"ל ובטלפון שמסרת כאן כדי לשלוח לך פרסומות על מוצרים ושירותים דומים לאלה שרכשת.
☐ לא לשלוח לי פרסומות
```

```text
We will use the email and phone you give here to send you ads about products and services similar to what you bought.
☐ Don't send me ads
```

Release check: this works only with all of the exception's conditions (baseline
2.4). If the products advertised later are not similar, use 4a instead.

### 4c. Email advertisement frame

```text
נושא: פרסומת: {{SUBJECT_HE}}
[גוף ההודעה]
—
{{ADVERTISER_LEGAL_NAME}} · {{ADVERTISER_ADDRESS}} · {{ADVERTISER_PHONE_OR_EMAIL}}
קיבלת הודעה זו כי {{REASON_HE}}. אפשר לבקש בכל עת להפסיק לקבל פרסומות: [להסרה מרשימת התפוצה] או בהשבה להודעה זו.
```

```text
Subject: Advertisement: {{SUBJECT_EN}}
[body]
—
{{ADVERTISER_LEGAL_NAME}} · {{ADVERTISER_ADDRESS}} · {{ADVERTISER_PHONE_OR_EMAIL}}
You received this because {{REASON_EN}}. You can stop receiving ads at any time: [Unsubscribe] or reply to this email.
```

For a Hebrew audience the subject line must start with the Hebrew word
**"פרסומת"** (or "בקשת תרומה" / "תעמולה"). Treat the English frame as
supplementary and confirm the language rule with counsel. The unsubscribe link
must work in one step, without a login.

### 4d. SMS / WhatsApp advertisement

```text
פרסומת {{BRAND_HE}}: {{TEXT_HE}} להסרה: {{OPTOUT_HE: השיבו "הסר" / קישור}}
```

### 4e. Unsubscribe confirmation page

```text
הוסרת מרשימת התפוצה של {{BRAND_HE}} ל{{CHANNEL_HE}}. לא נשלח לך פרסומות נוספות בערוץ זה.
[[if per-type]] אפשר לבחור כאן אילו סוגי עדכונים להמשיך לקבל.
```

---

## 5. Terms of service modules

**Use when:** there are accounts or paid services. **Basis:** contract law;
Standard Contracts Law (unfair-term screen); CPL rights cannot be waived.
Headings, with one-line drafting notes:

| Hebrew | English | Draft note |
|---|---|---|
| מי אנחנו | Who we are | Operator identity. If a marketplace, also say who the seller is. |
| השירות | The service | What it does and does not do; availability; changes with notice |
| חשבון | Your account | Eligibility (age), credentials, account security |
| מחירים, חיוב וחידוש | Prices, billing and renewal | VAT-inclusive prices; billing cycle; renewal per section 9 of this file |
| ביטול והחזרים | Cancellation and refunds | Point to section 7 of this file; never narrower than the law |
| תוכן שלך | Your content | A licence limited to running the service; moderation; takedown contact |
| שימוש אסור | Acceptable use | Specific, not open-ended |
| אחריות | Liability | No exclusion of liability for intent or gross negligence; check against the standard-contract presumptions |
| סיום | Termination | Notice periods both ways; data export window |
| דין וסמכות שיפוט | Law and venue | Israeli law; a consumer-fair venue |
| שינויים בתנאים | Changes | Advance notice; material changes need acceptance where required |

---

## 6. Accessibility statement

**Use when:** the accessibility module applies (or the operator chooses to
publish one). **Basis:** regulation 35ה (`regulation`); IS 5568.
**Placement:** a prominent link on every page (commonly the footer and the
accessibility menu) labeled **"הצהרת נגישות"**, and in the app.

```text
הצהרת נגישות
ב{{OPERATOR_NAME}} אנחנו פועלים כדי להנגיש את {{SITE_OR_APP_HE}} לאנשים עם מוגבלות, לפי תקנות שוויון זכויות לאנשים עם מוגבלות (התאמות נגישות לשירות), התשע"ג-2013, והתקן הישראלי 5568 ברמה AA.

מה עשינו
• {{VERIFIED_ACCOMMODATION_1_HE}}
• {{VERIFIED_ACCOMMODATION_2_HE}}
(רק התאמות שנבדקו בפועל. בדיקה אחרונה: {{AUDIT_DATE}}, {{AUDITOR}}.)

מה עדיין לא נגיש
{{KNOWN_GAPS_HE}}. עד לתיקון אפשר לקבל את השירות כך: {{ALTERNATIVE_HE}}.

[[if exempt]] פטור: {{EXEMPTION_TEXT_HE}} (לפי תקנה {{REG}}). במקום זאת אנחנו מציעים: {{ALTERNATIVE_ARRANGEMENTS_HE}}.

[[if physical service]] נגישות {{PHYSICAL_LOCATION_HE}}: {{PHYSICAL_ARRANGEMENTS_HE}}.

פנייה בנושא נגישות
נתקלת בבעיה או צריך התאמה? אפשר לפנות אל {{A11Y_CONTACT_NAME}}[[, רכז/ת הנגישות]]:
טלפון {{A11Y_PHONE}} · דוא"ל {{A11Y_EMAIL}} · {{OTHER_CHANNEL_HE}}
נשיב תוך {{A11Y_RESPONSE_DAYS}} ימים.

ההצהרה עודכנה ב-{{STATEMENT_DATE}}.
```

```text
Accessibility statement
{{OPERATOR_NAME}} works to make {{SITE_OR_APP_EN}} accessible to people with disabilities, under the Equal Rights for Persons with Disabilities (Service Accessibility Adjustments) Regulations 2013 and Israeli Standard 5568 at level AA.
What we did: {{VERIFIED_ACCOMMODATIONS_EN}} (last checked {{AUDIT_DATE}} by {{AUDITOR}}).
Known gaps: {{KNOWN_GAPS_EN}}. Until fixed, you can get the service this way: {{ALTERNATIVE_EN}}.
[[if exempt]] Exemption: {{EXEMPTION_TEXT_EN}}. Alternative arrangements: {{ALTERNATIVE_ARRANGEMENTS_EN}}.
Contact for accessibility: {{A11Y_CONTACT_NAME}}[[, accessibility coordinator]], {{A11Y_PHONE}}, {{A11Y_EMAIL}}. We reply within {{A11Y_RESPONSE_DAYS}} days.
Updated {{STATEMENT_DATE}}.
```

Never write "האתר נגיש באופן מלא" or "fully accessible". Do not credit an
overlay widget as compliance.

---

## 7. Sales and cancellation policy (distance sales)

**Use when:** B2C distance sales. **Basis:** CPL ss.14ג, 14ג1, 14ה, 14ט and the
Cancellation Regulations. Verify every number against the current text before
release. **Placement:** a policy page, summarized next to the buy button, and
repeated in the confirmation (section 10).

```text
ביטול עסקה והחזרות

מי מוכר: {{DEALER_LEGAL_NAME}}, {{DEALER_ID_TYPE}} {{DEALER_ID}}, {{DEALER_ADDRESS}}, טלפון {{DEALER_PHONE}}, דוא"ל {{DEALER_EMAIL}}.

עד מתי אפשר לבטל
• מוצר: מיום הרכישה ועד 14 ימים מיום קבלת המוצר או מיום קבלת מסמך פרטי העסקה, לפי המאוחר מביניהם.
• שירות: תוך 14 ימים מיום הרכישה או מיום קבלת מסמך פרטי העסקה, לפי המאוחר מביניהם[[, {{SERVICE_DATE_CONDITION_HE}}]].
• אדם עם מוגבלות, אזרח ותיק או עולה חדש, כהגדרתם בחוק: אם הרכישה כללה שיחה עם נציג שלנו, אפשר לבטל תוך 4 חודשים מיום הרכישה{{S14G1_CONDITIONS_HE}}.

דמי ביטול והחזר
• בביטול שלא בגלל פגם: דמי ביטול של 5% מהמחיר או 100 ₪, לפי הנמוך מביניהם.[[ אנחנו לא גובים דמי ביטול.]]
• בביטול בגלל פגם, אי-התאמה או איחור באספקה: אין דמי ביטול[[ ואנחנו נאסוף את המוצר על חשבוננו]].
• ההחזר יינתן תוך {{REFUND_DAYS}} ימים מקבלת הודעת הביטול, באותו אמצעי תשלום.
• החזרת המוצר: {{RETURN_METHOD_HE}}.

[[only categories you sell]] מה אי אפשר לבטל: {{EXCLUDED_CATEGORIES_HE}}.

איך מבטלים (כל דרך מספיקה)
• בקישור "ביטול עסקה" בעמוד הבית
• בטלפון {{DEALER_PHONE}} · בדוא"ל {{DEALER_EMAIL}} · בדואר רשום אל {{DEALER_ADDRESS}}[[ · {{OTHER_METHODS_HE}}]]
בהודעה יש לציין {{IDENTIFYING_DETAILS_HE}}.
```

`{{REFUND_DAYS}}`: 14 for distance-sale cancellations under s.14ה, unless a rule
that applies sets a shorter period (the regulations set 7 business days for
transactions under them; baseline 4.4). `{{IDENTIFYING_DETAILS_HE}}`: ask only
for what the law allows you to require (commonly name and order or ID number;
verify). `{{S14G1_CONDITIONS_HE}}`: fill from the official s.14ג1 text, or delete.

An English version follows the same structure. Translate only after the Hebrew is
approved.

---

## 8. Homepage cancellation link, form and confirmation

**Use when:** a dealer with a website has transactions consumers may cancel.
**Basis:** CPL s.14ט(ב) (`statute`). **Placement:** on the main page, prominent
and clear (not hidden in a collapsed footer menu on mobile), visible without
logging in.

- Link label: **"ביטול עסקה"** (exact text; confirm the wording required by the
  official s.14ט). English sites: **"Cancel a purchase"**, alongside the Hebrew
  label if the audience is Israeli.
- Form title: **"הודעת ביטול עסקה"**
- Fields:
  - "שם מלא" (required)
  - "מספר הזמנה, או הטלפון או הדוא"ל שאיתם הוזמן" (required, one of these)
  - {{ID_FIELD_IF_REQUIRED}}
  - "מה לבטל": the whole order or chosen items
  - "סיבת הביטול (לא חובה)"
  - "איך לחזור אליך": phone or email
- Submit button: **"שליחת הודעת ביטול"**
- Confirmation screen and message:

```text
הודעת הביטול התקבלה ב-{{SUBMITTED_AT}}. מספר פנייה: {{REFERENCE}}.
שלחנו אישור אל {{CONFIRMATION_DESTINATION}}. {{NEXT_STEPS_HE: ההחזר יינתן תוך ... / נתאם איסוף ...}}
```

```text
We received your cancellation notice at {{SUBMITTED_AT}}. Reference: {{REFERENCE}}.
A confirmation was sent to {{CONFIRMATION_DESTINATION}}. {{NEXT_STEPS_EN}}
```

Acceptance: the record is stored with a timestamp; the business is notified; the
consumer gets a confirmation; there is no login wall; no reason is required; it
works on mobile and with the keyboard and a screen reader.

---

## 9. Subscriptions and ongoing transactions

**Basis:** CPL ss.13א–13ד, 14ט (`statute`). Pick the variant that matches the
billing model. **Fixed-term plans must not renew without the consumer's
agreement** (s.13א(ג)).

### 9a. Before purchase (next to the pay button)

Open-ended (monthly until cancelled):

```text
{{PLAN_HE}}: {{PRICE}} ₪ ל{{PERIOD_HE}}, כולל מע"מ. החיוב ממשיך כל {{PERIOD_HE}} עד שמבטלים.
[[if trial]] {{TRIAL_DAYS}} ימי ניסיון בחינם; החיוב הראשון ב-{{FIRST_CHARGE_DATE}} אם לא מבטלים קודם.
אפשר לבטל בכל עת ב{{CANCEL_PATH_HE}} או ב"ביטול עסקה" בעמוד הבית. המנוי יסתיים תוך 3 ימי עסקים מהודעת הביטול[[ ו{{PRORATION_RULE_HE}}]].
```

Fixed term (for example annual):

```text
{{PLAN_HE}}: {{PRICE}} ₪ ל{{TERM_HE}}, כולל מע"מ, מ-{{START_DATE}} עד {{END_DATE}}.
לפני סוף התקופה נשלח לך הודעה. המנוי יתחדש רק אם תאשרו את החידוש.
אפשר לבטל בכל עת ב{{CANCEL_PATH_HE}} או ב"ביטול עסקה" בעמוד הבית.
```

### 9b. End-of-term notice (fixed term; send within the s.13א(א) notice period)

```text
נושא: המנוי שלך ל{{PRODUCT_HE}} מסתיים ב-{{END_DATE}}
המנוי {{PLAN_HE}} מסתיים ב-{{END_DATE}}.
כדי להמשיך, אפשר לאשר חידוש ל{{NEW_TERM_HE}} במחיר {{NEW_PRICE}} ₪ כולל מע"מ: [אישור החידוש]
בלי אישור, המנוי יסתיים ב-{{END_DATE}} ולא נחייב אותך שוב.
```

This is a service notice, not an ad. Keep promotions out of it, or it becomes
subject to s.30A.

### 9c. In-account cancellation

- Settings entry: **"ביטול המנוי"**
- Confirmation dialog: "לבטל את {{PLAN_HE}}? הגישה תימשך עד {{ACCESS_END}}[[, ויינתן החזר של {{REFUND_AMOUNT}} ₪]]." Buttons: **"ביטול המנוי"** · **"חזרה"**
- One retention offer is acceptable. Do not add extra steps, calls or a chat
  requirement.
- After confirming: "המנוי בוטל. נשלח אליך אישור בדוא"ל. לא יהיו חיובים נוספים
  אחרי {{LAST_CHARGE_DATE_OR_NONE}}."

---

## 10. Order confirmation (written disclosure document)

**Basis:** CPL s.14ג(ב) (`statute`; verify the timing and full list). **Placement:**
an email or PDF sent on every order path, in Hebrew or the marketing language.
Fields:

- Dealer name, ID or company number, address, phone, email
- Order number and date
- Each item or service: description, main characteristics, quantity
- Total price, with VAT and every mandatory charge itemized (delivery,
  installation)
- Payment method, installments, and credit terms if any
- Delivery or performance date and method
- Warranty: who gives it, its length, how to claim
- Manufacturer or importer and country of origin, where applicable
- How to cancel: the methods in section 7, the period, fees, and excluded
  categories that apply to this order
- For subscriptions: the renewal rule (section 9a) and the cancellation path

Hebrew heading: **"פרטי העסקה"**. Footer line: "שמרו הודעה זו. היא כוללת את
פרטי העסקה ואת זכות הביטול."

---

## 11. Call recording announcement

**Use when:** calls are recorded. From **2027-03-22** (deferrable) this is
mandatory for transactions covered by CPL Amendment 74 (`statute`, enacted, not
yet in force). Before then, or for other calls, use it as a privacy notice (PPL).

```text
השיחה מוקלטת{{PURPOSE_CLAUSE_HE: לצורך תיעוד העסקה ושיפור השירות}}. אפשר לבקש מאיתנו את ההקלטה.
```

```text
This call is recorded{{PURPOSE_CLAUSE_EN}}. You can ask us for the recording.
```

Operational pair: recordings are kept for 2 years if a deal was concluded, or 6
months if not (A74 minimums; check other laws requiring longer). A request route
for recordings must exist, free the first time.

---

## 12. Account deletion

**Basis:** platform requirement (Apple 5.1.1(v); Google Play account deletion)
where apps let users create accounts. PPL s.14 or EEA rules where relevant;
otherwise the operator's choice. **Placement:** in the app's account settings,
and a web page reachable without the app (Google Play).

- Entry: **"מחיקת החשבון"** / **"Delete account"**
- Confirmation:

```text
מחיקת החשבון תמחק את {{DELETED_DATA_HE}} תוך {{DELETE_DAYS}} ימים. אי אפשר לבטל את הפעולה.
{{RETAINED_DATA_HE}} יישמר {{RETAINED_PERIOD_HE}} כי {{RETENTION_REASON_HE}}.
[[if active subscription]] מנוי פעיל דרך {{STORE_HE}} צריך לבטל בנפרד ב{{STORE_PATH_HE}}.
כפתורים: "מחיקת החשבון לצמיתות" · "חזרה"
```

```text
Deleting your account removes {{DELETED_DATA_EN}} within {{DELETE_DAYS}} days. This cannot be undone.
{{RETAINED_DATA_EN}} is kept for {{RETAINED_PERIOD_EN}} because {{RETENTION_REASON_EN}}.
[[if active subscription]] A subscription bought through {{STORE_EN}} must be cancelled separately in {{STORE_PATH_EN}}.
Buttons: "Delete account permanently" · "Go back"
```

`{{RETENTION_REASON_HE}}`: name the actual legal duty (for example tax records,
with the period verified), never "for legal reasons" alone.
