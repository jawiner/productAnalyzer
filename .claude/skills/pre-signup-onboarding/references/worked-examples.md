# Worked examples

Five short examples, one per entry pattern plus an audit, showing the reasoning and the shape
of the output. Read one when you want to see what "done" looks like, then design from the real
app in front of you. Real products often mix patterns (different arrivals, a request that
pulls the other way), and the examples deliberately don't. Copying an example's questions into
another product is the failure this skill exists to prevent.

## Contents

1. LifeMaxing: a short questionnaire (illustrative)
2. A QR-code generator: immediate use, no quiz
3. A tenant portal: identity first
4. A web-analytics dashboard: demo with one routing question
5. A meal-planning app: audit of an existing quiz

---

## 1. LifeMaxing: a short questionnaire

**Illustrative only.** LifeMaxing's real features and user research were not supplied when
this example was written. The capabilities below are assumed so the example can be complete.
On the real repo, Step 1 replaces them with the personalization inventory found in the code.

**Assumed capabilities:** routines in a few focus areas; each available in short and longer
sizes; a first step that differs by obstacle; an optional reminder tied to a moment in the day.

**Assumed activation event:** completing a first routine within seven days, if that fits
normal LifeMaxing usage.

### Decision

Short questionnaire. Goal, obstacle and available time each change the starter routine
(different area, different first step, different length), so three answers produce a visibly
different start. A fourth, optional answer attaches a cue. [H: compare against the current
entry.]

### Screens

**Entry**

> **Find a routine you can fit into your day.**
> Three questions, plus one you can skip, then we'll suggest a routine to start with. You can
> change anything after.
> [Find my routine] · [Skip, show me a general routine] · Already have an account? Sign in

**Question 1 of 3: What would you like to improve first?**
Focus · Energy · Sleep · Calm · Not sure yet

**Question 2 of 3: What tends to get in the way?**
Getting started · Interruptions · Running out of time · Forgetting · Not sure

**Question 3 of 3: How much time can you realistically spare on a typical day?**
5 minutes · 15 minutes · 30 minutes

**Optional: When is it easiest to fit this in?**
After breakfast · At lunch · After work · Before bed · I'll decide later

**Result** (for Focus, Getting started, 5 minutes, After breakfast)

> **Your starter: a 5-minute focus routine, after breakfast.**
> - 5 minutes, because that's what you said you can spare.
> - It opens with a 2-minute starter step, because getting started is the hard part.
> - After breakfast, so there's a clear moment for it.
>
> First step: *Put your phone in another room and write down the one thing you'll work on.*
> [Change my answers] · [Save my routine]

**Account prompt**

> **Create an account to save this routine.**
> It'll be waiting for you tomorrow morning, and you can edit it any time.
> [Continue with Google] · [Sign up with email] · Back to my routine

**First signed-in screen:** the saved routine, open, with "Your routine is saved. Start the
first step?"

### Question protocol (condensed)

| | Q1 goal | Q2 obstacle | Q3 time | Q4 cue (optional) |
| --- | --- | --- | --- | --- |
| Changes | Which focus area the routine comes from | Which first step opens the routine | The routine's length | Adds "after [moment]" and the reminder time |
| Skip / not sure | General starter routine | Standard first step | n/a: defaults to 5 minutes, editable | No cue; "add a reminder later" |
| Data handling | Low sensitivity, option ID stored in the draft | Same | Same | Same |

### Mapping (extract)

| Goal | Obstacle | Time | Result |
| --- | --- | --- | --- |
| Focus | Getting started | 5 | 5-minute focus routine, opens with a 2-minute starter |
| Focus | Interruptions | 5 | 5-minute focus routine, opens by reducing interruptions |
| Focus | Running out of time | 5 | 5-minute focus routine, standard opening, "minimum version" note |
| Not sure | any | any | General starter routine at the chosen length |

Priority: time caps length whatever else is chosen. Invalidation: changing the goal keeps
obstacle and time.

### Two-answer-set check

| | Dana | Omar |
| --- | --- | --- |
| Answers | Focus, getting started, 5 minutes | Focus, interruptions, 5 minutes |
| First action | Phone away, write the one thing | Tell the people around you you're unavailable for 5 minutes, close chat apps |
| Why it fits | "…because getting started is the hard part" | "…because interruptions are what stop you" |

Same goal and time, different obstacle, different opening. This passes only if the product
supports both openings. If it has one opening for everyone, question 2 goes.

### Handoff

Draft in browser storage (answers are low sensitivity), 14-day expiry, attached once by
`draft_id` on first authenticated load. Existing account: keep their routines, offer "Add this
routine?". OAuth cancelled: back to the account prompt with the routine intact.

### Measurement

Baseline: the existing entry. Primary: first routine completed within seven days ÷ all
eligible entrants assigned. Tracked separately: signup per entrant, time to first action,
`draft_restored`. [H] until tested: three questions versus one, the "2 of 3" indicator, and
asking for the account after the result.

---

## 2. A QR-code generator: immediate use

**Brief:** a web tool that turns a link into a QR code. An account gives saved codes, scan
counts and editable destinations. The owner asks for "an onboarding quiz like the big apps".

**Tests.**
1. Does an answer change anything? Candidate questions: what the code is for, business or
   personal, how many codes. Every answer leads to the same first action: paste a link, get a
   code. Nothing survives.
2. Intent: people arrive from search wanting a code now.
3. Effort: any question delays the one thing they came for.

**Decision:** immediate use. No quiz. The quiz-to-plan pattern exists in subscription apps
where the plan differs by answer [V: 10–12]; here nothing differs.

**Where the account earns its place:** after the code exists.

> Your code is ready. [Download]
> **Want to change where it points later, or see how often it's scanned?**
> Create a free account to save this code. · [Save my code] · No thanks

**First signed-in screen:** that code, saved, with its (empty) scan count and "Edit
destination".

**If the owner still wants to learn about users:** one optional question after the download
("What's this code for?"), stated purpose, not blocking, answer kept out of ad pixels.

**Measurement:** primary is codes saved-and-used (a scan or an edit within 14 days) per
eligible entrant. If they insist on a quiz, test it against this flow, all assigned entrants in
the denominator.

---

## 3. A tenant portal: identity first

**Brief:** tenants see their rent statements and report repairs. Every tenant arrives the same
way: a text from their property manager, "Your repair request has an update."

**Tests.** Nothing can be shown without knowing who the tenant is: the statements and repair
history are private. The text message already says why they came. No answer could change what
they should see first.

**Decision:** identity first, no questions. The text message is the entry screen.

> **Sign in to see the update on your repair.**
> We ask you to sign in so only you can see your home's records.
> [Continue with the code we text you]

**After sign-in:** the repair request the message was about, open. Not the portal's home page.

**Handoff:** an expired link leads to "This link has expired. Ask your property manager to
send a new one", never a generic error. A code sent to a different phone number than the one
invited is refused with a plain explanation.

**Measurement:** first repair update viewed per invited tenant, within 7 days of the text.

---

## 4. A web-analytics dashboard: demo with one routing question

**Brief:** site owners install a snippet and get traffic reports. A new account is empty until
data arrives, which takes a day. Visitors come from the website.

**Tests.** Value needs data the visitor doesn't have yet, so nothing real can be shown at once,
and immediate use isn't possible. One answer does change something: the kind of site decides
which reports matter, and there are three sample dashboards.

**Decision:** demo, opened by one routing question.

> **See what your reports will look like.**
> What kind of site do you run?
> Online shop · Blog or media · Software product · Something else [text field]

"Something else" opens the general sample. Each sample carries a visible "Sample data" label.

**Where the account earns its place:** when they try to make it theirs.

> **Connect your own site to see your real numbers.**
> Create a free account and we'll give you the snippet to install. Data starts arriving
> within a day. · [Connect my site] · Keep exploring the sample

**After signup:** the install step, with the chosen site type already set. While the account
is empty it shows the sample, labelled, and says when real data will replace it.

**Measurement:** first real report viewed within 14 days per eligible entrant. Guardrail:
snippet installs that never send data.

---

## 5. A meal-planning app: audit

**Situation:** a seven-question quiz, then "Calculating your metabolic profile…" for six
seconds, then "Your plan: 92% match", then signup, then a paywall. After paying, everyone sees
the same recipe list. The team reports "quiz completers convert at twice the rate of
non-completers".

**Findings, in priority order.**

1. **Dishonest, fix now.** "92% match" has no calculation behind it, and the six-second
   "metabolic profile" does no work. Remove both. "Metabolic profile" implies a health
   assessment the product doesn't perform: needs review by a qualified owner. [R: 13, 14]
2. **Broken handoff, fix now.** Answers about diet and household size aren't used after
   signup. Either the recipe list filters by them or the questions go.
3. **Price appears only after signup.** Show price and terms before the person commits.
   [R: 13, 14]
4. **The headline number is a selection effect.** Completers versus non-completers compares
   people who chose to finish with people who didn't. It says nothing about what the quiz
   caused. Needed: random assignment, and paid-and-cooked-a-first-recipe per eligible entrant.
   [R: 18]
5. **Test next.** A three-question version (diet, household size, cooking time), each wired to
   the recipe filter, against the current entry. [H]

**What the audit can't say:** whether a quiz helps this app at all. No assignment event
exists, so the first deliverable is instrumentation.
