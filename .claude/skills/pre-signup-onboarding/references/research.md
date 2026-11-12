# Research basis

The evidence behind this skill, taken from the report *Designing pre-signup questionnaires:
research and design playbook* (November 2026). Read this when a recommendation needs a source,
when someone asks whether quizzes "work", or when you need to decide how hard to hold a rule.

The summaries below say what the report says each source supports. Open the source itself
before quoting it in something a client or the public will read.

## Contents

1. Labels
2. Headline finding
3. What the evidence does not establish
4. Source register (all links)
5. Findings by discipline
6. Hypotheses each app has to test
7. How to cite this in a deliverable

## 1. Labels

| Label | Meaning | How to use it |
| --- | --- | --- |
| **[R]** | Research finding or standards guidance: peer-reviewed research, meta-analyses, independent usability research, and guidance from public services, standards bodies and regulators | State it as support for a practice. Keep the transfer limit attached. |
| **[V]** | Vendor material: product documentation, company case studies, industry benchmarks | Say that the pattern exists and who uses it. Never use it as proof of effect. |
| **[H]** | Hypothesis: a design choice an individual app has to test | Say "candidate", "starting point", "test this". Attach how to test it. |

## 2. Headline finding

A pre-signup questionnaire can earn the next step by doing two jobs. It helps people recognize
their own situation, then turns what they tell the app into something they can see or use. The
business gets a reason for the person to create an account. The person gets a reason to care.
Whether that exchange improves conversion and activation depends on what the app delivers, the
audience's intent, and the friction the quiz adds. [H]

Starting hypothesis: **promise → relevant questions → visible value → account creation →
immediate continuation**. Start with the valuable thing the app can show or do, work backward
to the minimum information it needs, and compare the result with the app's current entry
point. [H]

## 3. What the evidence does not establish

The sources give stronger guidance on question quality and usability than on any causal,
app-wide signup lift. None of them establishes:

- that adding a pre-signup quiz raises signup or activation in general
- an ideal number of questions
- the best position for the account prompt
- that a progress indicator reduces drop-off
- that fewer answer options always helps

Treat the flow, the question count and the placement of the account prompt as hypotheses. A
test in the app itself is the strongest evidence for that app.

The source list also does not cover, and so cannot be cited for:

- the law on sensitive or health data in any particular country, beyond the general
  data-minimisation principle [15]
- rules for advertising and analytics tools in health, finance or children's products
- age-of-consent and children's privacy rules
- app-store and platform policies
- clinical, financial or safety practice, including how a product should respond when an
  answer signals risk to the person
- security practice for invitations and sign-in

When a design touches one of these, write "outside the source list: to verify with" and name
the owner. Don't present it as a finding.

A note on source 9: Baymard is a commercial research firm. It is labelled [R] because the
item reports its own usability studies and it has no product stake in quizzes, unlike the
[V] sources, which describe or sell the pattern itself.

## 4. Source register

| # | Source | Type | Label | What it supports | Transfer limit |
| --- | --- | --- | --- | --- | --- |
| 1 | [GOV.UK Service Manual, Structuring forms](https://www.gov.uk/service-manual/design/form-structure) | Public-service design standard | R | Document why each answer is needed. Use clear, coherent steps. | Practical guidance. Gives no conversion estimate. |
| 2 | [NHS Digital Service Manual, Get the questions into order](https://service-manual.nhs.uk/content/how-to-write-good-questions-for-forms/get-the-questions-into-order) | Public-service design guidance | R | Order questions coherently. Clear steps. | Practical guidance. Gives no conversion estimate. |
| 3 | [W3C Web Accessibility Initiative, Multi-page Forms](https://www.w3.org/WAI/tutorials/forms/multi-page/) | Accessibility standard guidance | R | Accessible multi-step forms, including telling people where they are in the steps. | Practical guidance. Gives no conversion estimate. |
| 4 | [Pew Research Center, Writing Survey Questions](https://www.pewresearch.org/writing-survey-questions/) | Questionnaire methodology | R | Wording, answer choices and question order can change responses. | The outcome studied is response quality. Signup lift needs its own experiment. |
| 5 | [Ryan and Deci, Self-Determination Theory and the Facilitation of Intrinsic Motivation, Social Development, and Well-Being](https://doi.org/10.1037/0003-066X.55.1.68) | Behavioral theory and research synthesis | R | Autonomy, competence and relatedness give a rationale for choice, attainable steps and feeling understood. | A theory of motivation does not predict the lift from a specific UI. |
| 6 | [National Cancer Institute, Implementation Intentions](https://cancercontrol.cancer.gov/brp/research/constructs/implementation-intentions) (summarizing Gollwitzer and Sheeran's goal-attainment research) | Research summary | R | Linking a concrete action to a situational cue can help people act on an intention they already have. | Supports useful plan content. Signup conversion is a different outcome. |
| 7 | [Villar, Callegaro and Yang, Meta-Analysis of Experiments on Progress Indicators for Web Surveys](https://doi.org/10.1177/0894439313497468) | Meta-analysis | R | Progress cues depend on context. No overall drop-off benefit was found from a constant indicator. | Web surveys differ from app onboarding. Test comprehension and behavior. |
| 8 | [Scheibehenne, Greifeneder and Todd, Meta-Analytic Review of Choice Overload](https://doi.org/10.1086/651235) | Meta-analysis | R | The effect of option count depends on context: a near-zero average effect with substantial variation. | Decision contexts differ from onboarding. Test in the flow. |
| 9 | [Baymard Institute, Checkout Optimization: Minimize Form Fields](https://baymard.com/research-articles/checkout-flow-average-form-fields) | Commercial usability research | R | Asking for an account can add perceived effort at a point when people are trying to do something else. | Checkout has a purchase objective. Apps can have other reasons for requiring identity. |
| 10 | [Noom, Weight Plan Pricing and What to Expect](https://www.noom.com/support/faqs/subscription-and-billing/2025/10/noom-plan-pricing-and-what-to-expect/) | Product documentation | V | Demonstrates a quiz-to-plan offer in a live product. | Shows a pattern. Cannot isolate the quiz's effect. |
| 11 | [Superwall, Cal AI paywall experimentation case study](https://superwall.com/case-studies/cal-ai) | Vendor case study | V | Documents paywall experimentation at one app. | Written by the vendor. Says nothing about ideal quiz length or account signup. |
| 12 | [RevenueCat, State of Subscription Apps 2026](https://www.revenuecat.com/state-of-subscription-apps) | Vendor industry benchmark | V | Category and market benchmarks for subscription apps. | Aggregates cannot isolate a quiz's effect or predict one app's signup. |
| 13 | [FTC, Bringing Dark Patterns to Light](https://www.ftc.gov/reports/bringing-dark-patterns-light) | Regulator report | R | Deceptive design deserves explicit review. Price and terms belong before commitment. | Obligations depend on jurisdiction, data categories and product policies. |
| 14 | [OECD, Dark commercial patterns](https://www.oecd.org/en/publications/dark-commercial-patterns_44f5e846-en.html) | Intergovernmental report | R | Same: deceptive design deserves explicit review. | Same. |
| 15 | [ICO, Data minimisation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/) | Regulator guidance | R | Unnecessary personal data collection deserves explicit review. Decide purpose, retention and deletion first. | UK guidance. Other jurisdictions set their own rules. |
| 16 | [Strategyzer, The Value Proposition Canvas](https://www.strategyzer.com/library/the-value-proposition-canvas) | Practitioner framework | V | A way to turn customer jobs, pains and gains into testable promises. | A working tool, not evidence of effect. |
| 17 | [Aguirre et al., Unraveling the Personalization Paradox](https://doi.org/10.1016/j.jretai.2014.09.005) | Peer-reviewed study (advertising) | R | Transparency about data collection can affect how people respond to personalization. | Studied in advertising. Applying it to this flow is a design hypothesis. |
| 18 | [Kohavi, Tang and Xu, Metrics for Experimentation and the Overall Evaluation Criterion](https://www.cambridge.org/core/books/abs/trustworthy-online-controlled-experiments/metrics-for-experimentation-and-the-overall-evaluation-criterion/0A8BF7F06A1338FF6D10C49F4CD8A198) | Experimentation methodology | R | Choose a primary outcome tied to product value. Define guardrails. | Method, not a result. |
| 19 | [Fabijan et al., Diagnosing Sample Ratio Mismatch in Online Controlled Experiments](https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/) | Experimentation methodology | R | Investigate sample ratio mismatch before interpreting a test. | Method, not a result. |
| 20 | [Lally, van Jaarsveld, Potts and Wardle, How are habits formed (European Journal of Social Psychology, 2010)](https://doi.org/10.1002/ejsp.674); plain summary: [BPS Research Digest](https://bps.org.uk/research-digest/how-form-habit) | Peer-reviewed study, 82 people over 12 weeks | R | A daily habit took 66 days on average to reach automaticity (18 to a predicted 254). Missing one day made little difference. | Small sample, self-reported automaticity, and over half didn't fit the curve well. Quote "on average, in one study", never "it takes 66 days". |
| 21 | [Judah, Gardner and Aunger, Forming a flossing habit (British Journal of Health Psychology, 2013)](https://pubmed.ncbi.nlm.nih.gov/22989272/) | Peer-reviewed exploratory study | R | Flossing after brushing (an existing routine as the cue) built a stronger habit than flossing before. | Exploratory, one behaviour. Use as an illustration, not a law. |
| 22 | [Sheeran, Listrom and Gollwitzer, The when and how of planning: 642 tests of implementation intentions (European Review of Social Psychology, 2024)](https://doi.org/10.1080/10463283.2024.2334563) | Meta-analysis | R | Planning when and where you'll act makes people more likely to follow through, across hundreds of tests. | Effects are smaller after correcting for publication bias. Say "more likely", never a number. |
| 23 | [Nunes and Drèze, The Endowed Progress Effect (Journal of Consumer Research, 2006)](https://doi.org/10.1086/500480) | Peer-reviewed field experiment | R | People given a head start on a progress card completed it more often. | The study gave artificial progress. The honest version is real progress: something the person really did before signup. |
| 24 | [Buell and Norton, The Labor Illusion (Management Science, 2011)](https://doi.org/10.1287/mnsc.1110.1376) | Peer-reviewed experiments | R | Visible effort can raise perceived value. | Explains why "building your plan" loaders exist. It is no licence for a fake wait: show the real reasoning instead. |
| 25 | [ScreensDesign onboarding captures (Fabulous, Duolingo, Opal, Cal AI, Finch, Flo, Liven, Atoms and others)](https://screensdesign.com/apps/fabulous-daily-habit-tracker/) | Recorded app flows | V | Shows which patterns top apps use: one question per screen, name asked and reused, insight screens, plan reveals, commitment screens, a real action before the account. | One recorded run per app, so one version or test arm. Shows that a pattern exists, not what it did. |
| 26 | [RevenueCat, Noom's web-to-app onboarding funnel](https://www.revenuecat.com/blog/growth/web-to-app-onboarding-funnel/) | Vendor teardown | V | A long quiz funnel in detail: why-we-ask lines, a dated and sourced user count, loaders, an email gate, a paywall. | A teardown of one funnel. Includes patterns this skill rules out (timers, an outcome date). |
| 27 | [Taplytics, Duolingo's onboarding test](https://taplytics.com/blog/duolingo-ab-test-onboarding) | Company account, retold by a vendor | V | Moving signup after the first lesson was reported to raise daily active users by about 20%. | Self-reported, no method published. Evidence that a pattern is worth testing, not a forecast. |
| 28 | [Irrational Labs, Headspace case study](https://irrationallabs.com/case-studies/headspace-doubled-course-starts/) | Consultancy case study | V | A matching quiz doubled course starts. Planning days and triggers raised app opens, but not days meditated. | Reports its own null result: commitment and planning screens raise starts, not necessarily the habit. |
| 29 | [Amplitude, How Calm increased retention](https://amplitude.com/blog/calm-increased-retention-amplitude) | Vendor case study | V | Asking for a reminder right after the first session: 40% set one, against under 1% who found the setting. | Vendor material, no sample sizes. Only applies to an app that has reminders. |
| 30 | [Adapty, How to fix your onboarding flow](https://adapty.io/blog/how-to-fix-your-onboarding-flow/) | Vendor benchmarks | V | Mixed results for "customizing" loaders: one client gained trial starts, another gained by removing the loader. | Unnamed clients, vendor-reported. Shows that a loader is a bet, not a rule. |

Sources 20 to 30 were added on 2026-11-11, after the first real use, from a teardown of top
consumer onboarding flows and a check of the habit-formation studies quoted on screen. They are
not from the original report. Patterns, with what each source supports: [top-app-patterns.md](top-app-patterns.md).

## 5. Findings by discipline

### Deciding whether to use a quiz

- Choose the first action that tells you the person received value, then ask what an answer
  could change about that action. [H, with the framing from 16]
- If two different answers lead to the same first experience, one common path is usually the
  better starting hypothesis. [H]
- If the app requires an account to provide value, test whether a sample, a demo or a clear
  explanation makes the requirement understandable. [H]
- Asking for an account adds perceived effort when the person is trying to do something
  else. [R: 9, from checkout]
- A recommendation that could affect health, finances or safety needs review by qualified
  owners and a safe fallback when answers are missing. [H as a design rule; the claims and
  data-handling parts of that review rest on 13–15]

### Marketing and sales

- Match the first screen to the acquisition promise. A direct visitor may need a broader
  starting question. [H]
- Use a time or step estimate only when you can support it. Keep the promise proportional to
  what the product delivers. [R: 13, 14]
- Treat questions as discovery: the job, what gets in the way, the constraints that change the
  recommendation. [H, framing from 16]
- Reflect the answer through the recommendation itself. "Personalized for you" carries little
  information. "Start with a 5-minute routine after breakfast because you said evenings are
  unpredictable" shows the reasoning and gives a usable action. [H]
- Place proof (a sample result, a specific customer example) near the point of doubt and
  substantiate it. [R: 13, 14 for substantiation; H for placement]
- Name what the person gains immediately at the account prompt. If payment follows, make the
  price and terms clear before commitment. [R: 13, 14]
- Account timing is a choice: early when identity is necessary, after a result when the
  account saves it, never-until-needed when the product demonstrates itself. [H]
- Quiz-to-plan funnels exist in successful subscription apps. [V: 10, 11, 12] That is not
  evidence of what the quiz contributed.

### Psychology and question design

- Self-relevance: use the stated goal to change the substance of the next screen, and explain
  which input mattered when the link is not obvious. [H, informed by 17]
- Autonomy: meaningful choices, an honest skip, a way to correct answers. An opt-out is
  meaningful when the resulting experience still works. [R: 5 for the theory]
- Competence and momentum: start with a question the person can answer confidently and give an
  early sign the answer did something. In a habit product, a realistic if-then action can make
  the result easier to use. [R: 5, 6]
- Progress: a truthful step count when the path is fixed, stages or a verified estimate when
  branches vary. Whether an indicator reduces drop-off is mixed. [R: 3, 7]
- Cognitive effort: one concept at a time, distinct options that cover real answers, an
  uncertainty option where it is meaningful. Reduce choices when it makes the decision easier
  to understand; keep coverage when it matters. [R: 4, 8]
- Sensitivity: sensitive questions later, explained where the person sees them, with an
  alternative and neutral wording. [R: 4, 15]
- Record each question's purpose, where its answer changes the experience, who sees it,
  whether it is optional, the skip behavior and the data handling. [R: 1]
- Wording, options and order change answers. Prefer concrete, neutral wording, avoid
  double-barrelled questions, and review option order where position could bias. [R: 4]
- Remove any question that only feeds marketing segmentation unless it has a clear purpose and
  an appropriate collection path. [R: 1, 4, 15]

### UI, accessibility and implementation

- Design the whole journey: entry explains the payoff, question screens make the choice and
  next action obvious, the result is specific, signup names what it saves, and the first
  signed-in screen opens the promised thing. [R: 1–3 for step clarity; H for the sequence]
- Preserve selections on back navigation, allow correction from the result, distinguish single
  from multiple selection, use an explicit Continue where people need time to read or adjust,
  especially for multi-select. [R: 1–3]
- Clear error messages, accessible labels and focus handling. Test keyboard, screen reader,
  zoom, touch, long translated labels and slow networks. [R: 1–3]
- Make personalization traceable with explicit rules or a decision table, conflict priority,
  skip fallbacks and invalidation rules. Where generative output is used, test relevance and
  consistency and that it does not invent capabilities or imply diagnostic precision. [H for
  the method; R: 13, 14 for not misleading]
- Handoff: use existing auth, decide how the draft survives, attach it once, handle retries,
  duplicate callbacks, OAuth cancellation, expiry and existing accounts. Keep raw sensitive
  answers out of analytics and URLs. Decide purpose, retention and deletion first. [R: 15 for
  data handling]

### Measurement

- Primary outcome tied to product value: activated users within a defined window divided by
  all eligible entrants assigned to the flow. [R: 18]
- Report account creation per entrant as secondary, and use completion and per-step drop-off
  to diagnose friction. For subscription apps add trial, paid conversion, refunds and
  retention. [R: 18]
- Randomize before the first variant screen, keep assignment stable, compare all assigned
  users including those who skip or abandon, validate deduplication, identity linkage and
  balance, and investigate sample ratio mismatch first. [R: 18, 19]
- Set the metric, guardrails, minimum effect, sample size or a valid sequential rule, and the
  window before reading results. [R: 18]
- Test in decision order: current entry versus a short, optional, truly personalized quiz
  first, then one uncertainty at a time. [H]

## 6. Hypotheses each app has to test

1. A quiz-led entry produces more activated users per eligible entrant than the current entry.
2. The chosen number of questions is better than fewer.
3. Showing a result before the account prompt beats asking for the account first.
4. A progress indicator helps people orient without increasing drop-off.
5. An intermediate insight between questions keeps people going.
6. Explaining which answer shaped the result increases trust in it.
7. Automatic advance on single-choice questions is not surprising and can be undone.
8. The entry promise matched to the traffic source beats a general one.
9. A real first action before the account (a check-in, a lesson, a first entry) raises
   activation per entrant, not just signups.
10. "Worth knowing" screens that answer the person's last answer with a cited study keep more
    people going than the same flow without them.
11. A signed commitment ("My plan", "I'm in") changes what people do afterwards, not only how
    many start.

Each is written as a claim that could turn out false. The first one is the test to run first.

## 7. How to cite this in a deliverable

- Put the label next to the recommendation, and the source when it is [R] or [V]:
  "Explain why the question is asked, next to the question. [R: GOV.UK form guidance; ICO
  data minimisation]"
- The numbers in this file are for use inside the skill. The reader of a deliverable hasn't
  seen this register, so name sources there and finish with a list of the ones used, with
  their links copied from section 4.
- For [V], write what the company does, never what it gained: "Noom uses a quiz-to-plan
  offer [V: 10]".
- For [H], attach the test: "Three questions is a starting point [H]; compare against one."
- Never write a percentage lift unless it comes from the app's own test.
