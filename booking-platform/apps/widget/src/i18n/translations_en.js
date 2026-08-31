const en = {
  common: {
    back: 'Back',
    next: 'Next',
    loading: 'Loading…',
    retry: 'Try again',
    cancel: 'Cancel',
    close: 'Close',
    submitting: 'Submitting…',
    optional: 'optional',
  },

  errors: {
    generic: 'Something went wrong. Please try again.',
    network: "We couldn't reach the server. Check your connection and try again.",
    businessNotFound: 'This booking page is not available right now.',
    serviceUnavailable: 'Booking is temporarily unavailable. Please try again shortly.',
    noSlots: 'No available times on this date. Please pick another date.',
    conflict: 'That time was just booked by someone else. Please choose another time.',
  },

  steps: {
    service: 'Service',
    employee: 'Provider',
    date: 'Date',
    time: 'Time',
    details: 'Your details',
    confirm: 'Confirmation',
  },

  service: {
    title: 'Choose a service',
    subtitle: 'Select the service you would like to book',
    duration: '{{minutes}} min',
    noServices: 'No services are currently available.',
  },

  employee: {
    title: 'Choose a provider',
    subtitle: 'Who would you like to book with?',
    any: 'No preference',
  },

  date: {
    title: 'Choose a date',
    subtitle: 'Pick a day that works for you',
  },

  time: {
    title: 'Choose a time',
    subtitle: 'Available times for {{date}}',
    noSlots: 'No available times on this date.',
    pickAnotherDate: 'Pick another date',
  },

  details: {
    title: 'Your details',
    subtitle: 'Almost done — how can we reach you?',
    fullName: 'Full name',
    fullNamePlaceholder: 'Jane Doe',
    phone: 'Phone number',
    phonePlaceholder: '050-000-0000',
    email: 'Email',
    emailPlaceholder: 'jane@example.com',
    notes: 'Notes',
    notesPlaceholder: 'Anything we should know?',
    submit: 'Confirm booking',
    errors: {
      fullNameRequired: 'Please enter your full name',
      phoneRequired: 'Please enter a valid phone number',
      emailInvalid: 'Please enter a valid email address',
    },
  },

  confirmation: {
    title: 'Booking confirmed',
    subtitle: 'A confirmation has been sent to you.',
    business: 'Business',
    service: 'Service',
    employee: 'Provider',
    when: 'When',
    customer: 'Name',
    code: 'Confirmation code',
    addToCalendar: 'Add to calendar',
    cancelBooking: 'Cancel booking',
    rescheduleBooking: 'Reschedule booking',
    bookAnother: 'Book another appointment',
  },

  manage: {
    title: 'Manage your booking',
    subtitle: 'Enter your confirmation code to look it up',
    codeLabel: 'Confirmation code',
    codePlaceholder: 'ABC12345',
    lookup: 'Look up booking',
    notFound: 'We could not find a booking with that code.',
    alreadyCancelled: 'This booking has already been cancelled.',
    cancelConfirmTitle: 'Cancel this booking?',
    cancelConfirmBody: 'This cannot be undone. You may need to book again if you change your mind.',
    cancelReason: 'Reason (optional)',
    cancelSubmit: 'Cancel booking',
    cancelSuccess: 'Your booking has been cancelled.',
    cancelNotAllowed: 'This business does not allow self-service cancellation. Please contact them directly.',
    rescheduleTitle: 'Pick a new time',
    rescheduleSubmit: 'Confirm new time',
    rescheduleSuccess: 'Your booking has been rescheduled.',
    rescheduleNotAllowed: 'This business does not allow self-service rescheduling. Please contact them directly.',
    tooCloseToCancel: 'Too close to the appointment time to change online. Please contact the business directly.',
  },
};

export default en;
