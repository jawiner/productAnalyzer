# Deliverable templates

Use these shapes for the output of each mode. Keep the section order; drop a section only when
it truly doesn't apply, and say why in a line.

Write real copy and real values. Where a value isn't known and can't be asked for (a price, a
limit, the name of one of the product's own lessons or exercises), write a marked gap such as
`[confirm: trial length]` in the copy and repeat it under open questions. That is different
from a placeholder standing in for copy you haven't written.

## Contents

1. Design deliverable (full form)
2. Design deliverable (short form, when the answer is "no quiz")
3. Audit deliverable
4. Implement report
5. Reusable tables

## 1. Design deliverable (full form)

For a questionnaire or a routing question.

```markdown
# Pre-signup onboarding design: <app>

## 1. Recommendation in brief
<Three or four sentences: the entry pattern, the result people get, what the account saves,
and the first test to run.>

### What changed from the request
<Only when the request named specific questions, screens or tactics. One row each.>
| Requested | Kept / changed / removed | Why |
| --- | --- | --- |

## 2. What we know about the app
- Why people arrive (by source): …
- What the business wants: …
- Activation event and window: …
- What the app can vary today (personalization inventory): …
- Current entry and auth: …
- Constraints: …

### Assumptions
| # | Assumption | Source | What changes if it is wrong |
| --- | --- | --- | --- |

## 3. Entry pattern decision
- Chosen: <short questionnaire | one routing question | immediate use | demo | identity first>
- Does an answer change anything? <the candidate questions and what survived>
- What did they come to do? …
- Is the result worth the effort? …
- What would change this decision: …

## 4. The flow, screen by screen
### Entry
<exact copy: headline, line, buttons, small print; and where it lives>
### Question 1 … n
<exact wording and options>
### Result
<exact copy for one worked answer set, with the "why it fits" lines>
### Account prompt
<exact copy, auth methods, price and terms if any>
### Between signup and the product
<email confirmation, paywall, permissions: exact copy for each that exists>
### First signed-in screen
<what opens, exact confirmation line>
### Behavior on every screen
<back, skip, progress, errors, keyboard and screen-reader behavior, small screens>

## 5. Question protocol
<one protocol table per question, or one combined table>

## 6. Answer-to-result mapping
<decision table, slots filled by a default, priority rule, fallbacks, invalidation>

### Two-answer-set check
<two people, side by side>

## 7. Signup handoff
- What the account saves or enables: …
- Draft: where it lives, expiry, attach-once rule: …
- Failure matrix: <the rows that apply>
- Data hygiene: …

## 8. Measurement plan
- Baseline: …
- Eligible entrant: …
- Primary outcome: …
- Diagnostics: …
- Guardrails: …
- Event map: …
- Test design and decision rule: …
- How to read signup up with activation down: …

## 9. What is evidence and what is a bet
| Recommendation | Label | Source or test |
| --- | --- | --- |

## 10. Open questions and review needed
<marked gaps; questions only the user can answer; anything needing legal, clinical,
financial or security review, with what the reviewer has to decide>
```

The five-lens pass from Step 4 is something you do to the draft. It shows up in the
deliverable as better copy and as the "Behavior on every screen" block, not as a section of
its own.

## 2. Design deliverable (short form)

When Step 2 lands on immediate use, a demo or identity first, there is little to specify and a
ten-section document buries the answer. Use this.

```markdown
# Pre-signup onboarding for <app>: recommendation

## 1. Recommendation
<The pattern, in two or three sentences, and the plain statement that a quiz is not
recommended here.>

### What changed from the request
| Requested | Kept / changed / removed | Why |
| --- | --- | --- |

## 2. Why
- Does an answer change anything? <each proposed question and what it would change: nothing,
  or what>
- What did they come to do? …
- Is a result worth the effort? …
- What would change this decision: …

### Assumptions
| # | Assumption | Source | What changes if it is wrong |
| --- | --- | --- | --- |

## 3. The flow
<One subsection per arrival type. For each: the screens that exist, with exact copy. Where
the account prompt appears, what triggers it, and its exact copy. What opens after signup.>

## 4. Handoff
<What must survive signup (the person's work, or the invited destination), where it waits,
and the failure rows that apply.>

## 5. If the team still wants questions
<Whether an honest version exists. If so, the smallest one and how to test it. If not, say
so, and give the proper home for what they want to learn.>

## 6. Measurement
<Baseline, eligible entrant, primary outcome, guardrails, events, the test.>

## 7. Evidence and bets, open questions, review needed
```

## 3. Audit deliverable

```markdown
# Pre-signup onboarding audit: <app>

## 1. Verdict
<Is the flow helping, on the evidence available? Two or three sentences, with the per-entrant
numbers if there are any, and how sure we can be.>

## 2. The numbers, recomputed
| | Before / control | After / variant |
| --- | --- | --- |
| Signup per entrant | | |
| Activation per signup | | |
| Activation per entrant | | |
<How the comparison was made, and what that does to confidence. What counts are missing.>

## 3. Does this app earn a quiz?
<Step 2's three tests on the existing questions: which answers change something the app
delivers, and the two-answer-set check on the current result.>

## 4. The flow as a new person meets it
| # | Screen | What it says and asks | Where the answer is used | Relevance | Trust | Momentum |
| --- | --- | --- | --- | --- | --- | --- |

## 5. Findings
### Broken or dishonest (fix now)
<each: what, evidence, fix, replacement wording where a screen's text changes>
### Likely costing activation (test)
<each: what, evidence, label, proposed change, how to tell it worked>
### Minor
…

## 6. Fixes in priority order
| # | Fix | Why this rank | Effort | Needs a test? |
| --- | --- | --- | --- | --- |

## 7. What to run in the meantime
<Split, revert or leave, with the trade-off, as the owner's decision.>

## 8. Measurement to put in place
<missing events, the primary outcome, the test to run next>

## 9. Assumptions and what couldn't be checked
```

Ratings in section 4: use "holds", "weak" or "breaks", with one phrase of evidence each.
Numbers out of ten suggest a precision the audit doesn't have.

## 4. Implement report

```markdown
# Pre-signup onboarding: what was built

## What changed
<files and routes, in plain terms>

## How it maps to the design
<any place the build differs from the design, and why>

## Verified
| Check | How | Result |
| --- | --- | --- |
<the verification list from signup-handoff.md, with what was actually run>

## Not verified
<what couldn't be checked here and how the user can check it>

## Still a hypothesis
<what the test has to settle; the test is not yet a result>

## To release
<the steps left, and anything waiting on the user>
```

## 5. Reusable tables

### Question protocol

| Field | Q1 | Q2 | Q3 |
| --- | --- | --- | --- |
| Wording | | | |
| Type | | | |
| Options | | | |
| Purpose (slot it fills) | | | |
| What each answer changes | | | |
| Who sees it | | | |
| Optional? | | | |
| Skip / not sure | | | |
| Data handling | | | |

### Answer-to-result

| Answer to Q1 | Answer to Q2 | Answer to Q3 | Result | First action |
| --- | --- | --- | --- | --- |

Not asked (filled by a default): … Priority rule: … Fallbacks: … Invalidation: …

### Two-answer-set check

| | Person A | Person B |
| --- | --- | --- |
| Why they came | | |
| Answers | | |
| Result headline | | |
| First action | | |
| "Why it fits" shown to them | | |
| What differs in substance | | |

### Event map

| Stage | Event | Properties (and who uses any answer data) | Fires when | Arm |
| --- | --- | --- | --- | --- |

### Evidence table

| Recommendation | Label | Source number or the test that settles it |
| --- | --- | --- |
