"use client";

import React, { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { VerifiedNotice } from "@/components/VerifiedNotice";
import { CountryPicker } from "@/components/CountryPicker";
import { CategorySelector } from "@/components/CategorySelector";
import { DownloadPanel } from "@/components/DownloadPanel";
import { Footer } from "@/components/Footer";
import { DEFAULT_MOCK_INDEX } from "@/lib/indexLoader";
import { CountryEntry, IndexData, Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import {
  Download,
  BookOpen,
  Info,
  ExternalLink,
  HardDrive,
} from "lucide-react";

export default function HomePage() {
  const [indexData, setIndexData] = useState<IndexData>(DEFAULT_MOCK_INDEX);
  const [lang, setLang] = useState<Language>("ro");
  const [selectedCountryId, setSelectedCountryId] = useState<string>("romania");
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"download" | "instructions" | "about">("download");

  const t = translations[lang];

  // Try to fetch remote index if NEXT_PUBLIC_INDEX_URL is set
  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_INDEX_URL;
    if (url) {
      fetch(url)
        .then((res) => res.json())
        .then((data: IndexData) => {
          if (data && data.countries && data.countries.length > 0) {
            setIndexData(data);
          }
        })
        .catch((err) => {
          console.warn("Using bundled index data:", err);
        });
    }
  }, []);

  // Update selected country and default categories
  const currentCountry: CountryEntry =
    indexData.countries.find((c) => c.id === selectedCountryId) ||
    indexData.countries[0];

  useEffect(() => {
    if (currentCountry) {
      setSelectedCategoryIds(new Set(currentCountry.categories.map((c) => c.id)));
    }
  }, [selectedCountryId, currentCountry]);

  const handleToggleCategory = (catId: string) => {
    setSelectedCategoryIds((prev) => {
      const next = new Set(prev);
      if (next.has(catId)) {
        next.delete(catId);
      } else {
        next.add(catId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (currentCountry) {
      setSelectedCategoryIds(new Set(currentCountry.categories.map((c) => c.id)));
    }
  };

  const handleDeselectAll = () => {
    setSelectedCategoryIds(new Set());
  };

  return (
    <div className="flex-1 flex flex-col">
      <Header lang={lang} onLanguageChange={setLang} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Verification Warning Notice */}
        <VerifiedNotice formatStatus={indexData.format} lang={lang} />

        {/* Tab Navigation */}
        <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 mb-6">
          <button
            type="button"
            onClick={() => setActiveTab("download")}
            className={`flex items-center space-x-2 py-3 px-4 font-semibold text-sm border-b-2 transition-all ${
              activeTab === "download"
                ? "border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            }`}
          >
            <Download className="w-4 h-4" />
            <span>{t.downloadSectionTitle}</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("instructions")}
            className={`flex items-center space-x-2 py-3 px-4 font-semibold text-sm border-b-2 transition-all ${
              activeTab === "instructions"
                ? "border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>{t.instructionsTab}</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("about")}
            className={`flex items-center space-x-2 py-3 px-4 font-semibold text-sm border-b-2 transition-all ${
              activeTab === "about"
                ? "border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400"
                : "border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            }`}
          >
            <Info className="w-4 h-4" />
            <span>{t.aboutTab}</span>
          </button>
        </div>

        {/* Main Content Area */}
        {activeTab === "download" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Country Picker - 4 columns on desktop */}
            <div className="lg:col-span-5">
              <CountryPicker
                countries={indexData.countries}
                selectedCountryId={selectedCountryId}
                onSelectCountry={setSelectedCountryId}
                lang={lang}
              />
            </div>

            {/* Category Selector & Download - 7 columns on desktop */}
            <div className="lg:col-span-7 space-y-6">
              <CategorySelector
                categories={currentCountry.categories}
                selectedCategoryIds={selectedCategoryIds}
                onToggleCategory={handleToggleCategory}
                onSelectAll={handleSelectAll}
                onDeselectAll={handleDeselectAll}
                osmExtractDate={currentCountry.osm_extract_date}
                lang={lang}
              />

              <DownloadPanel
                countryId={selectedCountryId}
                categories={currentCountry.categories}
                selectedCategoryIds={selectedCategoryIds}
                lang={lang}
              />
            </div>
          </div>
        )}

        {/* Import Instructions Tab */}
        {activeTab === "instructions" && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm max-w-3xl mx-auto space-y-6">
            <div className="flex items-center space-x-3 pb-4 border-b border-slate-100 dark:border-slate-800">
              <HardDrive className="w-6 h-6 text-brand-600 dark:text-brand-400" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                {t.importInstructionsTitle}
              </h2>
            </div>

            <ol className="space-y-4 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              <li className="flex items-start space-x-3">
                <span className="w-6 h-6 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  1
                </span>
                <p>{t.importStep1}</p>
              </li>
              <li className="flex items-start space-x-3">
                <span className="w-6 h-6 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  2
                </span>
                <p>{t.importStep2}</p>
              </li>
              <li className="flex items-start space-x-3">
                <span className="w-6 h-6 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  3
                </span>
                <p>{t.importStep3}</p>
              </li>
              <li className="flex items-start space-x-3">
                <span className="w-6 h-6 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  4
                </span>
                <p>{t.importStep4}</p>
              </li>
            </ol>

            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl text-xs text-slate-500 dark:text-slate-400">
              <p>{t.importNote}</p>
              <div className="mt-2">
                <a
                  href="https://github.com/your-username/rns510-poi-forge/blob/master/docs/FORMAT_PROBE.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-brand-600 dark:text-brand-400 hover:underline font-semibold"
                >
                  <span>{t.probeGuideLink}</span>
                  <ExternalLink className="w-3.5 h-3.5 ml-1" />
                </a>
              </div>
            </div>
          </div>
        )}

        {/* About & Limits Tab */}
        {activeTab === "about" && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm max-w-3xl mx-auto space-y-5 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
              {t.aboutTitle}
            </h2>
            <p>{t.aboutOsm}</p>
            <p>{t.aboutOdbl}</p>
            <div className="bg-red-50 dark:bg-red-950/30 border-l-4 border-red-500 p-3.5 rounded-r-xl text-red-900 dark:text-red-200 text-xs">
              {t.aboutSpeedCameras}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t.aboutDisclaimer}
            </p>
          </div>
        )}
      </main>

      <Footer lang={lang} />
    </div>
  );
}
