# Screens and copy

Use in Steps 3 and 4. Covers what each screen has to do, how to write it, where proof goes,
and the interface and accessibility behavior. Labels and sources: [research.md](research.md).

## Contents

1. The journey
2. Entry screen
3. Question screens
4. Between-question moments
5. Result screen
6. Account prompt
7. First signed-in screen
8. Proof
9. Navigation and interaction
10. Accessibility checks
11. Copy review
12. Selling it honestly

## 1. The journey

| Screen | Its job | Fails when |
| --- | --- | --- |
| Entry | Say the payoff and what is about to happen | The promise is bigger than the result, or unrelated to why the person came |
| Question | Make the choice and the next action obvious | Two concepts at once, unclear options, no way back |
| Result | Show a specific recommendation and why it fits | Generic output, a score with no basis, no way to adjust |
| Account prompt | Name what the account saves or enables | Vague benefit, hidden requirement, surprise price |
| First signed-in | Open the result or its first action | Blank dashboard, answers asked again |

Write real copy for every one. The sequence itself is [H]; clear, coherent steps are [R: 1–3].

## 2. Entry screen

**Match the arrival.** Someone who clicked an ad about building a morning routine should see
that language and a credible outcome. A direct visitor may need a broader opening. If traffic
sources differ a lot, vary the entry headline by source and keep the rest the same. [H]

**Say what happens next.** One line: what they'll be asked, and what they get.

**Where the entry lives.** The entry is wherever the promise is first made, and that is often
not a screen of its own: the main block of an existing landing page, an invite email, an ad or
a store listing. This skill writes the entry copy and its buttons. It doesn't redesign the
page around them.

**Estimates.** "3 questions" or "about a minute" only if it is true on every branch. Count the
questions everyone is asked and mention optional ones separately ("3 questions, plus one you
can skip"). With branching, say "a few questions". An estimate you can't support is a small
broken promise at the first step.

**Facts you don't have.** When a line depends on something the brief or repo doesn't give (a
limit, a price, the name of a real exercise or lesson), write the line with a marked gap,
`[confirm: free file-size limit]`, and list it under open questions. Don't invent the value.

**Offer the other door.** A visible way to skip to a general start, and a sign-in link for
people who already have an account.

Pattern:

```text
[Headline: the outcome, in the arrival's words]
[One line: what you'll ask and what they'll get]
[Primary button: start]            [Secondary: skip to a general start]
[Small: Already have an account? Sign in]
```

Example: "Find a routine you can fit into your day." / "Answer three questions and we'll
suggest one to start with. You can change anything after." / "Find my routine" / "Skip, show
me a general routine".

## 3. Question screens

- The question as the heading. A one-line helper only when it removes a real doubt.
- Options as large, labelled controls. Radio behavior for single choice, checkbox behavior for
  multiple, and the difference visible.
- For sensitive questions, the reason line sits directly under the question.
- A back control, and a skip where the question is optional.
- A truthful position indicator when the path is fixed ("2 of 3"), stages when branches vary
  ("About you → Your plan"). Whether an indicator reduces drop-off is mixed [R: 7]; its
  job here is orientation [R: 3]. Test it. [H]

## 4. Between-question moments

A short line that shows the last answer did something supports the sense of progress [R: 5 for
the theory, H for the effect]: "Got it: mornings. We'll keep it short." Rules:

- It must be true and specific to the answer.
- It never invents a statistic ("87% of people like you…") without a source the product can
  show.
- It doesn't add a screen. Put it at the top of the next question.
- An intermediate insight screen is a separate hypothesis to test later, once the basic flow
  has been compared with the baseline.

## 5. Result screen

The result is where the product shows fit. It should contain:

1. **The recommendation**, specific enough to act on: what, how long, when.
2. **Why it fits**, traced to the answers: "5 minutes, because you said that's what you can
   spare. It starts with a 2-minute step, because getting started is the hard part."
3. **A first action** the person can see or try now, where the product allows it.
4. **A way to adjust**: edit an answer, or change the result directly.
5. **Honest edges.** If a default was used because a question was skipped, say so.

"Personalized for you" carries no information. The reasoning does the persuading.

Never on a result screen: a score or percentage with no real calculation, a countdown or
"analyzing" delay longer than the real work, an outcome promise the product can't
substantiate ("fluent in 3 months"), or wording that reads as diagnosis.

## 6. Account prompt

**Name the gain.** "Create an account to save this routine" is honest when creating the
account saves the routine. Write the button as the outcome ("Save my routine"), and make sure
the next screen proves it.

**Label the requirement.** Say that an account is needed and why. Don't disguise signup as
"Continue".

**Offer the methods the app already has.** Same providers, same order, same styling as the
app's normal signup.

**If payment follows,** the price, the billing period, trial terms and how to cancel appear
before the person commits [R: 13, 14]. Creating the account is the first commitment made on
the strength of the offer, so the price belongs on or before the account prompt, in the app's
own words, not only on the store's payment sheet. Keep the account line true about what is
usable without paying: "Create a free account to keep this plan. Using it needs a
subscription: $X a year."

**Leave a way back** to the result, and say that the answers are kept.

Pattern:

```text
[Headline: what the account does for the thing they just made]
[One line: what happens next, and that nothing is lost]
[Auth methods as the app already offers them]
[Small: price and terms, if any]   [Small: Back to my result]
```

When the account comes at all is [H]: early when identity is needed, after the result when the
account saves it, only at the moment of saving when the product shows value by itself.

## 7. First signed-in screen

The first screen after signup opens the saved result or the first action it promised, with one
line confirming it: "Your routine is saved. Start the first step?" It does not ask anything
the quiz already asked, and it does not open on an empty state with the result one click away.

### Steps between signup and the product

If something follows before the product (email confirmation, a paywall, permissions), the
result is still waiting on the other side, and the person is told so. Each of these is a
screen in the flow and gets written copy.

- **Email confirmation.** Say that the result is saved, where the email went, and what
  happens when they tap the link: "Your routine is saved. We sent a link to dana@example.com.
  Open it on this device to start." Offer resend and a way to fix a mistyped address.
- **Paywall.** The person already knows the price from the account prompt. "Not now" has a
  defined end state: whatever the product truly offers for free, with the saved result
  visible and the way to subscribe later. If nothing is usable without paying, say so before
  the account prompt, never after it.
- **Permission prompts.** Ask at the moment the benefit is concrete ("Remind me after
  breakfast" leads to the notification prompt), with one line of explanation first.

## 8. Proof

Use proof where it answers a real doubt [H for placement], and only proof that can be backed
up [R: 13, 14]:

| Doubt | Where it arises | Proof that answers it |
| --- | --- | --- |
| "What will I get?" | Entry | A sample result, shown as a sample |
| "Is this for someone like me?" | Early questions | A specific, real customer example, with permission |
| "Why are you asking this?" | Sensitive question | The reason line |
| "Is the result any good?" | Result | The reasoning, and the first action to try |
| "What am I signing up to?" | Account prompt | What is saved, price and terms |

No invented testimonials, user counts, ratings, logos or statistics. If there is no real proof
yet, a sample result is the honest substitute.

## 9. Navigation and interaction

These are standard form-usability practice [R: 1–3]:

- **Back keeps answers.** Returning to a question shows the earlier selection.
- **Edit from the result** where practical, without restarting.
- **Consistent labels.** The same word for the same action on every screen.
- **Explicit Continue** when people need time to read or adjust, and always for multi-select.
- **Automatic advance** on a single choice is a thing to test [H]: check that it doesn't
  surprise, that focus lands sensibly, and that the choice can be undone.
- **Grouping.** Small, closely related inputs can share a screen when that is easier to scan.
- **Errors.** Say what is wrong and how to fix it, next to the field, without clearing input.
- **Refresh and return.** The person comes back to where they were.
- **Changing an earlier answer** clears only what depends on it, and says so.

## 10. Accessibility checks

- Every control has a visible label and an accessible name. Option groups are announced as a
  group with the question as its label.
- The whole flow works by keyboard, with a visible focus indicator and a logical order.
- On each step change, focus moves to the new question's heading, and the change is announced.
- Position ("step 2 of 3") is available as text, not only as a bar.
- Errors are announced and tied to their field.
- Works at 200% zoom and on a small phone without horizontal scrolling. Touch targets are
  large enough to hit.
- Labels survive translation: long strings wrap, and right-to-left layouts mirror correctly.
- Motion respects the reduced-motion setting.
- Usable on a slow network: each step shows quickly, and a failed save can be retried.
- Color is never the only sign of selection.

## 11. Copy review

Read every line and ask:

- Is it true for every person who can reach this screen?
- Is it something the product does today?
- Would the person use this word?
- Does it tell them what happens next?
- Could a number, claim or name on this screen be shown a source if challenged?
- Does the button say what it does?

## 12. Selling it honestly

The first version of a flow tends to come out polite and flat: correct, but it doesn't make
anyone want the result. On the first real use, the owner sent a working flow back with "make it
salesy". Selling and honesty don't pull against each other here. Every lever below is in the
research, and each claim it puts on screen has to be something the product does today.

| Screen | Lever | What it looks like | Basis |
| --- | --- | --- | --- |
| Entry | The outcome, in the person's words, not a feature list | "Start the habits you keep putting off.", not "Your habits and your days, in one place." | Proportional promise [R: 13, 14]; the headline itself [H] |
| Entry | Proof where the doubt is ("what will I get?") | A small example of the result built from the product's real content, labelled "Example" | [R: 13, 14] for substantiation, [H] for placement |
| Entry | Risk reversal, only if true | "Free, no card needed. Change anything later." | [R: 13, 14] |
| Questions | Discovery: goal, then obstacle | "What usually gets in the way?", but only when each answer changes the setup (smaller habits, a different order, fewer to start) | [H], framing from 16 |
| Questions | Show the answer landed | "Got it: busy days. Your habits will be the short versions." at the top of the next question | [R: 5] theory, [H] effect |
| Result | The reasoning sells, not the label | A "why it looks like this" list: each part of the setup "because you said…" | [H], informed by 17 |
| Result | What builds up with use | Streaks, scores, recaps, insights the product really produces, with the condition when there is one ("once you've logged your mood for a few days") | [H]; every line checked against the code |
| Close | Name the gain, the cost and the loss | "Save it, and it's on your Today page the first time you sign in. Free, no card needed. Until you save it, it's only in this browser, and it's cleared after 7 days." | Gain and price [R: 13, 14]; the loss line [H], and it must be literally true |
| Account screen | Answer the last doubt by the button | "Free, no card needed. You can delete your account any time in Settings." | [R: 13, 14] |

Before a line goes in, find the code that makes it true. On the first use, the app's own streak
card promised a freeze "every 7 days" that nothing in the code refilled, so the flow said only
"you start with two", and the stale line was reported to the owner. Write a test that fails if a
line promises something the product doesn't have (reminders, refills, percentages).

What selling never includes, however hard the owner pushes: invented user counts, ratings,
testimonials or "87% of people like you" statistics; countdowns or "offer ends" timers; an
"analysing your answers" wait; a score made up from the answers; outcome promises; a pre-ticked
marketing opt-in; signup disguised as "Continue" [R: 13, 14]. When asked for one, say which
rule it breaks and offer the honest lever from the table that does the same job.

Each lever is a bet for this app [H]. Test the selling version against the plain one per
eligible entrant (see [measurement.md](measurement.md)), because more questions and more copy
can cost more than they earn.

These levers are the floor, not the ceiling. On the first real use, a flow with all of them was
still judged "30% there" next to the best consumer apps. What closed the gap was the
experience around the copy: one question per screen, full-colour "worth knowing" screens with a
cited study, the person's name, a signed plan, honest numbers, and the first real action before
the account. See [top-app-patterns.md](top-app-patterns.md).
