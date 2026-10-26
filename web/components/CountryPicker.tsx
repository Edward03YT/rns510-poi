"use client";

import React, { useMemo, useState } from "react";
import { CountryEntry, Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import { formatNumber } from "@/lib/format";
import { Search, MapPin, Check } from "lucide-react";

interface CountryPickerProps {
  countries: CountryEntry[];
  selectedCountryId: string;
  onSelectCountry: (countryId: string) => void;
  lang: Language;
}

export const CountryPicker: React.FC<CountryPickerProps> = ({
  countries,
  selectedCountryId,
  onSelectCountry,
  lang,
}) => {
  const t = translations[lang];
  const [query, setQuery] = useState("");

  const sortedCountries = useMemo(() => {
    return [...countries].sort((a, b) => {
      const nameA = a.name[lang] || a.name.en || a.id;
      const nameB = b.name[lang] || b.name.en || b.id;
      return nameA.localeCompare(nameB, lang);
    });
  }, [countries, lang]);

  const filteredCountries = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return sortedCountries;
    return sortedCountries.filter((c) => {
      const nameLocal = (c.name[lang] || "").toLowerCase();
      const nameEn = (c.name.en || "").toLowerCase();
      const id = c.id.toLowerCase();
      return nameLocal.includes(q) || nameEn.includes(q) || id.includes(q);
    });
  }, [sortedCountries, query, lang]);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center space-x-2 mb-4">
        <MapPin className="w-5 h-5 text-brand-600 dark:text-brand-400" />
        <h2 className="text-base font-bold text-slate-900 dark:text-white">
          {t.selectCountryTitle}
        </h2>
      </div>

      {/* Search Input */}
      <div className="relative mb-3">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t.searchCountryPlaceholder}
          className="w-full pl-9 pr-4 py-2 text-sm rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
        />
      </div>

      {/* Country List */}
      <div className="max-h-64 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
        {filteredCountries.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-4">{t.noCountriesFound}</p>
        ) : (
          filteredCountries.map((c) => {
            const isSelected = c.id === selectedCountryId;
            const displayName = c.name[lang] || c.name.en || c.id;
            const totalPois = c.categories.reduce((acc, cat) => acc + cat.count, 0);

            return (
              <button
                key={c.id}
                type="button"
                onClick={() => onSelectCountry(c.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left text-sm transition-all ${
                  isSelected
                    ? "bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 font-semibold border border-brand-200 dark:border-brand-800"
                    : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent"
                }`}
              >
                <div className="flex items-center space-x-2 truncate">
                  <span className="truncate">{displayName}</span>
                  <span className="text-xs text-slate-400 font-normal">
                    ({c.categories.length} cat.)
                  </span>
                </div>

                <div className="flex items-center space-x-2 shrink-0 ml-2">
                  <span
                    suppressHydrationWarning
                    className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md font-mono"
                  >
                    {formatNumber(totalPois, lang)}
                  </span>
                  {isSelected && <Check className="w-4 h-4 text-brand-600 dark:text-brand-400" />}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
