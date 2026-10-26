"use client";

import React from "react";
import { CategoryEntry, Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import { formatNumber, formatDate } from "@/lib/format";
import { Layers, CheckSquare, Square, Calendar } from "lucide-react";

interface CategorySelectorProps {
  categories: CategoryEntry[];
  selectedCategoryIds: Set<string>;
  onToggleCategory: (catId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  osmExtractDate: string;
  lang: Language;
}

export const CategorySelector: React.FC<CategorySelectorProps> = ({
  categories,
  selectedCategoryIds,
  onToggleCategory,
  onSelectAll,
  onDeselectAll,
  osmExtractDate,
  lang,
}) => {
  const t = translations[lang];

  const totalSelectedPois = categories
    .filter((c) => selectedCategoryIds.has(c.id))
    .reduce((acc, c) => acc + c.count, 0);

  // Format extract date deterministically
  const formattedDate = formatDate(osmExtractDate, lang);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-3">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-brand-600 dark:text-brand-400" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            {t.selectCategoriesTitle}
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onSelectAll}
            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 px-2 py-1 rounded-md hover:bg-brand-50 dark:hover:bg-brand-950/50 transition-colors"
          >
            {t.selectAll}
          </button>
          <span className="text-slate-300 dark:text-slate-700">|</span>
          <button
            type="button"
            onClick={onDeselectAll}
            className="text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {t.deselectAll}
          </button>
        </div>
      </div>

      {/* Freshness date banner */}
      <div className="flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400 mt-3 mb-4 bg-slate-50 dark:bg-slate-800/50 px-3 py-2 rounded-xl">
        <Calendar className="w-4 h-4 text-slate-400" />
        <span>
          {t.dataFrom}{" "}
          <strong
            suppressHydrationWarning
            className="text-slate-700 dark:text-slate-200"
          >
            {formattedDate}
          </strong>
        </span>
      </div>

      {/* Categories Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-72 overflow-y-auto pr-1 custom-scrollbar">
        {categories.map((cat) => {
          const isChecked = selectedCategoryIds.has(cat.id);
          const categoryName = t.categories[cat.id] || cat.id.replace("_", " ").toUpperCase();

          return (
            <label
              key={cat.id}
              className={`flex items-center justify-between p-3 rounded-xl border text-sm cursor-pointer transition-all select-none ${
                isChecked
                  ? "bg-brand-50/60 dark:bg-brand-950/40 border-brand-300 dark:border-brand-800 text-brand-900 dark:text-brand-200 font-medium"
                  : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => onToggleCategory(cat.id)}
                  className="sr-only"
                />
                {isChecked ? (
                  <CheckSquare className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0" />
                ) : (
                  <Square className="w-4 h-4 text-slate-400 shrink-0" />
                )}
                <span className="truncate">{categoryName}</span>
              </div>

              <span
                suppressHydrationWarning
                className="text-xs font-mono bg-white/80 dark:bg-slate-800 px-2 py-0.5 rounded-md text-slate-500 dark:text-slate-400 border border-slate-200/60 dark:border-slate-700 shrink-0 ml-2"
              >
                {formatNumber(cat.count, lang)}
              </span>
            </label>
          );
        })}
      </div>

      {/* Selected count footer */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>
          {selectedCategoryIds.size} / {categories.length} categorii
        </span>
        <span
          suppressHydrationWarning
          className="font-semibold text-slate-800 dark:text-slate-200"
        >
          {formatNumber(totalSelectedPois, lang)} {t.selectedCount}
        </span>
      </div>
    </div>
  );
};
