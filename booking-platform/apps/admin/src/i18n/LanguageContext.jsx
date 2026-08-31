import { createContext, useContext, useMemo, useState, useEffect } from 'react';
import en from './translations_en';
import he from './translations_he';

const DICTS = { en, he };
const RTL_LANGS = new Set(['he']);
const STORAGE_KEY = 'admin_lang';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && DICTS[stored]) return stored;
    } catch {
      // ignore storage errors (private browsing etc.)
    }
    return 'en';
  });

  const setLang = (next) => {
    setLangState(DICTS[next] ? next : 'en');
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    const dir = RTL_LANGS.has(lang) ? 'rtl' : 'ltr';
    document.documentElement.setAttribute('dir', dir);
    document.documentElement.setAttribute('lang', lang);
  }, [lang]);

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

/** Usage: const t = useT(); t('nav.dashboard') or t('appt.count', { n: 3 }) */
export default function useT() {
  const { lang } = useLang();
  const dict = DICTS[lang] || DICTS.en;
  return (key, vars) => {
    const raw = getPath(dict, key) ?? getPath(DICTS.en, key) ?? key;
    return interpolate(raw, vars);
  };
}
