# Audit report template

Fill every section in this order. Write "None" rather than dropping a section.
Keep it in the reply unless the user asked for a file (SKILL.md, mode table).

---

```markdown
# Israeli digital compliance audit: {{PRODUCT_NAME}}

| | |
|---|---|
| Mode | audit / plan |
| Scope | {{SCOPE as requested}}, and what was excluded |
| Date | {{YYYY-MM-DD}} |
| Evidence used | static review of {{paths}}; runtime checks: {{what ran, with synthetic data}} / none |
| Repository state | {{branch, commit}} |
| Sources verified live this run | {{n}} of {{m}} cited (see section 8) |

This report supports review by qualified Israeli counsel. It is not legal advice
and does not certify compliance.

## 1. Executive summary

- Overall position in 3 to 5 bullets: the biggest exposures first, and what is
  already in place.
- Counts: findings by status (missing / partial / applicability unknown /
  verified implemented / inapplicable) and by priority (P0 to P3). Fill these
  in last, by counting section 4, so they match.
- The facts that, once answered, would change the most conclusions.

## 2. Facts and assumptions

| # | Fact | Value | Basis | Evidence or source | If wrong |
|---|---|---|---|---|---|
| F1 | Operator and dealer | {{legal name / unknown}} | observed / provided / inferred / unknown | {{file:line or "user, msg"}} | {{which findings change}} |
| F2 | Audience and ages | | | | |
| F3 | Data categories (special sensitivity?) | | | | |
| F4 | Scale (people, authorized users) | | | | |
| F5 | Storage and vendor countries | | | | |
| F6 | Sales model (B2C/B2B, distance sale, subscription) | | | | |
| F7 | Public service? Turnover band for accessibility exemptions | | | | |
| ... | | | | | |

Open questions for the user (only ones that change a conclusion):
1. {{question}}. Affects {{finding IDs}}.

## 3. Applicability matrix

| Module or row | Result | Why | Facts pending |
|---|---|---|---|
| B1 Privacy and data governance | applies / inapplicable / unknown | | |
| B2 Tracking and marketing | | | |
| B3 Accessibility | | | |
| B4 Consumer, contracts, content | | | |
| Row {{n}}: {{name}} (from system-types.md) | | | |
| Foreign law: {{EU/other}} | analyzed separately / not triggered | | |

## 4. Findings

Order by priority, then by module.

### {{ID: e.g. PRIV-03}}: {{one-line title}}

| Field | Value |
|---|---|
| Status | missing / partial / applicability unknown / verified implemented / inapplicable: {{reason}} |
| Priority | P0 / P1 / P2 / P3 |
| Trigger | {{the fact or feature that triggers the duty}} |
| Who owes it | {{controller / dealer / platform / seller / employer}} |
| Legal classification | statute / regulation / binding sector rule / regulator interpretation / platform requirement / contract requirement / best practice |
| Source and section | {{source ID, section}}, {{status: in force / enacted not in force / draft}}, verified {{date}} by {{KO/WS/official/NF}} |
| Duty | {{what must be published or implemented, where, and when}} |
| Observed evidence | `{{path:line}}` ({{static/runtime}}): {{what it shows}} |
| Missing facts | {{or "None"}} |
| Remediation | {{concrete change: component, copy (link to drafts), config, process}} |
| Owner | {{role}} |
| Acceptance test | {{measurable behavior: given, when, then; static or runtime}} |
| Review needed | counsel / accessibility specialist / business / regulator / none |

Finding ID prefixes: `PRIV` (privacy), `SEC` (security), `XFER` (transfers),
`TRK` (tracking), `MKT` (marketing messages), `A11Y`, `CONS` (consumer), `TERMS`,
`CONT` (content and IP), `SECT` plus the row number for sector findings (for
example `SECT8-02`).

## 5. Copy and placement checklist

| Surface (route or screen) | Required copy | Exact placement | Draft (notices.md section) | Status | Unresolved placeholders |
|---|---|---|---|---|---|
| {{/contact form}} | s.11 short notice | Under the submit button, before submit | §1 | missing | {{OPERATOR_LEGAL_NAME}} |

## 6. Prioritized remediation

| Order | Action | Findings closed | Owner | Depends on | Size |
|---|---|---|---|---|---|
| 1 | | | | | S / M / L |

Owner roles: Product owner, Engineering lead, Frontend, Backend or data,
Marketing or CRM owner, Customer support lead, Finance or billing, Privacy
officer or data protection lead, Information security officer, Accessibility
coordinator, Israeli counsel, Business owner (for decisions such as retention
periods or whether to offer deletion).

## 7. Evidence to verify after changes

| Finding | Test | Method | Pass criterion |
|---|---|---|---|
| | {{e.g. fresh profile, reject optional tracking, browse 3 pages}} | runtime: network capture plus server log | zero requests to {{domains}}; no {{event}} rows in server log |

A screenshot alone does not verify backend behavior. Each runtime test names the
log, network capture or database query that proves the outcome.

## 8. Sources

| Source ID | Section | Status | Effective | URL | Verified (date, method) |
|---|---|---|---|---|---|

List every claim that is `unverified` or `provisionally sourced`, and the
check a person must make for each.

## 9. Reviews needed

- Israeli counsel: {{finding IDs and the question}}
- Accessibility specialist: {{...}}
- Business owner decisions: {{...}}
- Regulator contact (if any): {{...}}

## 10. Limitations

What was not inspected (production, third-party dashboards, contracts not in the
repo), what was static only, and what could not be verified live.
```

---

## Plan mode additions

Add to section 6 for each item: the sprint or phase, the acceptance test ID, and
whether it blocks release. Group items so that one change closes related
findings (for example one consent component for all forms).

## Status rules (quick reference)

- `verified implemented`: every element of the duty has evidence. Runtime duties
  need runtime evidence.
- `partial`: some elements are present (for example a footer privacy link, but
  no notice at the form).
- `missing`: the duty applies and nothing implements it.
- `applicability unknown`: it depends on a pending fact. Name the fact.
- `inapplicable`: state the reason and the fact it rests on (for example "no
  sales: no checkout routes found in `app/`, user confirmed no payments").
