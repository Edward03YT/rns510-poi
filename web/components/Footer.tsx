"use client";

import React from "react";
import { Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import { ShieldAlert, Database } from "lucide-react";

interface FooterProps {
  lang: Language;
}

export const Footer: React.FC<FooterProps> = ({ lang }) => {
  const t = translations[lang];

  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 py-8 mt-12 transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4 text-xs text-slate-500 dark:text-slate-400">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-2 max-w-2xl">
            <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <p>{t.footerDisclaimer}</p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <Database className="w-4 h-4 text-slate-400 shrink-0" />
            <p>
              ©{" "}
              <a
                href="https://www.openstreetmap.org/copyright"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-slate-700 dark:hover:text-slate-200"
              >
                OpenStreetMap contributors
              </a>{" "}
              (
              <a
                href="https://opendatacommons.org/licenses/odbl/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-slate-700 dark:hover:text-slate-200"
              >
                ODbL
              </a>
              )
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200/60 dark:border-slate-800/60 text-center text-slate-400 dark:text-slate-500 text-[11px]">
          rns510-poi-forge &bull; Open-source under MIT License &bull; Volkswagen, Škoda, and SEAT are trademarks of Volkswagen AG.
        </div>
      </div>
    </footer>
  );
};
