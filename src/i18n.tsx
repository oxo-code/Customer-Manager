import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type Language = 'en' | 'de';

interface LanguageContextValue {
  lang: Language;
  setLang: (language: Language) => void;
  t: (en: string, de: string) => string;
}

const getPreferredLanguage = (): Language => {
  const saved = localStorage.getItem('customer-manager-language');
  if (saved === 'en' || saved === 'de') {
    return saved;
  }
  return 'en';
};

const LanguageContext = createContext<LanguageContextValue>({
  lang: 'en',
  setLang: () => undefined,
  t: (en, de) => en,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>(() => getPreferredLanguage());

  useEffect(() => {
    localStorage.setItem('customer-manager-language', lang);
  }, [lang]);

  const value = useMemo<LanguageContextValue>(() => ({
    lang,
    setLang: (language: Language) => setLangState(language),
    t: (en: string, de: string) => (lang === 'en' ? en : de),
  }), [lang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export const useLanguage = () => useContext(LanguageContext);
