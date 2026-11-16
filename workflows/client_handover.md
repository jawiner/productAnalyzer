# Client hand-over (a client leaves a Mashtech monthly plan)

## Objective

Give a leaving client everything that is theirs, the domain, their content and the site files, in one
package they can take to any host, then switch off what ran through Mashtech without the site going dark.
This is the promise in the "תנאי המנוי" block on mashtech.co.il, so it has to be quick and reliable.

## The terms this follows (as published on the site)

- Minimum term: 3 months on Starter and Professional, 6 months on Premium.
- After that the client stops with a WhatsApp or email; the plan ends at the end of the month already
  paid for, with no further charge.
- The domain is registered in the client's name and account (it always has been), so nothing to transfer.
- On leaving they get all the site files and content.
- Premium: online booking, online payment, missed-call SMS and review collection end with the plan.
- Price changes: 30 days' notice, and they can stop before the new price applies.

## Inputs

- The site folder under `websites/` (or wherever it lives).
- Client name (for the documents), first name of the contact (for the message), domain, plan.

## Steps

1. **Confirm the end date** with the client: the end of the paid month, and after the minimum term.
2. **Build the package:**
   ```
   python tools/client_handover.py websites/<site> --client "<business name>" --contact "<first name>" \
       --domain <domain> --plan <starter|professional|premium>
   ```
   Output: `.tmp/handover/<site>-<date>/`
   - `handover-<site>-<date>.zip`: what the client gets (website.zip, source.zip, README.txt in Hebrew and English)
   - `owner-checklist.md`: your steps, with notes and warnings from the build
   - `message-to-client.txt`: the WhatsApp/email text to send with it
   - `build.log`: only for sites with a build step
3. **Look before sending:** unzip website.zip, run `python -m http.server` inside it, open the pages.
4. **Send** the zip and the message. Ask the client to tell you once their new host is live.
5. **Only after their domain answers from the new host,** work through `owner-checklist.md`:
   Vercel domain + project, Intake Studio access, booking business, Premium services, billing, LeadFlow.
   Removing the domain from Vercel earlier takes the site offline.

## What the tool handles for you

- **Source = the last commit** (what is live). Uncommitted changes are reported, not shipped. A folder
  that isn't in git is copied as it is (with a warning).
- **Never ships secrets:** `.env*` files are left out (and removed if someone committed one), and every
  file is scanned. A real secret stops the run and names the file, never the value. Supabase anon keys
  are fine (they are public by design); a service-role key stops it.
- **Intake Studio edits are frozen in.** The client's published texts, photos and videos live in the
  Intake Studio database, not in the site files. The tool downloads them into `cms-content.json` and
  `cms-media/`, and replaces the loader with a frozen local copy that reads those files and calls nothing
  outside. With nothing published, it just removes the loader. Tested 2026-11-16 on El Nof with a test
  edit: the delivered site showed the edited paragraph and photo with no request to Intake Studio.
- **Builds Vite sites** in a temp copy (`npm ci` + `npm run build`, output dir from `vercel.json` or `dist`).
  The build runs without `.env`; if the code reads settings, the checklist lists their names.
- **Spots the booking widget and Mashtech services**, and tells the client in README.txt what stops working.

## Edge cases

- **"no index.html at the top":** the last commit isn't the live site (often the real page is uncommitted).
  Commit the site, then run again.
- **Build fails:** read `build.log`. Common cause: a setting the build needs. Never put secrets in the
  package to make it build; tell the client's developer the setting names instead.
- **Next.js app** (e.g. a site with server code): no website.zip; README tells them to import the source
  into their own Vercel account.
- **Client wants the GitHub repo:** transfer the repo to their GitHub account (repo Settings → Transfer).
  Do it after the secret scan passes and after checking the history has no secrets (`git log -p | grep`).
- **Client wants to stay on Vercel:** an alternative is transferring the Vercel project to their account.
  Check Vercel's current rules for transfers between accounts before offering it.
- **Live site differs from the last commit:** the package follows the last commit. If you deploy from a
  branch, check out what production runs before building the package.

## Booking data

The booking platform (saas/booking-platform, Supabase) keeps each client's appointments and customers.
If the client asks for their history, Claude runs this read-only export on the booking platform's
database (per the "run SQL myself" rule), saves it as CSV and adds it to the package:

```sql
select a.starts_at, a.ends_at, a.status, s.name as service,
       c.full_name, c.phone, c.email, a.notes
from appointments a
left join customers c on c.id = a.customer_id
left join services s on s.id = a.service_id
where a.business_id = '<BUSINESS_ID>'
order by a.starts_at;
```

Then switch the business off so the widget stops taking bookings (it only books for `trial`/`active`):

```sql
update businesses set status = 'cancelled' where id = '<BUSINESS_ID>';
```

This changes no customer data. Deleting the client's data is a separate decision: ask the user first.
The business id is in the site's `booking/config.js` (`businessId`).

## Lessons

- 2026-11-16: built and tested on El Nof (Vite + prerender, Intake Studio connected), Tnufa (static,
  booking widget, not in git) and Art Rock Dental (stopped correctly: its last commit has no index.html).
