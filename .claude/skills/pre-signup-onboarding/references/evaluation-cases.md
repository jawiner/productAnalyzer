# Evaluation cases

Five cases for checking that this skill still behaves after it is changed. Each has a prompt,
the behavior expected, and pass criteria that can be judged from the response alone.

This file is for maintaining the skill. Do not read it while doing a real design, audit or
build, and never show it to an agent that is being tested: it contains the answers.

This file is the single source for the cases. The folders under `evals/` are generated from it
by `scripts/build_evals.py`. Edit here, then regenerate.

## Contents

- How to run the cases
- How to grade
- Case: habit-app-earns-short-quiz
- Case: utility-starts-immediately
- Case: b2b-identity-before-questions
- Case: sensitive-answers-minimized
- Case: audit-signup-up-activation-down
- What the cases do not cover

## How to run the cases

Run each case in a fresh agent that has not seen this file.

1. Make a copy of the skill folder for the test, and delete this file and the `evals/` folder
   from the copy. Telling the agent not to open them is not enough: an agent that lists the
   folder sees the grader file names, and those hint at what is graded.
2. Give the agent the path to the copy and the case prompt, and tell it to read `SKILL.md` and
   follow it.
3. The agent cannot ask questions in a test. Tell it to proceed on labelled assumptions where
   the skill would ask.
4. Save the full response to a file.
5. Give a second fresh agent the response and the pass criteria, and have it grade each
   criterion pass or fail with a quoted line as evidence.

With a Claude Code version that has `claude plugin eval`, the same cases run from the skill
folder with `claude plugin eval .` (these are real, billed model runs).

After editing this file: `python scripts/build_evals.py` regenerates `evals/`, and
`python scripts/check_package.py` confirms the package is consistent.

## How to grade

- A criterion passes only when the response contains clear evidence for it. A vague gesture
  ("consider accessibility") does not pass a criterion that asks for something specific.
- A case passes when every criterion passes.
- A failed criterion points at the skill, not at the test, unless the criterion turns out to
  be ambiguous. Fix the instruction that should have produced the behavior, and prefer
  explaining why over adding a rule.

---

## Case: habit-app-earns-short-quiz

**Tests:** an app where answers change the first experience. The skill should choose a short
questionnaire, trace every question to a change, and write the whole flow.

**Mode:** Design

### Prompt

```text
I'm building Dayloop, a habit app (React web app, Supabase auth with Google and email + password; email confirmation is on). Design the pre-signup onboarding for it.

Today the landing page button goes straight to the sign-up form, and a new account lands on an empty "My habits" screen with a + button.

Most new visitors come from TikTok ads that say "Finally stick to a habit. Start with 2 minutes." About 1,200 people a week reach the landing page and roughly 22% create an account. We don't track anything after that yet.

What the app can really do today:
- Starter habit packs for four goals: energy, focus, fitness, sleep. Each pack has 3 habits.
- Every habit comes in three sizes: tiny (2 minutes), standard (10 minutes), full (30 minutes).
- Reminders can be anchored to something the person already does (after coffee, after brushing teeth, after work, before bed) or to a clock time.
- "Restart mode": no streak counter, and a weekly check-in instead of a daily one. Built for people who quit when they break a streak.
- Accountability partner: invite one friend who sees your check-ins. Needs an account.

For us a user is activated when they check in a habit for the first time. The app is free, with an optional Pro plan later. No paywall at signup.
```

### Expected behaviors

- Chooses a short questionnaire because goal, obstacle and available time each change the starting habit, and says what would change that decision.
- Works backward from a real result (a starter habit with a size, a reminder and a mode) to the fewest questions that fill it.
- Writes the copy for every screen and matches the entry to the TikTok promise.
- Gives every question options, a traced effect and a working skip.
- Shows two answer sets ending in different results built only from listed capabilities.
- Specifies a handoff that survives OAuth, email confirmation and an existing account, and opens the saved result.
- Measures first check-in per eligible entrant against the current flow, and labels length, progress and account timing as things to test.

### Pass criteria

1. The response recommends a short questionnaire as the entry pattern and justifies it by showing that answers change the starting habit, its size, its reminder or its mode.
2. Every question in the design lists its answer options and states what the answers change in the result, and no question is included whose answer changes nothing (for example "how did you hear about us" or age).
3. Every question has a stated skip or "not sure" behavior, and the skip path still produces a usable starting habit.
4. The response shows at least two different answer sets that lead to materially different results (a different pack, size, reminder type or mode), and each result uses only capabilities listed in the prompt.
5. The response contains the actual wording for the entry screen, each question, a result screen, the account prompt and the first signed-in screen (written copy, not descriptions of copy).
6. The entry screen copy reflects the TikTok ad's promise (sticking to a habit, starting small or with 2 minutes).
7. The account prompt names what the account saves or enables, and the first signed-in screen opens the saved result or its first action instead of the empty "My habits" screen.
8. The handoff covers how answers survive the Google sign-in redirect, a cancelled sign-in and the email confirmation step, and says what happens for a person who signs in to an existing account.
9. The primary metric is a first habit check-in within a stated time window divided by all eligible entrants (landing visitors assigned to the flow), not divided by signups; signup rate, quiz completion and step drop-off are reported as secondary or diagnostic measures and not as the deciding metric; the current sign-up-first flow is the baseline.
10. Question count, the progress indicator and the timing of the account prompt are presented as hypotheses or choices to test, and the response does not state an expected conversion lift figure.
11. The designed flow contains no fabricated score, fake processing delay, invented testimonial or invented statistic.

---

## Case: utility-starts-immediately

**Tests:** an app where every visitor does the same first thing. The skill should decline the
requested quiz, recommend immediate use, and find the moment an account adds value.

**Mode:** Design

### Prompt

```text
We run Squish, a browser tool that compresses and resizes images (Next.js, Clerk for auth). Everybody does the same thing: drop an image, pick a size, download. That works without an account for one file at a time. A free account adds batch upload (up to 50 files) and a 30-day history of your files. Pro is $6 a month for bigger files.

About 90% of our traffic is Google search for things like "compress image online" and "resize jpg".

Our marketing lead wants a 5-question quiz before people can use the tool, "because quiz funnels convert": 1) your role, 2) company size, 3) how you heard about us, 4) what you'll use Squish for, 5) team size. Then the sign-up form, then the tool.

Design the pre-signup onboarding for us.
```

### Expected behaviors

- Runs the "does an answer change anything" test on the five proposed questions and finds that none changes the first experience.
- Recommends immediate use, says so plainly even though a quiz was requested, and explains the reasoning from intent and effort.
- Places the account prompt where batch upload or history becomes useful, with copy that names it.
- Treats "quiz funnels convert" as vendor-level evidence that does not transfer, without quoting a lift.
- Gives the marketing lead an appropriate way to learn about users, and says what happens if they insist: the smallest honest quiz as a test, or a plain statement that none exists here.
- Measures a value outcome per eligible entrant against the current flow.

### Pass criteria

1. The response recommends immediate product use (the tool available before any questionnaire or signup) as the entry pattern, and does not recommend the 5-question quiz as the default.
2. The response explains that the proposed questions do not change the first experience (everyone drops an image, picks a size, downloads), naming at least role, company size and "how you heard about us" as questions that change nothing for the person.
3. The response identifies a specific moment where an account adds value (batch upload or file history) and places the account prompt at that moment, with written copy that names what the account enables.
4. The response does not claim that quizzes generally raise conversion and does not cite a conversion lift figure; it says the effect of a quiz is unproven for this app or has to be tested.
5. The response says where the information the marketing lead wants could be collected appropriately (optional, after the person has had value, with a stated purpose, or through analytics for attribution) instead of gating the tool.
6. The measurement plan uses an outcome tied to product value (such as a completed compression or download, or an account-enabled action) per eligible entrant, with the current flow as the baseline.
7. The response addresses what to do if the team still wants a quiz: it either gives the smallest honest version or states plainly that no honest version exists because no answer changes anything, and it says that any quiz or sign-up wall the team tests anyway is compared against immediate use over all assigned entrants.
8. Assumptions the design rests on are listed and labelled as assumptions.

---

## Case: b2b-identity-before-questions

**Tests:** an app whose data can't be shown without identity, with two kinds of arrival. The
skill should put sign-in where access needs it, and consider a demo for evaluators.

**Mode:** Design

### Prompt

```text
Signoff is our B2B tool for approving supplier invoices. Invoices and approval chains live inside a company workspace. Stack: Rails, Devise with Google Workspace and Microsoft sign-in, SAML for bigger customers.

Two kinds of people show up for the first time:
1. Invited approvers. Their finance admin adds them, and they get an email: "You have 3 invoices waiting for approval." They click through.
2. Finance leads evaluating us from the website. They can start a self-serve trial with a work email or request a demo.

Nothing real can be shown without the workspace, since it's the company's financial data. Each role gets a different home screen: approvers see their queue, AP clerks see invoice intake, finance admins see chains and reports. We also have a sandbox company with fake invoices that we use in sales demos.

Activation: for an approver, the first invoice approved or rejected. For a finance admin, the first approval chain created.

Sales wants a 7-question qualification quiz in front of both the invite link and the trial signup (company size, annual invoice volume, ERP, budget, timeline, decision maker, phone number). Design the first-run experience.
```

### Expected behaviors

- Separates the two arrivals and decides each one independently.
- Sends invited approvers through sign-in to their waiting invoices with no quiz, and explains in the copy why sign-in is needed.
- Considers the sandbox company as a labelled demo for evaluators before or alongside the trial account.
- Keeps only questions that change the experience (role), and moves sales qualification to a labelled path that doesn't gate the product.
- Covers invite expiry, SSO failure and existing accounts.
- Measures each arrival by its own activation event per eligible entrant.

### Pass criteria

1. For invited approvers, the response places sign-in first and takes them straight to the invoices waiting for them, with no qualification quiz in front of the invite link.
2. The response includes written copy that explains to the person why sign-in is required (private company or financial data).
3. For website evaluators, the response considers showing value before or alongside account creation through the sandbox company or another demo with sample data, labelled as sample data.
4. The response treats the two arrival types as separate flows with separate recommendations.
5. Any question kept in a flow is tied to a difference in experience (for example role selecting the home screen), and qualification-only questions (budget, timeline, decision maker, phone number) are removed from the gate or moved to a clearly labelled, optional or sales-specific path such as the demo request form.
6. The handoff covers at least an expired or invalid invite link, cancelled or failed single sign-on, and a person who already has an account.
7. Measurement is defined per arrival type using the stated activation events (first invoice approved or rejected; first approval chain created) per eligible entrant, not only signups or leads.
8. The response does not state an expected conversion lift, and labels account timing or the demo-first choice as something to test.

---

## Case: sensitive-answers-minimized

**Tests:** an app handling sensitive answers, with a request that includes a fabricated score,
a fake delay and hidden pricing. The skill should minimize collection, refuse the dishonest
parts, and flag what needs specialist review.

**Mode:** Design

### Prompt

```text
Steady is a self-help app for anxiety and low mood: short CBT-style exercises. It is not therapy and there are no clinicians. iOS and Android (React Native, Firebase auth), users in the EU and the US. Mixpanel and the Meta pixel are on every screen.

What the app can vary today: exercise track (worry, sleep, panic, low mood), session length (3, 10 or 20 minutes), and a reminder time.

The founder wants this before signup:
- 12 questions: main symptoms, any diagnosis, current medication, thoughts of self-harm, sleep hours, alcohol use, age, gender, relationship status, how long you've felt this way, what you've tried, preferred time of day
- then "Analyzing your answers…" for 10 seconds
- then "Your anxiety score: 78/100. Your personalized plan is ready"
- then create an account, then a $59.99/year paywall with the price shown only on the App Store sheet

Design the pre-signup onboarding.
```

### Expected behaviors

- Cuts the twelve questions down to those that fill the three things the app can vary.
- Refuses the invented score and the fixed delay, explains why, and offers the honest version.
- Flags the self-harm question and the health-data handling for qualified review instead of deciding them alone.
- Keeps sensitive answers out of analytics, pixels and URLs, and specifies draft storage and expiry.
- Explains each remaining sensitive question in place, with a working "prefer not to say".
- Shows the price and terms before commitment.
- Frames the result as a starting exercise, with no diagnostic language, and gives a general start to people who skip.

### Pass criteria

1. The response reduces the question set to questions whose answers change something the app can deliver (track, session length, reminder time) and removes or explicitly challenges questions that map to no capability, naming at least diagnosis, medication, alcohol use, gender and relationship status.
2. The response rejects the invented "anxiety score: 78/100" (or permits a score only if it comes from a validated instrument with qualified review) and rejects the fixed 10-second "analyzing" delay.
3. The response flags the self-harm question for review by a qualified clinical or safety owner, and says the product needs a defined response (such as crisis resources) if such a question is asked, instead of deciding it alone.
4. The response flags legal or privacy review for health data (for example special-category data under GDPR) and addresses the Meta pixel and Mixpanel on quiz screens.
5. The response keeps sensitive answers out of analytics events, ad pixels and URLs (in a native app: screen names, deep links and logs), and specifies where the anonymous draft is stored and when it expires.
6. Each sensitive question that remains has a reason shown where it is asked, a skip or "prefer not to say" that still leads to a working result, and a position after easier questions.
7. The price and billing period ($59.99 a year) are shown to the person before they commit, earlier than the App Store sheet.
8. The result is framed as a starting exercise or plan and avoids diagnostic or treatment-outcome claims.
9. Skipping the whole questionnaire leads to a usable general starting point.

---

## Case: audit-signup-up-activation-down

**Tests:** an existing quiz with higher signup and lower activation, compared before and
after. The skill should recompute per eligible entrant, question the comparison, find the
broken handoff and order the fixes.

**Mode:** Audit

### Prompt

```text
Pace is our language-learning app. Six weeks ago we put a 9-question quiz in front of signup. Signup rate per landing-page visitor went from 18% to 26% and the team is celebrating. But the share of new accounts that finish a first lesson within 7 days dropped from 52% to 31%.

The quiz:
1. Which language do you want to learn?
2. Why are you learning? (travel / work / family / fun)
3. What's your current level?
4. Your age range
5. How did you hear about us?
6. Daily goal (5 / 10 / 20 minutes)
7. What's your biggest obstacle?
8. When do you want to be fluent by?
9. Allow notifications?

Then "Building your plan…" for 8 seconds, then a result page: "Your personalized plan is ready! You'll be conversational in 3 months", then the sign-up form. After signup everybody lands on the same course picker and chooses language and level again.

We compared the 6 weeks since launch with the 6 weeks before. The quiz went to 100% of visitors. Events we have: quiz_started, quiz_completed, signup_completed, lesson_completed.

Is the quiz working? What should we do?
```

### Expected behaviors

- Multiplies through to first lessons per landing visitor (about 9.4% before, about 8.1% after) and says the quiz is not winning on activation.
- Says the before/after comparison limits what can be concluded, and proposes a randomized test over all assigned visitors.
- Finds that the answers are thrown away at signup and that language and level are asked twice, and ranks that first or near first.
- Finds the questions that change nothing, the unsupported fluency promise and the fake delay.
- Gives fixes in priority order, separating "fix now" from "test".
- Lists the missing events.
- Offers causes for the mixed result as hypotheses with something to check.

### Pass criteria

1. The response computes first-lesson completion per landing visitor for both periods (about 9.4% before and about 8.1% after, from 18% x 52% and 26% x 31%) and concludes that activation per visitor fell even though signup rose.
2. The response does not call the quiz a success on the strength of the signup rate.
3. The response points out that the comparison is before/after with no random assignment, says this limits what can be concluded, and proposes a randomized test with stable assignment that counts all assigned visitors.
4. The response identifies the handoff as broken (answers not carried past signup, the same course picker for everyone, language and level asked again) and ranks fixing it among the top priorities.
5. The response flags questions whose answers change nothing for removal or relocation, naming at least two of: age range, "how did you hear about us", "when do you want to be fluent by".
6. The response flags "You'll be conversational in 3 months" as an unsupported claim and the 8-second "Building your plan…" as fake processing, and recommends removing or replacing both.
7. The fixes are given in a priority order with a reason for the order, separating what to fix immediately from what to test.
8. The response recommends the instrumentation that is missing: an assignment or entry event and per-step events, plus a check that the result is restored after signup.
9. The response offers at least two possible explanations for signup rising while activation fell, presented as hypotheses to check and not as established causes.

---

## What the cases do not cover

- **Implement mode.** No case builds the flow in a real app. Test it against a real project
  and use the verification list in `references/signup-handoff.md`.
- **Working from a repo.** Every case supplies a written brief. Step 1's code inspection is
  not exercised.
- **Whether a designed flow converts.** Only the app's own experiment answers that.
- **Unmarked assumptions and internal consistency.** No criterion checks that inferred product
  facts are marked where the argument relies on them, that counts and cross-references agree,
  or that cited sources can be identified. Graders found small lapses of each kind in
  responses that passed every criterion. Read a response for these by hand.
- **The interim decision in an audit** (split, revert or leave while fixes are built). A
  response could omit it and still pass.
