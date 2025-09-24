import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Globe } from 'lucide-react';

const LanguageSwitcher = ({ className = "" }) => {
  const { language, setLanguage, t } = useLanguage();

  const handleLanguageChange = (newLanguage) => {
    if (newLanguage !== language) {
      setLanguage(newLanguage);
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <Globe className="w-4 h-4 text-slate-600" />
      <div className="flex bg-white/80 rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <button
          onClick={() => handleLanguageChange('tr')}
          className={`px-3 py-1.5 text-sm font-medium transition-colors ${
            language === 'tr' 
              ? 'bg-[#2c5282] text-white' 
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          TR
        </button>
        <button
          onClick={() => handleLanguageChange('en')}
          className={`px-3 py-1.5 text-sm font-medium transition-colors ${
            language === 'en' 
              ? 'bg-[#2c5282] text-white' 
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          EN
        </button>
      </div>
    </div>
  );
};

export default LanguageSwitcher;