import { Language } from "./types";

const RO_MONTHS = [
  "ian.", "feb.", "mar.", "apr.", "mai", "iun.",
  "iul.", "aug.", "sept.", "oct.", "nov.", "dec."
];

const EN_MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

/**
 * Deterministically formats an integer with thousands separators.
 * Romanian locale uses '.' (e.g. 63.900), English uses ',' (e.g. 63,900).
 * Does not rely on runtime/OS/browser locale variations, preventing SSR hydration mismatches.
 */
export function formatNumber(n: number, lang: Language = "ro"): string {
  const sep = lang === "ro" ? "." : ",";
  const str = Math.round(n).toString();
  return str.replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}

/**
 * Deterministically formats an ISO date string (e.g. "2026-10-26T00:00:00Z").
 * Guarantees exact string matching between Node.js SSR and browser hydration.
 */
export function formatDate(isoDate: string, lang: Language = "ro"): string {
  if (!isoDate) return "";
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return isoDate;
    const day = d.getUTCDate();
    const monthIdx = d.getUTCMonth();
    const year = d.getUTCFullYear();
    const monthList = lang === "ro" ? RO_MONTHS : EN_MONTHS;
    const month = monthList[monthIdx] ?? "";
    return `${day} ${month} ${year}`;
  } catch {
    return isoDate;
  }
}
