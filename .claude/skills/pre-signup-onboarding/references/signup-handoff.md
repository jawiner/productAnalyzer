# Signup handoff and implementation

Use in Step 5 and throughout Implement mode. Stack-neutral: the patterns apply to any web or
mobile app; the provider names are examples only. Data-handling rules are [R: 15]; the
engineering patterns are practice, to be verified in the app.

## Contents

1. Ground rules
2. The draft
3. Where the draft lives
4. Surviving authentication
5. Attaching the draft to the account
6. Existing accounts (and 6a. Flows with no questionnaire: saved work, invites)
7. Expiry and fallbacks
8. Failure matrix
9. Data hygiene
10. Build order
11. Verification

## 1. Ground rules

- **Use what the app has.** Its auth provider, its signup components, its design tokens, its
  router, its analytics wrapper. A second auth path or a new visual language for the quiz is a
  maintenance cost and a trust break.
- **The host project's instructions win.** Follow its own conventions, review rules and
  release process over anything here.
- **The mapping is code someone can read.** Rules or a decision table in one module, with
  tests, used by both the pre-signup result and the first signed-in screen.
- **Every path ends somewhere usable.** There is no state in which the person sees an error
  and has lost their answers with no way forward.

## 2. The draft

The draft is the anonymous record of the flow so far.

| Field | Why |
| --- | --- |
| `draft_id` | Random, unguessable. The key for attaching it once. |
| `schema_version` | The quiz will change. An old draft must be recognized and handled. |
| `answers` | Keyed by question ID, storing option IDs (not display text) |
| `skipped` | Which questions were skipped, so fallbacks are deliberate |
| `result` | The computed result, or enough to recompute it |
| `current_step` | To restore position after refresh |
| `variant` | The experiment arm, so assignment stays stable |
| `created_at`, `updated_at` | For expiry |

Recompute the result from the answers when the mapping version matches; store the computed
result when it involved generation or anything not repeatable.

## 3. Where the draft lives

| Option | Good for | Limits |
| --- | --- | --- |
| Browser storage on a web page | Most web flows. Survives refresh and an OAuth round trip in the same browser. | Lost in another browser or device, in some private modes, and when the email link opens elsewhere. Any script running on the page can read it, including third-party analytics and ad scripts. |
| Private app storage on a phone (the app's own sandbox, or the OS's encrypted store) | Mobile apps, including sensitive answers | Lost on reinstall or another device. Other apps can't read it, and nothing leaves the device before the person has an account or has consented. |
| Server-side draft, referenced by an opaque ID in a cookie or client storage | Cross-device confirmation, long expiry, sensitive answers on a web page that carries third-party scripts | Needs an endpoint, rate limits, cleanup and an expiry job. It sends answers to a server before there is an account, which needs its own justification for sensitive data. The ID alone must reveal nothing. |
| Provider anonymous session upgraded to a real account | Apps whose auth provider supports anonymous users and linking | Provider-specific. Read the provider's docs for how linking and data ownership work, and for what happens when the person signs in to an existing account instead. |

Choose by asking who else could read the draft where it sits, then whether authentication can
finish in another browser or on another device. For sensitive answers the usual order of
preference is: private app storage, then a server-side draft, then browser storage only on
pages free of third-party scripts. Session-only storage (cleared when the tab closes) is too
fragile when the auth step can open a new tab.

How a given provider behaves (in-page signup or redirect, code or link confirmation, anonymous
sessions) comes from that provider's documentation. Until checked, write it in the spec as an
assumption.

## 4. Surviving authentication

- **Back navigation and refresh.** Restore `current_step` and selections from the draft on
  load. Write the draft on every answer, not at the end.
- **OAuth round trip.** The person leaves for the provider and returns to a callback. The
  draft waits in storage. Do not pass answers through the redirect URL or the OAuth `state`
  value. If the return destination needs to be remembered, store "return to result" as a flag
  or a path with no answer data in it.
- **Cancelled or failed auth.** Return to the account prompt with the result intact and a
  plain message. Retrying must not create a second draft.
- **Email confirmation or magic link.** The link may open in another browser or on another
  device, where a client-side draft doesn't exist. Either keep the draft server-side and
  attach it by an ID carried through the provider's own redirect mechanism (the ID, never the
  answers), or accept the gap and show the general start with a short way to redo the
  questions. Decide which, and write it in the spec.
- **In-app browsers.** Someone who taps an ad inside a social app usually lands in that app's
  built-in browser. An email link then opens in the phone's default browser, so for ad
  traffic "another browser" is the normal case, not the edge case. Some sign-in providers
  also refuse to run inside embedded browsers. Check both with the app's real traffic
  sources before choosing where the draft lives, and prefer a method that finishes in the
  same browser (a typed code instead of a link, where the provider offers one).
- **Password signup with errors.** Validation errors keep the person on the form with the
  draft untouched.
- **A paywall or permission step after signup.** The result is attached before that step, so
  it is waiting whatever the person chooses.

## 5. Attaching the draft to the account

Do it once, after authentication succeeds, in one place.

1. On the first authenticated load, look for a draft.
2. Send it to an endpoint that writes the result to the account and records the `draft_id` as
   claimed. Make the write idempotent: a unique constraint on `draft_id`, or an upsert keyed
   by it, so a second call does nothing and returns the same result.
3. Only after the server confirms, clear the local draft.
4. Navigate to the saved result or its first action.
5. Record `draft_restored` (success or failure, no answer content).

Guard against: the callback firing twice, two tabs, a retry after a timeout, and auth state
listeners that run on every token refresh. The idempotent write is what makes all of these
harmless.

## 6. Existing accounts

A person may finish the quiz and then sign in to an account that already has data.

- Never overwrite existing data with the draft silently.
- Never discard the draft silently either.
- Default: sign them in to what they have, and offer the new result as an addition ("Add this
  routine to your account?") with a clear way to decline.
- If the app has no place for a second result, say what happened: "You already have a plan.
  We've kept it. See the new suggestion?"

Also handle the reverse: a person who chooses "sign up" with an email that already exists
should be routed to sign-in with the draft still intact.

## 6a. Flows with no questionnaire

The same handoff exists when nothing was asked. What has to survive is different.

**Immediate use: the person's work.** They made something before the account prompt (a
compressed file, a document, a design), and "save this" is the promise.

- Decide where the work waits during signup: on the device (the browser's database storage
  has size limits and can be cleared), or uploaded first (which stores a stranger's file
  before there is an account, and needs a short expiry and a deletion path).
- Treat the work as potentially personal whatever the tool is for. Images and documents
  often are.
- Attach it once, by the same idempotent rule as a draft.
- If the work can't be kept (too large, storage blocked, expired), say so before the person
  leaves for signup, and make redoing it cheap. Never let "Save my file" lead to an account
  with no file in it.

**Invites and identity first: the destination.** There is no draft. What must survive sign-in
is where the person was going and the invitation that lets them in.

| Event | Expected state |
| --- | --- |
| Invite link expired or already used | A page that says so and offers the way to get a new one. No generic error. |
| Signed in with a different address than the one invited | Say which address was invited, and offer to switch account or ask the inviter to re-send. Never attach the invite to the wrong identity silently. |
| Invite forwarded to someone else | Same as above: the invite binds to the invited identity. |
| Single sign-on cancelled or failed | Back to the sign-in screen with the destination kept and a plain message. |
| Organization requires a sign-in method the person hasn't been set up for | Say who can fix it (their admin), not just that it failed. |
| Already a member | Go straight to the destination. |
| Invite accepted twice (double click, two tabs) | One membership. |
| The email said "3 waiting" and the number has changed | Show the current state and say so if it's now zero. |
| Sign-in succeeds | Land on the thing the invite named, not a general home screen. |

Keep the return path as a path or an ID with no private content in it. A security owner
should review invite links (lifetime, single use, binding to identity) and any sample or
sandbox data shown before sign-in, to be sure it is isolated from real data.

## 7. Expiry and fallbacks

- Set an expiry that fits the data: short for sensitive answers, longer for harmless ones.
  Write the number in the spec with the reason.
- On load with an expired or unreadable draft, or one from an old `schema_version` that can't
  be migrated: discard it and start the person at the entry screen or a general start. Tell
  them only if they would otherwise be confused.
- If the mapping can't produce a result (a combination nobody planned for, a failed
  generation call), show the general start. Log the case without answer content.
- Server-side drafts need a cleanup job and a deletion path.

## 8. Failure matrix

Fill this in for the app, and test every row.

| Event | Expected state |
| --- | --- |
| Back from question 3 to question 2 | Question 2 shows the earlier selection |
| Change question 1 after answering 3 | Dependent answers cleared and re-asked; others kept |
| Refresh on any step | Same step, same selections |
| Refresh on the result | Same result |
| Close the tab, return within expiry | Offer to continue or start again |
| Return after expiry | Entry screen or general start, no error |
| Skip a question | The defined fallback, result still works |
| Skip the whole quiz | General start; account prompt still truthful |
| OAuth cancelled | Account prompt, result intact, plain message |
| OAuth succeeds | Draft attached once, saved result opens |
| Callback fires twice, or two tabs | One saved result |
| Network fails during attach | Draft kept locally, retry offered, no duplicate after retry |
| Email link opened in another browser or on another device | The behavior chosen in section 4 |
| Sign-in to an existing account | Existing data untouched, new result offered |
| Signup with an email that already exists | Routed to sign-in, draft intact |
| Quiz changed since the draft was made | Migrated, or discarded with a general start |
| Storage unavailable (private mode, blocked) | Flow still completes in memory; the person is warned before leaving the page for auth |

## 9. Data hygiene

- **URLs.** Step IDs are fine in the URL. Answers are not: URLs end up in browser history,
  referrer headers, server logs and shared screenshots.
- **Analytics.** Events carry the step ID, the variant, and whether the step was completed or
  skipped. Raw answers to sensitive questions never go in. For harmless questions, send option
  IDs only if someone has a named use for them.
- **Ad pixels and session recorders.** Check what they capture on quiz pages. Recorders often
  capture on-screen text and inputs; mask or exclude sensitive screens.
- **Logs and error reports.** Strip answer content from request logs and error payloads.
- **Mobile apps.** The same leaks have different names: automatically tracked screen names
  that include an answer, analytics user-profile properties set from answers, crash reports
  that capture state, and reminder text shown on the lock screen ("Time for your panic
  exercise"). Analytics and ad tools often start collecting at launch, before any consent
  prompt; check when each one starts.
- **Free text.** Never in analytics, URLs or logs, whatever the question was. It may sit in
  the draft with the other answers.
- **Purpose, retention, deletion.** Written down before collection, and reflected in the
  privacy notice.
- **Minimum.** Store what the result and the account need, and nothing kept "in case".

## 10. Build order

1. The mapping module and its tests, including every fallback row.
2. The draft store, with read, write, expiry and versioning.
3. The question screens, using the app's own components, with back, skip and restore.
4. The result screen with editing.
5. The account prompt, wrapping the app's existing signup.
6. The attach step and the first signed-in screen.
7. Events, checked against the event map in [measurement.md](measurement.md).
8. The experiment switch, so the baseline entry still exists and assignment is stable.

## 11. Verification

Run the flow. Reading the code doesn't show a lost draft.

- [ ] Two different answer sets end on visibly different results, and both survive signup.
- [ ] Every row of the failure matrix behaves as written.
- [ ] Each auth method the app offers completes the handoff.
- [ ] The first signed-in screen shows the saved result without asking anything again.
- [ ] A repeated attach creates no duplicate.
- [ ] The flow works on a small phone viewport and by keyboard alone, and a screen reader
      announces each step.
- [ ] No answer content in URLs, analytics payloads, pixel calls or logs (inspect the network
      requests, don't assume).
- [ ] Events fire once each, in order, with the variant attached.
- [ ] The baseline entry still works for people not assigned to the new flow.
- [ ] Nothing on any screen breaks the honesty rules in SKILL.md.

Report what was verified, how, and what could not be checked in this environment.
