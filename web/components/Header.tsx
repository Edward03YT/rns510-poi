"use client";

import React from "react";
import { Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import { Compass, Globe, Github } from "lucide-react";

interface HeaderProps {
  lang: Language;
  onLanguageChange: (newLang: Language) => void;
}

export const Header: React.FC<HeaderProps> = ({ lang, onLanguageChange }) => {
  const t = translations[lang];

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-brand-600 dark:bg-brand-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <Compass className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white leading-tight">
              {t.appTitle}
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
              {t.appSubtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Language Toggle */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <button
              type="button"
              onClick={() => onLanguageChange("ro")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                lang === "ro"
                  ? "bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              RO
            </button>
            <button
              type="button"
              onClick={() => onLanguageChange("en")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                lang === "en"
                  ? "bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              EN
            </button>
          </div>

          <a
            href="https://github.com/your-username/rns510-poi-forge"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
            title="GitHub Repository"
          >
            <Github className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  );
};
