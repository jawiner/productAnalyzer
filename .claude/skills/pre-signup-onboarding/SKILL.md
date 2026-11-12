---
name: pre-signup-onboarding
description: Design, audit, or implement the first-run experience where a new user answers questions before creating an account - a pre-signup quiz, onboarding questionnaire, personalization flow, quiz funnel, quiz-to-plan, or the decision of where the signup wall goes. Decides whether a quiz earns its place versus one routing question, immediate product use, a demo, or signup-first; works backward from the result to write screen copy, questions, answer-to-result mapping, the signup handoff, and a measurement plan. Use whenever the user wants to ask new users questions before signup, personalize the first run, show value before the account wall, fix a quiz where signups rose but activation fell, or mentions an onboarding quiz, welcome survey, "tell us about yourself" step or get-started flow - for any app, audience, business model or stack, even if they never say "quiz". Not for product tours inside the app after signup, marketing landing pages, or research surveys with no signup.
argument-hint: "[design | audit | implement] [app, path or brief]"
---

# Pre-signup onboarding

Design, audit, or build what a new person meets before they have an account: the opening
promise, any questions, the result those questions produce, the account prompt, and the first
signed-in screen.

The questions are an exchange. The person tells the app about their situation. The app shows it
understood by giving back something they can see or use. That gives them a concrete reason to
create an account. A quiz that only collects is a longer signup form. The working chain is:

**promise → relevant questions → visible value → account creation → immediate continuation**

Treat that chain as a starting hypothesis to compare against the app's current entry, never as a
known winner. Whether it helps depends on what the app can deliver, why people arrived, and how
much effort the questions add.

## How this job usually fails

| Failure | Prevented by |
| --- | --- |
| A quiz bolted onto an app where every answer leads to the same first screen | Step 2: decide whether a quiz earns its place |
| "Personalized for you" on a result that is the same for everyone | Step 3: answer-to-result mapping and the two-answer-set check |
| Questions that fill a marketing spreadsheet and change nothing for the person | Step 3: every question traces to a decision |
| Answers lost at signup, so the new user lands on an empty generic screen | Step 5: the handoff |
| Signup rate rises, fewer people get value, and nobody notices | Step 6: measure per eligible entrant |
| Invented scores, fake "analyzing…" delays, unsupported promises, surprise pricing | Honesty rules |

## Evidence labels

Every recommendation you make carries one of three labels, so the reader can tell what is known
from what is a bet:

- **[R] Research or standards guidance.** Peer-reviewed research, meta-analyses, independent
  usability research, and guidance from public services, standards bodies and regulators.
  Strong on question quality, usability, accessibility and honest design.
- **[V] Vendor material.** Product documentation, company case studies and industry benchmarks.
  It shows that a pattern exists. It cannot isolate what a quiz contributed.
- **[H] Hypothesis.** A design choice this particular app has to test. Craft and engineering
  practice with no source behind it is [H] too; don't stretch a source to cover it.

None of the sources behind this skill measures a causal signup lift from a pre-signup quiz, an
ideal number of questions, or the best place for the account prompt. So wherever a flow has
them, **quiz length, progress indicators and account timing are always [H]**: present them as
choices to test, and never quote an expected lift.

Some matters sit outside the source list altogether: the law in a given country, app-store and
platform rules, clinical or financial practice. Don't label those [R]. Write "outside the
source list: to verify with" and name the owner (lawyer, clinician, security lead). The
sources, links and their limits are in [references/research.md](references/research.md).

The reader of your deliverable has not seen that file, so a bare "[R: 9]" tells them nothing.
Name the source where you cite it, and end the deliverable with a short list of the sources
you used, with their links.

## Pick the mode

| Mode | Use when | Produces |
| --- | --- | --- |
| **Design** | There is no flow yet, or the user wants a new one | Recommended entry pattern, screen copy, question protocol, answer-to-result mapping, handoff spec, measurement plan |
| **Audit** | A flow exists and the question is whether it works or why it doesn't | Where the flow loses relevance, trust or momentum, with fixes in priority order |
| **Implement** | A design is approved, or the user hands you one and says build it | The working flow in the target app, verified |

Take the mode from the request or the invocation argument. When someone asks to "add" or "build"
a quiz and no design exists, run Design first and get a yes before writing code, because the
expensive mistake is building a flow the app never needed. Steps 1 and 2 run in every mode.

## Reference map

| When | Read |
| --- | --- |
| Step 2, or the user pushes for a quiz the app may not need | [references/entry-patterns.md](references/entry-patterns.md) |
| Step 3: writing questions, options, fallbacks, the mapping table | [references/question-design.md](references/question-design.md) |
| Steps 3–4: writing each screen, promise, proof, account prompt, accessibility | [references/screens-and-copy.md](references/screens-and-copy.md) |
| Step 5, and all of Implement mode. Also covers flows with no quiz: saved work, invite links | [references/signup-handoff.md](references/signup-handoff.md) |
| Step 6, and any audit that involves numbers | [references/measurement.md](references/measurement.md) |
| Audit mode: what to cut, and what a result or account prompt may claim | "Questions to cut" in [question-design.md](references/question-design.md); sections 5 and 6 of [screens-and-copy.md](references/screens-and-copy.md) |
| Writing the deliverable | [references/templates.md](references/templates.md) |
| You want to see a finished design, or a non-quiz recommendation | [references/worked-examples.md](references/worked-examples.md) |
| A claim needs a source, or someone asks "does this actually work?" | [references/research.md](references/research.md) |
| The flow has to sell, the owner says it's weak or asks what the best apps do | [references/top-app-patterns.md](references/top-app-patterns.md) |

---

## Step 1: Understand the app

The design has to come from what this app really does, so look before proposing anything.

With a repo, inspect:

- **Entry points.** Where the landing page's buttons go; routes like sign-up, login, welcome,
  onboarding, get-started; links from ads, invites and emails.
- **Auth.** Provider and methods (password, magic link, OAuth, SSO), whether email confirmation
  is on, how the callback is handled, and what the app does right after a first sign-in.
- **The first signed-in screen.** What a brand-new account sees, including empty states.
- **Personalization inventory.** What the app can already vary per person: templates, starter
  content, plan types, modules, defaults, roles, categories. Take it from code and data, not
  from the roadmap. This list is the ceiling on what a quiz may promise.
- **Any existing onboarding.** Quiz, wizard, profile setup, tour.
- **Evidence about people.** Analytics events, funnel numbers, acquisition sources and what the
  ads or search results promise, reviews, support messages, interviews.
- **Constraints.** Is identity needed before anything real can be shown? Sensitive data?
  Payment right after signup? Which countries? Minors?
- **Design system and languages.** Tokens, components, right-to-left support.

With only a brief, pull the same facts from the text.

Pin down five things: **why people arrive** (by traffic source), **what the business wants them
to do**, **the activation event** (the first action that shows the person received value),
**what an answer could change** about that first action, and **the constraints**.

Ask the user only for a gap that would change the design: usually the activation event, the
traffic source and its promise, sensitive data, or whether a paywall follows. Everything else
goes into an assumption ledger (fact, where it came from, what changes if it is wrong). When you
cannot ask, proceed on labelled assumptions.

An assumption stays visible wherever the design leans on it, not only in the ledger. If the
verdict or a recommendation depends on something you inferred (what the old flow looked like,
that the app already knows a person's role, that answers are discarded at signup), say
"assuming…" at that point. A reader who skims the conclusion should not mistake your inference
for something they told you.

## Step 2: Decide whether a quiz earns its place

A questionnaire is one of five entry patterns. Choose by what the app can do with an answer:

| Pattern | Fits when | What earns the account |
| --- | --- | --- |
| **Short questionnaire** | Different goals or constraints lead to materially different first experiences the app can deliver today | Save, edit and continue the result |
| **One routing question** | One answer changes the starting path and the rest is the same | Resume work, keep the preference |
| **Immediate use** | The product shows its value faster than questions could, and the first action is the same for everyone | Keep a real artifact, history, collaboration |
| **Demo or sample** | Value needs data or setup the visitor doesn't have yet | Do it with their own data |
| **Identity first** | Private or shared data, invites, permissions: nothing real can be shown without knowing who they are | Access to the real workspace, with the reason explained |

Run three tests and show your working:

1. **Does an answer change anything?** List the candidate questions. For each, name two answers
   and the two different first experiences they lead to, using only what the app does today. A
   question that fails is cut. None survive: no quiz. One survives: a routing question.
2. **What did they come to do?** Someone who arrived to finish a task now is slowed by
   questions. Someone who arrived for a plan expects to be asked.
3. **Is the result worth the effort?** Compare the effort of answering with the value of the
   result. If an editable default would serve as well, use the default.

Different arrivals can get different entries: an invite link should not pass through the quiz
built for ad traffic. A quiz can also be optional, with a working "skip, show me a general
start" path.

State the recommendation, the reasoning, and what evidence would change it. When someone asked
for a quiz and the app does not earn one, say so plainly and recommend the better pattern. If
they still want a quiz, the fallback is the smallest honest version, set up as a test against
the alternative. If no question passes test 1, no honest version exists for that arrival, and
saying so is a complete answer: offer what does the job instead (an optional research question
after the person has had value, or the product change that would give an answer something to
do). Where a flow touches health, money, safety or private records, flag it for review by a
qualified owner and define a safe fallback. Detail:
[references/entry-patterns.md](references/entry-patterns.md).

## Step 3: Work backward from the result

Write in this order, because each item limits the one after it:

1. **The result.** The useful thing the app can show or do before signup: a starter plan, a
   first action, a filled-in example, a preview. It has to be real output of the product.
2. **What the account enables.** What creating an account saves or unlocks, stated so that it
   is literally true the moment signup completes.
3. **The promise.** The opening line, matched to why people arrived and no bigger than the
   result.
4. **The questions.** The minimum inputs the result needs.

Then write the actual copy for every screen: entry, each question with its options, the result,
the account prompt, anything that stands between signup and the product (email confirmation, a
paywall), and the first signed-in screen. Descriptions of copy ("a friendly headline about
goals") are not a design. When the copy depends on a fact you don't have and can't ask for (a
price, a limit, the names of the product's own content), write around a marked gap such as
`[confirm: trial length]` and list it under open questions. A visible gap is better than an
invented fact.

For every question record: wording, answer options, the decision or experience **each answer**
changes, who sees it, whether it is optional, what happens on skip or "not sure", and how the
answer is stored and handled. A question with nothing in the "changes" column is removed.
Removing it is a correctness and data-minimisation fix [R: 1, 15], done without a test; what
stays [H] is how many of the questions that do change something to keep. A slot can also be
filled by an editable default instead of a question; record those too.

Answers the business wants for its own purposes (research, attribution, sales qualification)
don't belong between the person and the product. If they are needed, collect them where the
person chooses to give them: an optional question after they have had value, or a form they
opened to talk to sales, labelled for what it is.

Add an answer-to-result table wherever answers combine, with a priority rule for conflicting
answers, the fallback for skipped ones, and what changing an earlier answer invalidates.

**Two-answer-set check.** Write two realistic people with different answers, walk each through,
and put their results side by side. They must differ in substance (a different action, content,
size or order), not just echo the answer back in a headline. If they don't, the quiz is not
personalizing and Step 2 needs revisiting. With no quiz there is nothing to check; where the
design has several arrivals or a routing question, set two arrivals side by side instead.

Detail and templates: [references/question-design.md](references/question-design.md),
[references/screens-and-copy.md](references/screens-and-copy.md).

## Step 4: Check the draft through each discipline

Read the draft once per lens and fix what each one finds:

- **Marketing.** Does the first screen use the language of the ad, search or referral that
  brought the person? Is the promise proportional to what the product delivers? Is any time or
  step estimate one you can support?
- **Sales discovery.** Do the questions surface the goal, the obstacle and the constraints that
  change the recommendation? Does the result show fit through its reasoning ("5 minutes after
  breakfast, because you said evenings are unpredictable") instead of asserting it
  ("personalized for you")?
- **Selling it.** A timid flow is a failure too. Check every screen against the honest selling
  levers: the outcome in the headline, a labelled example as proof, the obstacle question when
  an answer can change the setup, "because you said…" on the result, what builds up with use,
  and a close that names the gain, the cost and what is lost without an account. Checklist, and
  the tricks it rules out: section 12 of
  [references/screens-and-copy.md](references/screens-and-copy.md). For a consumer app, also
  hold it against what the best apps do: one question per screen, "worth knowing" screens with
  a cited study, the person's name, a plan reveal with honest numbers, a signed commitment, and
  the first real action before the account. A flow with good copy but none of these was judged
  "30% there" on its first real use. Patterns, honest versions and a checklist:
  [references/top-app-patterns.md](references/top-app-patterns.md).
- **Behavioral psychology.** Autonomy: real choices, an honest skip, a way to correct answers.
  Confidence: an easy first question, an early sign the answer did something. Momentum: a first
  action small enough to do, with an if-then cue where the product supports it. [R] for the
  theory, [H] for its effect in this flow.
- **UX and accessibility.** One concept per question, distinct options that cover real answers,
  a truthful step count (or stages when branches vary), back navigation that keeps answers,
  editing from the result, clear errors, keyboard and screen-reader paths, small screens, long
  translated labels. [R]
- **Privacy and honesty.** Every sensitive question is explained where it is asked, has an
  alternative, and comes late. Collect the minimum. Every claim, score, price and testimonial
  can be backed up. [R]

## Step 5: Design the signup handoff

The account prompt is a handoff, and it fails in specific ways. Specify:

- **What the account saves or enables**, in the button and the line above it ("Save my
  routine" only if signup saves the routine). Label the account requirement plainly. If payment
  follows, show the price and terms before the person commits.
- **What they see immediately after signup:** the result they were promised, or the first
  action of it. Never a blank dashboard. If a step stands in between (confirming an email, a
  paywall), the person is told before they commit, and the account line stays true about what
  is usable without paying.
- **How the anonymous answers survive:** back navigation, refresh, leaving for an OAuth screen
  and returning, auth cancelled, auth failed and retried, email confirmation opened in another
  browser or on another device, and sign-in with an account that already exists.
- **When there are no answers to carry:** with immediate use, the thing that must survive is
  the person's work; with an invite, it is the destination they were invited to. The same
  rules apply to those.
- **Draft rules:** where the draft lives, when it expires, what the person gets after expiry (a
  usable general start, never an error), and how it attaches to the account exactly once.
- **What never happens:** sensitive answers in URLs, analytics events, ad pixels or logs.

For Implement requests, use the app's existing design system and authentication. Do not add a
second auth path or a new visual language for the quiz. Patterns, a failure matrix and the
verification list: [references/signup-handoff.md](references/signup-handoff.md).

## Step 6: Measure whether the flow helped

- **Baseline:** the current entry flow, defined precisely, running alongside the new one. If
  nothing is tracked yet, instrumenting the baseline comes before any test. If the app has no
  entry yet, the baseline is the simplest honest one.
- **Primary outcome:** people who complete the app's first core action within a window that
  fits normal usage, divided by **all eligible entrants assigned to the flow**, including those
  who skip or leave. Dividing by signups hides the people the quiz lost. When the core action
  needs no account, see measurement.md for which outcome leads.
- **Diagnostics:** account creation per entrant, quiz completion, drop-off per step, draft
  restored after signup, time to first core action.
- **Guardrails:** whatever a "win" could quietly damage: retention, refunds or cancellations,
  support contacts, complaint or unsubscribe rates, page performance.
- **Event map and test:** assignment before the first screen, stable assignment, all assigned
  users compared, sample ratio checked before reading results, the metric and decision rule
  written down first.
- **Reading a mixed result:** if signup rises and activation per entrant falls, the flow lost
  under an activation objective. Say so, then diagnose why (lower-intent signups, a result that
  over-promised, a handoff that dropped the answers).

With low traffic, use moderated walkthroughs and an event audit to find confusion, and call any
conversion difference directional. Detail: [references/measurement.md](references/measurement.md).

---

## Mode specifics

### Design

Deliver, using the Design template in [references/templates.md](references/templates.md): the
app understanding and assumption ledger, the entry-pattern decision with reasoning, the
screen-by-screen copy, the question protocol, the answer-to-result table with the two-answer-set
check, the handoff spec, the measurement plan, and the open questions. When Step 2 lands on
immediate use, a demo or identity first, use the template's short form: the answer is mostly
"don't build a quiz, and here is where the account prompt goes", and a long document buries
it. When the request named specific questions or tactics, include the table of what was kept,
changed or removed and why. In a repo, save the design where the project keeps specs so a
later Implement session can pick it up; otherwise reply in the conversation.

### Audit

1. Experience the flow as a new person: run it if you can, otherwise read every screen in the
   code. Record each screen's copy, inputs and what happens next.
2. For each question, find where its answer is used. Unused answers are the commonest finding.
3. Rate each screen on three things: **relevance** (does it relate to why I came and what I
   said?), **trust** (is every claim, score, delay and price honest and explained?), and
   **momentum** (is the next step obvious, small and kept after a mistake?).
4. Follow the handoff: do the answers survive signup, and does the first signed-in screen
   deliver the promise?
5. Recompute any numbers per eligible entrant, and check how the comparison was made (random
   assignment or before/after).
6. Order the fixes. First what is broken or dishonest (fix now, no test needed). Then what
   likely moves the primary outcome most for the least effort (test). Each fix names the
   evidence, the label and how to tell it worked. Where a fix changes what a screen says, give
   the replacement wording.
7. Say what to do with live traffic while the fixes are built (measurement.md covers the
   options), and whether the app earns a quiz at all (Step 2).

Use the Audit template in [references/templates.md](references/templates.md).

### Implement

1. Confirm there is an approved or supplied design. If the design has a gap that blocks the
   build (no fallback for a skipped question, no rule for existing accounts), settle it first.
2. Read [references/signup-handoff.md](references/signup-handoff.md). Follow the host project's
   own instructions, design system and auth; they win over this skill's defaults.
3. Build the mapping as explicit rules or a decision table that someone can review, before any
   screens. Then the screens, the draft storage, the handoff, and the events.
4. Verify by running the flow, not by reading the code: the acceptance checks below, on a small
   screen and by keyboard, with each auth method the app offers.
5. Report what you verified, what you could not, and what is still [H] and needs the test.
   Do not release a test variant to real traffic without the user's say-so.

## Honesty rules

These hold in every mode, including when the user asks for the opposite. The reason is
practical as much as ethical: the whole flow works by earning trust before asking for an
account, and regulators treat several of these as deceptive design. [R]

- No fabricated scores, diagnoses or "match percentages". A number shown to the person must
  come from a real calculation that can be explained.
- No fake processing. A delay or "building your plan" animation is allowed only for as long as
  real work takes.
- No claim, outcome promise, statistic or testimonial that can't be substantiated.
- No undisclosed price, trial terms or data use. The person learns them before committing.
- No question that exists only to make the person feel invested.
- No blocking of the skip path with guilt or tricks.

When a user asks for one of these, explain the problem, and offer the honest version that does
the same job (a real preview in place of a fake score, a specific first action in place of an
outcome promise). A variant that breaks these rules is not offered as a test arm either:
"it converted better" would not make it acceptable.

## Before you deliver

- Two materially different answer sets produce meaningfully different results wherever the
  flow promises personalization.
- Skipping, going back, changing a branch, refreshing, or failing auth each ends in a usable
  state.
- The first signed-in action fulfils the signup promise, and a retry doesn't import twice.
- The flow works on a small screen and with keyboard and screen-reader navigation.
- Nothing breaks the honesty rules.
- Every recommendation carries [R], [V] or [H] (or "outside the source list"), and question
  count, progress indicator and account timing are presented as things to test.
- The measurement plan divides by eligible entrants and names a baseline.
- Assumptions and marked gaps are listed where the reader can correct them.

## Maintaining this skill

Not part of normal work: the test cases for this skill, with expected behaviors and pass
criteria, are in [references/evaluation-cases.md](references/evaluation-cases.md). Open that
file only when changing or testing the skill itself.
