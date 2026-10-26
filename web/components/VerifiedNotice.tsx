"use client";

import React from "react";
import { Language, FormatStatus } from "@/lib/types";
import { translations } from "@/lib/translations";
import { AlertTriangle, ExternalLink } from "lucide-react";

interface VerifiedNoticeProps {
  formatStatus: FormatStatus;
  lang: Language;
}

export const VerifiedNotice: React.FC<VerifiedNoticeProps> = ({ formatStatus, lang }) => {
  if (formatStatus.verified) {
    return null;
  }

  const t = translations[lang];

  return (
    <div className="bg-amber-50 dark:bg-amber-950/40 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-sm mb-6 transition-colors">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="text-sm">
          <h3 className="font-semibold text-amber-900 dark:text-amber-200">
            {t.unverifiedWarningTitle}
          </h3>
          <p className="text-amber-800/90 dark:text-amber-300/80 mt-1">
            {t.unverifiedWarningBody}
          </p>
          <div className="mt-2">
            <a
              href="https://github.com/your-username/rns510-poi-forge/blob/master/docs/FORMAT_PROBE.md"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-xs font-semibold text-amber-900 dark:text-amber-200 underline hover:text-amber-700 dark:hover:text-amber-100"
            >
              <span>{t.probeGuideLink}</span>
              <ExternalLink className="w-3.5 h-3.5 ml-1" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
