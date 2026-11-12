---
tags: [pre-signup-onboarding]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Signoff is our B2B tool for approving supplier invoices. Invoices and approval chains live inside a company workspace. Stack: Rails, Devise with Google Workspace and Microsoft sign-in, SAML for bigger customers.

Two kinds of people show up for the first time:
1. Invited approvers. Their finance admin adds them, and they get an email: "You have 3 invoices waiting for approval." They click through.
2. Finance leads evaluating us from the website. They can start a self-serve trial with a work email or request a demo.

Nothing real can be shown without the workspace, since it's the company's financial data. Each role gets a different home screen: approvers see their queue, AP clerks see invoice intake, finance admins see chains and reports. We also have a sandbox company with fake invoices that we use in sales demos.

Activation: for an approver, the first invoice approved or rejected. For a finance admin, the first approval chain created.

Sales wants a 7-question qualification quiz in front of both the invite link and the trial signup (company size, annual invoice volume, ERP, budget, timeline, decision maker, phone number). Design the first-run experience.
