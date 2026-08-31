const he = {
  common: {
    back: 'חזרה',
    next: 'הבא',
    loading: 'טוען…',
    retry: 'נסה שוב',
    cancel: 'ביטול',
    close: 'סגירה',
    submitting: 'שולח…',
    optional: 'אופציונלי',
  },

  errors: {
    generic: 'משהו השתבש. נסו שוב.',
    network: 'לא הצלחנו להתחבר לשרת. בדקו את החיבור ונסו שוב.',
    businessNotFound: 'עמוד ההזמנות הזה אינו זמין כרגע.',
    serviceUnavailable: 'ההזמנה אינה זמינה זמנית. נסו שוב בקרוב.',
    noSlots: 'אין שעות פנויות בתאריך זה. בחרו תאריך אחר.',
    conflict: 'השעה הזו נתפסה זה עתה על ידי מישהו אחר. אנא בחרו שעה אחרת.',
  },

  steps: {
    service: 'שירות',
    employee: 'נותן שירות',
    date: 'תאריך',
    time: 'שעה',
    details: 'הפרטים שלך',
    confirm: 'אישור',
  },

  service: {
    title: 'בחרו שירות',
    subtitle: 'בחרו את השירות שברצונכם להזמין',
    duration: '{{minutes}} דקות',
    noServices: 'אין כרגע שירותים זמינים.',
  },

  employee: {
    title: 'בחרו נותן שירות',
    subtitle: 'עם מי תרצו לקבוע תור?',
    any: 'אין העדפה',
  },

  date: {
    title: 'בחרו תאריך',
    subtitle: 'בחרו יום שמתאים לכם',
  },

  time: {
    title: 'בחרו שעה',
    subtitle: 'שעות פנויות בתאריך {{date}}',
    noSlots: 'אין שעות פנויות בתאריך זה.',
    pickAnotherDate: 'בחרו תאריך אחר',
  },

  details: {
    title: 'הפרטים שלך',
    subtitle: 'כמעט סיימנו — איך נוכל ליצור איתכם קשר?',
    fullName: 'שם מלא',
    fullNamePlaceholder: 'ישראל ישראלי',
    phone: 'מספר טלפון',
    phonePlaceholder: '050-000-0000',
    email: 'אימייל',
    emailPlaceholder: 'israel@example.com',
    notes: 'הערות',
    notesPlaceholder: 'משהו שכדאי שנדע?',
    submit: 'אישור ההזמנה',
    errors: {
      fullNameRequired: 'אנא הזינו שם מלא',
      phoneRequired: 'אנא הזינו מספר טלפון תקין',
      emailInvalid: 'אנא הזינו כתובת אימייל תקינה',
    },
  },

  confirmation: {
    title: 'ההזמנה אושרה',
    subtitle: 'אישור נשלח אליכם.',
    business: 'עסק',
    service: 'שירות',
    employee: 'נותן שירות',
    when: 'מועד',
    customer: 'שם',
    code: 'קוד אישור',
    addToCalendar: 'הוספה ליומן',
    cancelBooking: 'ביטול הזמנה',
    rescheduleBooking: 'שינוי מועד',
    bookAnother: 'קביעת תור נוסף',
  },

  manage: {
    title: 'ניהול ההזמנה שלך',
    subtitle: 'הזינו את קוד האישור כדי לאתר את ההזמנה',
    codeLabel: 'קוד אישור',
    codePlaceholder: 'ABC12345',
    lookup: 'איתור הזמנה',
    notFound: 'לא מצאנו הזמנה עם הקוד הזה.',
    alreadyCancelled: 'הזמנה זו כבר בוטלה.',
    cancelConfirmTitle: 'לבטל את ההזמנה?',
    cancelConfirmBody: 'לא ניתן לבטל פעולה זו. ייתכן שתצטרכו להזמין מחדש אם תשנו את דעתכם.',
    cancelReason: 'סיבה (אופציונלי)',
    cancelSubmit: 'ביטול ההזמנה',
    cancelSuccess: 'ההזמנה שלכם בוטלה.',
    cancelNotAllowed: 'עסק זה אינו מאפשר ביטול עצמאי. אנא צרו קשר ישירות עם העסק.',
    rescheduleTitle: 'בחרו מועד חדש',
    rescheduleSubmit: 'אישור המועד החדש',
    rescheduleSuccess: 'מועד ההזמנה שונה בהצלחה.',
    rescheduleNotAllowed: 'עסק זה אינו מאפשר שינוי מועד עצמאי. אנא צרו קשר ישירות עם העסק.',
    tooCloseToCancel: 'קרוב מדי למועד התור לשינוי מקוון. אנא צרו קשר ישירות עם העסק.',
  },
};

export default he;
