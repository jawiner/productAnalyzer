---
tags: [pre-signup-onboarding]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

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
