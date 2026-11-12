# Question design and answer mapping

Use in Step 3. Covers the question protocol, order, wording, options, skip behavior, sensitive
questions, and the table that turns answers into a result. Labels and sources:
[research.md](research.md).

## Contents

1. Start from the result
2. The question protocol
3. Order
4. Wording
5. Answer options
6. Skip, "not sure" and fallbacks
7. Sensitive questions
8. Answer-to-result mapping
9. The two-answer-set check
10. Question bank (starting points)
11. Questions to cut

## 1. Start from the result

List the parts of the result that can vary: which plan or template, how big the first step is,
when it happens, what it starts with, which screen opens. Each varying part is a slot. A
question exists to fill a slot. When every slot has a source (an answer or a default), stop
adding questions.

A slot does not have to be asked. If one value suits most people and the person can change it
on the result ("We've started you at 10 minutes"), fill the slot with an editable default and
record it in the mapping as "not asked".

How many questions is [H]. No source gives an ideal count. The honest starting point is the
fewest the result needs, and a test of that against one fewer. Removing a question that fills
no slot is different: that is a fix, made without a test [R: 1, 15].

## 2. The question protocol

Record this for every question before writing screens. Documenting why each answer is needed is
standard practice for form design [R: 1].

| Field | What to write |
| --- | --- |
| ID and wording | The exact text the person reads |
| Type | Single choice, multiple choice, number, short text |
| Options | The exact option labels, in display order |
| Purpose | Which slot of the result it fills |
| What each answer changes | One line per option: the concrete difference in the result |
| Who sees it | Everyone, or only a named branch |
| Optional? | Yes or no, and why |
| Skip or "not sure" | What the person gets instead, and that it still works |
| Data handling | Sensitivity, where it is stored, how long, whether any analytics event may carry it |

A question with an empty "what each answer changes" row is removed.

## 3. Order

Starting hypothesis [H]: **goal → the obstacle or constraint that matters → preference**. The
product may need only one of these.

- Open with something the person can answer confidently and that relates to why they came. An
  easy, relevant first answer supports the sense of competence [R: 5].
- Group related questions and keep the order coherent, so each question makes sense given the
  one before [R: 1, 2].
- Put sensitive questions later, after the person has seen why the flow is worth it [R: 4].
- When the goal question is itself the sensitive one (a mental-health or money app), the two
  rules above collide. Open with an easier question that still fills a slot (time, format),
  and word the goal as a choice among what the app offers ("What would you like to work on
  first?") instead of a description of the person ("What are you suffering from?"). [H]
- Ask a follow-up only on the branch where its answer can improve the result.
- Order changes answers [R: 4]. If an early question could color a later one, consider
  swapping them or testing both orders.

## 4. Wording

Wording changes answers [R: 4], and a wrong answer produces a wrong result that the person
then judges the product by.

- **Concrete over abstract.** "How many days did you practice last week?" is easier to answer
  truthfully than "Are you consistent?", if recent frequency is what the result needs.
- **One concept per question.** "How much time and energy do you have?" is two questions.
- **Neutral.** No option should read as the embarrassing one. "What usually gets in the way?"
  is better than "Why do you keep failing?".
- **The person's words.** Use language from interviews, reviews, support messages and search
  queries when you have it.
- **Answerable now.** Don't ask what people can't know ("How many hours will you save?").
- **No leading.** "How much do you want to transform your mornings?" presumes the answer.

## 5. Answer options

- **Distinct.** Two options that lead to the same result should be one option. A "not sure"
  option is the exception: it may land on the same result as a real option, as long as the
  result says a default was used.
- **Covering.** A person whose real answer is missing either leaves or picks at random. Check
  the options against real answers from customer language.
- **Count.** The effect of the number of options depends on context [R: 8]. Reduce when it
  makes the choice easier to understand; keep coverage when it matters.
- **Order.** Position can bias a choice [R: 4]. Use a natural order (time, size) where one
  exists. Where none does and the choice matters, consider rotating the order.
- **Single or multiple.** Say which. Multi-select needs a rule for how several picks combine,
  and an explicit Continue.
- **Catch-all options.** "Something else" needs somewhere to go: a text field so the person can
  say what they mean, and a stated general result. People type things nobody planned for, so
  typed text never goes into analytics, URLs or logs. It can stay in the draft like any other
  answer unless the question itself is sensitive.
- **Sensible defaults.** For size or time questions, an editable default beats a forced choice.

## 6. Skip, "not sure" and fallbacks

An opt-out is real only when what follows still works [R: 5].

- Every optional question has a visible, neutral skip ("Skip" or "Not sure yet"), styled as a
  normal choice. No guilt copy.
- Each skip has a defined fallback: a broadly useful general start, a default the person can
  edit, or a slot left for later ("add a reminder later").
- A whole-quiz skip leads to a usable general start, and the account prompt still tells the
  truth about what it saves. A general start is one specific suggestion the person can accept
  or change, never a bigger menu: someone who said "not sure" should not be handed the full
  catalogue to choose from. Write the first signed-in screen for this person too.
- The result says plainly when it used a default: "We've started you with 10 minutes. Change
  it any time."
- Required questions are rare. A question is required only when no sensible result exists
  without it, or the law requires the answer.

## 7. Sensitive questions

Health, mental state, money, relationships, identity, location, children, anything a person
might not want a stranger to know.

1. **Need.** Does any answer change a result the product can support? If not, remove it [R: 15].
2. **Explain in place.** One line next to the question saying why it is asked and what it
   changes: "We ask so we can leave out exercises that don't fit. It isn't shared." [R: 4, 15]
3. **Alternative.** A "prefer not to say" that leads to a working result.
4. **Late.** After easier questions [R: 4].
5. **Neutral wording.** No judgment in the question or the options [R: 4].
6. **Handling.** Purpose, storage, retention and deletion decided before collecting. The raw
   answer never goes into a URL, an analytics event, an ad pixel or a log [R: 15].
7. **Review.** Where an answer could affect health, finances or safety, or indicates risk to
   the person, a qualified owner reviews the question, the result it leads to, and what the
   product does if the answer signals danger. Flag it; don't decide it alone.
8. **Default while review is pending.** Leave the question out. A product should not ask
   something it has no reviewed response to: a person who discloses risk and gets a habit
   plan back has been failed. Design the flow so it works without the question, and note
   what the reviewer needs to decide (whether to ask, the wording, and what the person sees
   after each answer, such as how help is offered). [H, outside the source list]

Law on sensitive data, rules for ad and analytics tools in health or finance apps, age rules
and store policies are outside the source list. Name them as items for the lawyer or the
relevant owner to verify; don't state them as settled.

Being open about what is collected and why can affect how people respond to
personalization [R: 17, from advertising]. Whether the explanation line helps here is [H].

## 8. Answer-to-result mapping

Personalization has to be traceable: a person, a reviewer and a tester should all be able to
see why an answer set produced a result.

**Use explicit rules or a decision table where practical.** Example of a reviewable rule:
"goal = focus, available time = five minutes → five-minute focus routine."

| Goal | Obstacle | Time | Result |
| --- | --- | --- | --- |
| Focus | Hard to start | 5 min | 5-minute focus routine, first step: a 2-minute starter |
| Focus | Interruptions | 5 min | 5-minute focus routine, first step: clear interruptions |
| Focus | (skipped) | 5 min | 5-minute focus routine, standard first step |
| (skipped) | any | any | General starter routine, default 10 minutes, editable |

Slots filled by a default get a line under the table: "Reminder: not asked. Default: none.
Editable on the result."

Alongside the table, define:

- **Priority.** When two answers pull in different directions, which wins, and why.
- **Fallbacks.** The row for every skipped or "not sure" answer.
- **Invalidation.** Which later answers are cleared when an earlier one changes, and what the
  person is told.
- **Coverage.** Every reachable combination lands on a row. Count the combinations and check.
- **Capability check.** Every result is something the app delivers today.

**Where generated output is used** (a model writes the plan), keep a rule-based skeleton that
decides the substance, and let generation phrase it. Test that results are relevant and
consistent across runs, and that the output doesn't invent features or imply diagnostic
precision. Decide what is shown if generation fails or is slow: the rule-based result.

## 9. The two-answer-set check

Write two realistic people. Give each a name, a reason for arriving and a full answer set. Walk
each through the mapping and set the two results side by side:

| | Person A | Person B |
| --- | --- | --- |
| Answers | … | … |
| Result headline | … | … |
| First action | … | … |
| Why it fits (as shown to them) | … | … |

Pass: the first action, content, size or order differs, and each difference traces to an
answer. Fail: the only difference is the person's answer repeated in the headline. On a fail,
either the app can't vary enough (go back to Step 2) or the mapping ignores an answer (remove
that question).

## 10. Question bank (starting points)

Adapt the wording to the product and the person's language. Every one of these is [H] until the
"changes" column is true for the app in hand.

| Starting question | Decision it changes | Fallback |
| --- | --- | --- |
| What would you like to improve first? | Selects the first workflow or plan category | A useful general starting point |
| What usually gets in the way? | Selects a starting action that addresses the obstacle | A broadly feasible first step |
| How much time can you spend on a typical day? | Sets the size of the starting action | An editable default |
| When is it easiest to fit this in? | Attaches an optional cue to the plan | The person adds a cue later |
| What are you here to do today? | Routes to the matching tool or home screen | The most common path |
| Which best describes your role? | Selects the home screen and sample data | A general view with a role switch |
| What level are you starting from? | Sets the difficulty of the first activity | A short placement activity, or beginner |
| What are you working with? (file type, platform, tool) | Selects the import path or template | A guided chooser |

An if-then cue ("after breakfast, I'll…") is supported as plan content for people who already
intend to act [R: 6]. Offer it as optional.

## 11. Questions to cut

- **"How did you hear about us?"** Attribution belongs in analytics. It changes nothing for
  the person.
- **Demographics with no effect on the result** (age range, gender, company size), unless
  required by law or used by the mapping.
- **Commitment theater.** "How motivated are you, 1 to 10?" when nothing reads the answer.
- **Restated questions.** Two questions that fill the same slot.
- **Aspirations the product can't act on.** "When do you want to reach your goal?" when no
  plan changes with the date, especially if the result then implies the date is achievable.
- **Permission requests dressed as questions.** Notification or tracking prompts belong at the
  moment their benefit is concrete, with the system prompt explained first.

If the business needs one of these for a real purpose, give it a clear purpose statement and an
appropriate collection path: optional, after value, labelled, with its own data handling
[R: 1, 4, 15].

The "changes" test applies to anything that stands between the person and the product. A form
the person opens by choice is a different exchange: a "Talk to sales" or demo-request form may
ask qualifying questions, provided each field has a stated use by whoever acts on it, the form
is labelled for what it is, and the product stays reachable without it.
