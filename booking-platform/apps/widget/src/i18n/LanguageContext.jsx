import { createContext, useContext, useMemo, useState, useEffect } from 'react';
import en from './translations_en';
import he from './translations_he';

const DICTS = { en, he };
const RTL_LANGS = new Set(['he']);

const LanguageContext = createContext(null);

/**
 * @param {{ initialLanguage?: 'en'|'he', rootEl?: HTMLElement, children: any }} props
 * rootEl receives dir="rtl"/"ltr" so the widget mirrors correctly whether
 * it's mounted standalone (document) or inside a shadow root.
 */
export function LanguageProvider({ initialLanguage = 'en', rootEl, children }) {
  const [lang, setLang] = useState(DICTS[initialLanguage] ? initialLanguage : 'en');

  useEffect(() => {
    const dir = RTL_LANGS.has(lang) ? 'rtl' : 'ltr';
    if (rootEl) {
      rootEl.setAttribute('dir', dir);
      rootEl.setAttribute('lang', lang);
    } else if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('dir', dir);
      document.documentElement.setAttribute('lang', lang);
    }
  }, [lang, rootEl]);

  const value = useMemo(() => ({ lang, setLang, isRtl: RTL_LANGS.has(lang) }), [lang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLang must be used within a LanguageProvider');
  return ctx;
}

function getPath(obj, path) {
  return path.split('.').reduce((acc, key) => (acc == null ? acc : acc[key]), obj);
}

function interpolate(str, vars) {
  if (!vars) return str;
  return str.replace(/\{\{(\w+)\}\}/g, (_, key) => (key in vars ? String(vars[key]) : `{{${key}}}`));
}

/**
 * Translation hook, mirroring talentflow's useT() pattern: components
 * re-render on language change. Usage: const t = useT(); t('service.title')
 * or t('service.duration', { minutes: 30 }).
 */
export default function useT() {
  const { lang } = useLang();
  const dict = DICTS[lang] || DICTS.en;
  return (key, vars) => {
    const raw = getPath(dict, key) ?? getPath(DICTS.en, key) ?? key;
    return interpolate(raw, vars);
  };
}
