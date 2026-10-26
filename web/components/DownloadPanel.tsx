"use client";

import React, { useState } from "react";
import { CategoryEntry, Language } from "@/lib/types";
import { translations } from "@/lib/translations";
import { buildBrowserZip, triggerBrowserDownload } from "@/lib/zipBuilder";
import {
  Download,
  FileDown,
  FileText,
  ShieldCheck,
  Check,
  Copy,
  Loader2,
  Package,
} from "lucide-react";

interface DownloadPanelProps {
  countryId: string;
  categories: CategoryEntry[];
  selectedCategoryIds: Set<string>;
  lang: Language;
}

export const DownloadPanel: React.FC<DownloadPanelProps> = ({
  countryId,
  categories,
  selectedCategoryIds,
  lang,
}) => {
  const t = translations[lang];
  const [isBuildingZip, setIsBuildingZip] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const selectedCats = categories.filter((c) => selectedCategoryIds.has(c.id));
  const totalFiles = selectedCats.reduce((acc, c) => acc + c.files.length, 0);

  const handleDownloadAllZip = async () => {
    if (selectedCats.length === 0) return;
    setIsBuildingZip(true);
    try {
      // Resolve files from release assets if URL exists, or generate
      const resolver = async (catId: string, fileName: string) => {
        const releaseBase = process.env.NEXT_PUBLIC_RELEASE_BASE_URL;
        if (releaseBase) {
          const res = await fetch(`${releaseBase}/${countryId}/${catId}/${fileName}`);
          if (res.ok) {
            const buf = await res.arrayBuffer();
            return new Uint8Array(buf);
          }
        }
        // Fallback demo content
        return `26.100000,44.400000,"${countryId} - ${catId} POI","RNS 510 Personal POI"\r\n`;
      };

      const zipData = await buildBrowserZip(
        countryId,
        categories,
        selectedCategoryIds,
        resolver
      );
      triggerBrowserDownload(zipData, `${countryId}_rns510_poi.zip`);
    } catch (err) {
      console.error("ZIP build error:", err);
    } finally {
      setIsBuildingZip(false);
    }
  };

  const handleDownloadSingleFile = (fileName: string, catId: string) => {
    const demoContent = `26.100000,44.400000,"${countryId} - ${catId}","RNS 510 Personal POI"\r\n`;
    triggerBrowserDownload(demoContent, fileName);
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2">
          <Package className="w-5 h-5 text-brand-600 dark:text-brand-400" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            {t.downloadSectionTitle}
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">
          {totalFiles} fișier(e)
        </span>
      </div>

      {/* Main ZIP Download Button */}
      <button
        type="button"
        disabled={selectedCats.length === 0 || isBuildingZip}
        onClick={handleDownloadAllZip}
        className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm shadow-md shadow-brand-500/20 flex items-center justify-center space-x-2.5 transition-all"
      >
        {isBuildingZip ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{t.buildingZip}</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>{t.downloadZipButton}</span>
          </>
        )}
      </button>

      {/* Individual Files List */}
      <div>
        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
          {t.individualFiles}
        </h4>

        {selectedCats.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl">
            Selectează cel puțin o categorie pentru a descărca fișierele.
          </p>
        ) : (
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1 custom-scrollbar">
            {selectedCats.map((cat) => (
              <div key={cat.id} className="space-y-1.5">
                {cat.files.map((file) => (
                  <div
                    key={file.name}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60 text-xs gap-2"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileText className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0" />
                      <span className="font-mono text-slate-700 dark:text-slate-200 truncate font-medium">
                        {file.name}
                      </span>
                      <span className="text-slate-400 font-mono shrink-0">
                        ({(file.bytes / 1024).toFixed(1)} KB)
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0 self-end sm:self-auto">
                      {/* SHA256 copy button */}
                      <button
                        type="button"
                        onClick={() => copyHash(file.sha256)}
                        title={`SHA256: ${file.sha256} (Click to copy)`}
                        className="flex items-center space-x-1 px-2 py-1 rounded-md bg-white dark:bg-slate-700 text-slate-500 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-600 font-mono text-[11px] transition-colors"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>{file.sha256.substring(0, 8)}...</span>
                        {copiedHash === file.sha256 ? (
                          <Check className="w-3 h-3 text-emerald-600 ml-1" />
                        ) : (
                          <Copy className="w-3 h-3 text-slate-400 ml-1" />
                        )}
                      </button>

                      {/* Download single file button */}
                      <button
                        type="button"
                        onClick={() => handleDownloadSingleFile(file.name, cat.id)}
                        className="p-1.5 rounded-md bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-200 hover:text-brand-600 dark:hover:text-brand-400 border border-slate-200 dark:border-slate-600 transition-colors"
                        title="Download single .asc file"
                      >
                        <FileDown className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
