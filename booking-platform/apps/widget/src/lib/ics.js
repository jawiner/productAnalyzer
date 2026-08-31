// Generates a downloadable/openable .ics file as a data URI for the
// "Add to calendar" action on the confirmation screen. This is a single
// customer-facing action triggered by an explicit click (an <a> tag with
// a data: href), not a build artifact, so no special download handling is
// needed beyond a plain anchor.
function toIcsDate(iso) {
  // .ics wants UTC basic format: YYYYMMDDTHHMMSSZ
  return new Date(iso).toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
}

function escapeIcsText(str = '') {
  return String(str).replace(/([,;])/g, '\\$1').replace(/\n/g, '\\n');
}

export function buildIcsDataUri({ businessName, serviceName, employeeName, startsAt, endsAt, confirmationCode, address }) {
  const summary = escapeIcsText(`${serviceName} — ${businessName}`);
  const description = escapeIcsText(
    [employeeName ? `With: ${employeeName}` : null, `Confirmation code: ${confirmationCode}`].filter(Boolean).join('\\n')
  );
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Booking Platform//Widget//EN',
    'CALSCALE:GREGORIAN',
    'BEGIN:VEVENT',
    `UID:${confirmationCode}@booking-platform`,
    `DTSTAMP:${toIcsDate(new Date().toISOString())}`,
    `DTSTART:${toIcsDate(startsAt)}`,
    `DTEND:${toIcsDate(endsAt)}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${description}`,
    address ? `LOCATION:${escapeIcsText(address)}` : null,
    'END:VEVENT',
    'END:VCALENDAR',
  ].filter(Boolean);

  const ics = lines.join('\r\n');
  return `data:text/calendar;charset=utf-8,${encodeURIComponent(ics)}`;
}
