# Entry patterns: does a quiz earn its place?

Use in Step 2, and whenever someone wants a quiz the app may not need. The patterns and the
reasoning are hypotheses [H] drawn from the research report; the only general finding behind
them is that an account request adds perceived effort when the person is trying to do something
else [R: 9]. Sources: [research.md](research.md).

## The five patterns

### 1. Short questionnaire

**Fits when** a personal plan or starting point changes meaningfully with the person's goals
and constraints, and the app can deliver those different starting points today.

**Signals in the product:** several templates or plan types; starter content in different
sizes or levels; different first actions for different obstacles; people in reviews or support
describing clearly different situations.

**What earns the account:** saving, editing and continuing the plan.

**Watch for:** questions added because "quizzes build commitment". A question that changes
nothing is a cost with no return, and the honesty rules forbid it.

### 2. One routing question

**Fits when** one answer changes the starting path and everything else is shared: role,
language, platform, use case with separate home screens.

**What earns the account:** resuming work or keeping the preference.

**Watch for:** routing that only changes a label. The paths have to differ.

### 3. Immediate use

**Fits when** the product can deliver value straight away and the first action is the same for
everyone: converters, generators, editors, calculators, search.

**What earns the account:** preserving a real artifact, history, sync, higher limits,
collaboration. Ask at the moment that value appears ("Save this to your history"), not before.

**Watch for:** a "tell us about yourself" step in front of the tool. It delays the value that
would have made the case for an account.

### 4. Demo or sample

**Fits when** the value depends on data or setup the visitor doesn't have yet, and a realistic
sample can show it: dashboards, analytics, team tools, anything empty until populated.

**What earns the account:** doing the same thing with their own data.

**Watch for:** a demo that shows features the person's plan won't include, or sample data that
implies real customers.

### 5. Identity first

**Fits when** nothing real can be shown without knowing who the person is: private records,
shared workspaces, invitations, permissions, regulated data.

**What earns the account:** access to the real workspace. Say why identity is needed in one
plain line next to the sign-in ("Sign in so we can show your company's invoices").

**Watch for:** qualification questions in front of an invited user. They were asked to do one
thing. Take them to it.

## Decision procedure

1. **Name the activation event.** The first action that shows the person received value.
2. **List what an answer could change about reaching it.** Use the personalization inventory
   from Step 1. Each entry needs two answers and two different first experiences.
3. **Count what survived.**
   - Nothing: patterns 3, 4 or 5, chosen by whether value is immediate, needs sample data, or
     needs identity.
   - One thing: pattern 2.
   - Several things that combine into one result: pattern 1.
4. **Check intent by arrival.** For each traffic source, write what the person came to do.
   Task-now intent pulls toward immediate use. Plan-seeking intent tolerates questions.
   Invitation intent goes to identity first, then the invited task.
5. **Weigh effort against result.** Would an editable default get most people to the same
   place? Then show the default and let them adjust.
6. **Check the constraints.** Sensitive data, regulated advice, minors, a paywall straight
   after signup: each can change the pattern or require review.
7. **Write the decision** with the reasoning, the assumptions it rests on, and what evidence
   would reverse it.

## Combinations that often fit

- **Optional quiz beside immediate use.** "Start now" and "Help me pick a starting point" on
  the same screen. Useful as the first test, because it measures take-up as well as outcome.
- **Routing question, then demo.** One question picks which sample to show.
- **Identity first, then one question.** After sign-in, ask the one thing that sets the home
  screen. Questions after signup are outside this skill's main scope but the same rules apply.
- **Different entries per arrival.** Ad traffic gets the quiz, invite links skip it, returning
  visitors go to sign-in.

## When the user wants a quiz anyway

People ask for quizzes because well-known subscription apps use them [V: 10–12]. That shows
the pattern exists in those products. It does not show what the quiz contributed, and those
products have something most apps lack: a plan that differs by answer.

1. Say what the three tests found, concretely: "all five proposed questions lead to the same
   upload screen".
2. Separate the two goals that usually hide inside the request. "Learn about our users" is a
   research goal and has better tools: an optional question after the person has had value, a
   survey, analytics. "Convert more visitors" is the goal the entry flow serves.
3. Recommend the pattern that fits, and where the account prompt goes in it.
4. If they still want the quiz, design the smallest honest version (often one optional
   question whose answer does change something) and set it up as a test against the pattern
   you recommended, measured per eligible entrant.

Three cases this leaves open:

- **No question changes anything.** Then no honest version exists, and that is the answer.
  Say what would make one possible (a product change that gives an answer something to do,
  such as presets by use), and where their research goal can be met meanwhile.
- **The person who wants the quiz isn't in the conversation.** Give the recommendation, and
  outline the fallback in a few lines so the requester can see it was considered. Don't
  design a full flow nobody has agreed to.
- **The request bundles a signup wall with the quiz** ("quiz, then sign up, then the tool").
  Those are two changes. Putting a wall in front of something that used to be open is its own
  decision, with the cost noted above [R: 9]. Advise against it where the product works
  without an account. If the team decides to test it anyway, the wall is its own arm,
  separate from any questions.

## Special situations

| Situation | What changes |
| --- | --- |
| Health, finances, safety | Suitability, data handling and claims go to qualified owners for review. Define a safe general fallback when answers are missing. Avoid anything that reads as diagnosis or advice the product can't support. |
| Handles money or private records but gives no advice (approvals, payroll, records portals) | A security owner reviews invite links, sign-in, and the isolation of any sample data. The first-run copy doesn't nudge toward the consequential action ("Approve all"). |
| Paywall right after the quiz | Price and terms appear before commitment [R: 13, 14]. Measure trial start, paid conversion, refunds and retention as well as activation. |
| Mobile app from a store | The install already cost effort, and the store listing made the promise. Match the first screen to the listing. Draft storage is on the device. |
| B2B with a buying committee | The person in the flow may not be the buyer. Role is often the one question worth asking. Lead qualification belongs in a clearly labelled contact or demo-request form that the person opens by choice, where each field has a stated use by the salesperson. It is not a gate before the product. Measure per company as well as per person. |
| Marketplace or two-sided app | Route by side first (pattern 2). Each side then gets its own decision. |
| Minors or age-restricted products | Age may be legally required. Ask it plainly, say why, and get the legal owner's review of what follows. |
| Returning visitor with an unfinished draft | Offer to continue where they left off, or start again. Never silently discard or silently reuse. |
