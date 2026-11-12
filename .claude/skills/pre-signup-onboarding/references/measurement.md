# Measurement and experiments

Use in Step 6 and in any audit that involves numbers. The method is [R: 18, 19]. Which variant
wins is always [H] until the app's own test says. Sources: [research.md](research.md).

## Contents

1. Definitions to fix first
2. Metrics
3. Why the denominator matters
4. Event map
5. Experiment setup
6. Reading results
7. Signup up, activation down
8. What to test, in order
9. Low traffic
10. Auditing someone else's numbers

## 1. Definitions to fix first

Write these down before building or reading anything:

- **Eligible entrant.** Who counts as having entered: for example, a new, signed-out visitor
  who loads the entry point. Define it once and use it for every variant.
- **Baseline.** The current entry flow, described step by step, kept running as the control.
- **Activation event.** The first core action that shows the person received value: a first
  routine completed, a first document summarized, a first invoice approved. A meaningful
  action, not "opened the dashboard".
- **Window.** How long after entry the activation event counts, chosen from normal usage. A
  daily-use product might use 7 days. A monthly-use product needs longer. If an answer can
  change how soon the activation event is possible (a weekly mode in a daily app), the window
  has to fit the slowest path the flow can produce, and results are also read by path.

Three situations the definitions above don't cover:

- **Nothing is tracked yet.** Instrument the current flow first and let it run. Without a
  baseline rate there is nothing to compute a sample size from, and inventing one is a
  prediction in disguise.
- **There is no current flow** (a new app). The baseline is the simplest honest entry: a
  general start, immediate use, or plain signup, whichever the app would otherwise ship.
- **The unit isn't one person.** In a team product, colleagues talk and share a workspace.
  Assign by company or workspace, count entrants at that level too, and say which unit each
  metric uses. A second business objective (sales pipeline, demo requests) is a secondary
  metric or a guardrail, with its own per-entrant definition.

## 2. Metrics

| Role | Metric | Definition |
| --- | --- | --- |
| **Primary** | Activation per entrant | Entrants who complete the activation event within the window ÷ all eligible entrants assigned to the flow |
| Secondary | Signup per entrant | Accounts created ÷ all eligible entrants assigned |
| Diagnostic | Quiz take-up | Entrants who start the quiz ÷ entrants offered it |
| Diagnostic | Quiz completion | Entrants who reach the result ÷ entrants who start |
| Diagnostic | Step drop-off | For each step, those who leave ÷ those who view it |
| Diagnostic | Result edits | How often people change the result (possible mismatch) |
| Diagnostic | Draft restored | Signups whose result was attached ÷ signups that had a draft |
| Diagnostic | Time to value | Time from entry to the activation event |
| Guardrail | Retention | Return or repeat use in a later period |
| Guardrail | For paid apps | Trial start, paid conversion, refunds, cancellations |
| Guardrail | Friction and trust | Support contacts, complaints, unsubscribes, notification opt-outs |
| Guardrail | Technical | Page load, error rate on the new screens |

Choose guardrails by asking what a "win" could quietly damage in this business.

**When the core action needs no account** (immediate use), changing where the account prompt
sits can barely move first-core-action per entrant. Lead with the outcome the change is meant
to move: entrants who get value from an account feature within the window (a saved item
reopened, a batch run, history used) ÷ all eligible entrants. Keep first core action per
entrant as a guardrail that must not fall. An account created and never used again is not
the outcome.

## 3. Why the denominator matters

A hypothetical example. Of 1,000 eligible entrants:

| | Accounts | Activated | Signup per entrant | Activation per entrant |
| --- | --- | --- | --- | --- |
| Existing flow | 300 | 150 | 30% | 15% |
| Quiz | 340 | 120 | 34% | 12% |

Signup improves from 30% to 34%. Activation falls from 15% to 12%. Under an activation
objective the quiz loses.

Three rates get confused. Keep them apart:

- **Signup per entrant** (accounts ÷ entrants): how many people the entry converted.
- **Activation per signup** (activated ÷ accounts): how many of the converted got value.
- **Activation per entrant** (activated ÷ entrants): the product of the two, and the primary.

Activation per signup can fall while the flow still wins. If signup goes from 30% to 40% and
activation per signup from 50% to 45%, activation per entrant goes from 15% to 18%: more
people got value. So always multiply through to the per-entrant figure before judging.

## 4. Event map

| Stage | Events | Diagnoses |
| --- | --- | --- |
| Entry | `experience_assigned`, `quiz_started`, `quiz_skipped` | Reach, take-up, self-selection |
| Questions | `step_viewed`, `step_completed`, `step_skipped` | Exits, effort, difficult branches |
| Result | `result_viewed`, `result_edited` | Reach, possible mismatch |
| Account | `signup_started`, `signup_completed`, `draft_restored` | Auth and handoff friction |
| Product value | `first_core_action_completed` | Activation, time to value |

Rename to the app's conventions. For each event specify:

- **Properties:** variant ID, step ID, anonymous ID, and after signup the account ID. No raw
  answers to sensitive questions. Minimize personal information throughout. If an option ID
  is sent for a harmless question, write down who uses it and for what.
- **Fires once** per person per step (deduplicated), including after refresh and back.
- **Identity link:** the anonymous ID is tied to the account ID at signup, so pre-signup
  events and the activation event join up. Check this link works before trusting anything.
- **Baseline too:** the control arm fires `experience_assigned`, `signup_started`,
  `signup_completed` and the activation event, or the comparison is impossible.

## 5. Experiment setup

1. **Randomize before the first variant screen.** Assignment happens when the eligible
   entrant arrives, before they see anything that differs.
2. **Keep assignment stable.** The same person sees the same variant on return. Store the
   variant with the draft and then with the account.
3. **Compare everyone assigned.** People who skip the quiz or leave on the first question stay
   in the quiz arm's denominator. Comparing only quiz completers with the baseline measures
   who chose to finish, not what the quiz did.
4. **Hold the promise constant.** Same traffic sources and the same acquisition message in
   both arms within one comparison.
5. **Decide before looking:** the primary metric, the guardrails and how much harm is
   tolerable, the smallest effect worth acting on, the sample size (or a valid sequential
   rule), and the observation window.
6. **Validate the plumbing:** events deduplicated, identity link working, arms balanced.
7. **Check sample ratio first.** If a 50/50 split arrives as something clearly different,
   find out why before reading any outcome. A mismatch usually means assignment or logging is
   broken, and the outcome numbers can't be trusted [R: 19].
8. **Segment afterward, with care.** Look at new versus returning visitors and at traffic
   sources. Treat segment differences as leads for the next test.

## 6. Reading results

| Signup per entrant | Activation per entrant | Reading |
| --- | --- | --- |
| Up | Up | The flow helped. Check the guardrails, then keep it and test the next uncertainty. |
| Up | Flat | More accounts, no more value. The flow added signups that don't activate. Look at the handoff and the result's usefulness. |
| Up | Down | The flow lost under an activation objective. See section 7. |
| Down | Up | Fewer, better-matched signups. A win on the primary; confirm retention and that volume still meets the business need. |
| Down | Down | The flow lost. Use step drop-off to see where. |
| Flat | Flat | No detectable effect at this sample. Simpler is better: keep the baseline or the shorter flow. |

A result is a result for this app, this traffic and this version of the flow.

## 7. Signup up, activation down

Do not report this as a win. State the per-entrant activation figures side by side with the
signup figures, and say which objective the business set.

Then diagnose. Each cause is a hypothesis [H] with something to check:

| Possible cause | What to check |
| --- | --- |
| The questions carried lower-intent people into signup | Activation per signup for quiz completers versus quiz skippers; time to first action |
| The result promised more than the product delivers | The result's claims against the first session; early exits right after signup |
| The handoff dropped the answers | `draft_restored` rate; whether the first signed-in screen shows the result; whether anything is asked twice |
| The account prompt came before any real value | Whether the result is visible and usable before signup |
| A step after signup (confirmation, paywall, permissions) lost them | Drop-off between `signup_completed` and the first core action |
| The comparison itself is unsound | Whether assignment was random, traffic mix was the same, and the periods are comparable |

**What dilution can and can't explain.** Extra low-intent signups lower activation per
signup, but they cannot lower activation per entrant: the people who would have activated
anyway are still there. So if activation per entrant fell, the flow is losing some of those
people (or the comparison is unsound). A quick check from rates alone: old activation per
entrant ÷ new signup per entrant is the lowest activation per signup that pure dilution
could produce. An observed figure below that floor means something more than dilution.

Next step: fix what is broken or dishonest without a test, then rerun the comparison per
eligible entrant with random assignment.

**What to run in the meantime.** When a flow is already live for everyone and the
per-entrant figure looks worse, there are three options, and the choice is the owner's:

- **Split now.** Send a random half to the old entry and half to the current flow. It limits
  the possible harm and starts producing a sound comparison. Usually the best option when
  the old entry can be switched back on.
- **Revert.** Go back to the old entry until the repaired flow is ready. Defensible when the
  flow contains dishonest elements or the handoff is broken, and those can't be fixed quickly.
- **Leave it.** Only when the evidence of harm is weak and the fixes ship within days.

Whichever is chosen, the dishonest elements come out at once. They don't wait for the test.

## 8. What to test, in order

1. **The package.** Current entry versus a short, optional, truly personalized quiz. This
   answers whether the approach helps at all.
2. **If it wins, one uncertainty at a time:** fewer questions, an earlier result, different
   account timing, an intermediate insight, the progress indicator.
3. Keep the acquisition promise the same within each comparison.

Testing details before the package is known to help spends traffic on the wrong question.

One change per arm. A proposal such as "quiz, then mandatory signup, then the tool" bundles
two changes: the questions, and an account wall in front of something that used to be open.
If the team wants to test it, the wall and the quiz are separate arms, or the result can't
say which one did what.

## 9. Low traffic

When the app can't reach a usable sample in a reasonable time:

- Run **moderated walkthroughs** with a handful of people from the target audience. Watch for
  confusion, misread options, surprise at the account prompt, and whether the result feels
  like it came from their answers.
- Do an **event audit**: walk every path yourself and confirm each event fires once and joins
  to the account.
- Read **step drop-off** as a pointer to where to look.
- Treat conversion differences from small cohorts as **directional**, and say so in the
  report. Do not quote a percentage difference as a finding.

## 10. Auditing someone else's numbers

- Rebuild every rate from counts, with the denominator named. Multiply signup per entrant by
  activation per signup to get activation per entrant when only those two are given.
- When only percentages are supplied, compute what they allow, say that the size of the
  noise can't be judged without the counts, and ask for them.
- Ask how the comparison was made. Before/after comparisons mix the change with everything
  else that moved in that time: traffic mix, season, campaigns, other releases.
- Check who was excluded. "Among people who completed the quiz" is a selected group.
- Check the window is the same on both sides, and long enough for the later cohort to have
  had its chance to activate.
- Check the events exist to answer the question. Without an assignment event and step events,
  the honest answer may be "this can't be known yet; here is what to instrument".
