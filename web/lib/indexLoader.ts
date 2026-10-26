import { IndexData } from "./types";

export const DEFAULT_MOCK_INDEX: IndexData = {
  schema: 1,
  generated: "2026-10-26T00:00:00Z",
  format: {
    verified: false,
    note: "UNVERIFIED: Default ASC settings based on community convention. Awaiting physical hardware probe on RNS 510 unit.",
  },
  countries: [
    {
      id: "romania",
      name: { ro: "România", en: "Romania" },
      osm_extract_date: "2026-10-25T21:21:00Z",
      categories: [
        {
          id: "fuel",
          count: 4321,
          files: [{ name: "romania_fuel_001.asc", bytes: 145230, sha256: "8d79324dfed9eae11d6b11dcfe1b8036f95e6b4a" }],
        },
        {
          id: "lpg",
          count: 1840,
          files: [{ name: "romania_lpg_001.asc", bytes: 64200, sha256: "fd3142bf94498a5b605ea21324a82f5be37be8b5" }],
        },
        {
          id: "ev_charging",
          count: 1250,
          files: [{ name: "romania_ev_charging_001.asc", bytes: 48900, sha256: "c18f1234abcd5678" }],
        },
        {
          id: "pharmacy",
          count: 5120,
          files: [{ name: "romania_pharmacy_001.asc", bytes: 182300, sha256: "a12bcde3456" }],
        },
        {
          id: "supermarket",
          count: 3890,
          files: [{ name: "romania_supermarket_001.asc", bytes: 135400, sha256: "f456789abc" }],
        },
      ],
    },
    {
      id: "germany",
      name: { ro: "Germania", en: "Germany" },
      osm_extract_date: "2026-10-25T21:21:00Z",
      categories: [
        {
          id: "fuel",
          count: 14500,
          files: [
            { name: "germany_fuel_001.asc", bytes: 240000, sha256: "aa11bb22" },
            { name: "germany_fuel_002.asc", bytes: 240000, sha256: "cc33dd44" },
            { name: "germany_fuel_003.asc", bytes: 110000, sha256: "ee55ff66" },
          ],
        },
        {
          id: "ev_charging",
          count: 28400,
          files: [
            { name: "germany_ev_charging_001.asc", bytes: 240000, sha256: "11223344" },
            { name: "germany_ev_charging_002.asc", bytes: 240000, sha256: "55667788" },
          ],
        },
        {
          id: "supermarket",
          count: 21000,
          files: [{ name: "germany_supermarket_001.asc", bytes: 250000, sha256: "99887766" }],
        },
      ],
    },
    {
      id: "monaco",
      name: { ro: "Monaco", en: "Monaco" },
      osm_extract_date: "2026-10-25T21:21:00Z",
      categories: [
        {
          id: "fuel",
          count: 3,
          files: [{ name: "monaco_fuel_001.asc", bytes: 128, sha256: "fd3142bf94498a5b605ea21324a82f5be37be8b5" }],
        },
        {
          id: "ev_charging",
          count: 10,
          files: [{ name: "monaco_ev_charging_001.asc", bytes: 420, sha256: "8d79324dfed9eae11d6b11dcfe1b8036f95e6b4a" }],
        },
        {
          id: "pharmacy",
          count: 18,
          files: [{ name: "monaco_pharmacy_001.asc", bytes: 790, sha256: "c18f1234abcd5678" }],
        },
        {
          id: "supermarket",
          count: 10,
          files: [{ name: "monaco_supermarket_001.asc", bytes: 480, sha256: "f456789abc" }],
        },
      ],
    },
    {
      id: "andorra",
      name: { ro: "Andorra", en: "Andorra" },
      osm_extract_date: "2026-10-25T21:21:00Z",
      categories: [
        {
          id: "fuel",
          count: 61,
          files: [{ name: "andorra_fuel_001.asc", bytes: 2150, sha256: "13b8cbc6cd9941acae18e8af11e1d04b" }],
        },
        {
          id: "ev_charging",
          count: 11,
          files: [{ name: "andorra_ev_charging_001.asc", bytes: 510, sha256: "bb22cc33" }],
        },
        {
          id: "pharmacy",
          count: 36,
          files: [{ name: "andorra_pharmacy_001.asc", bytes: 1420, sha256: "dd44ee55" }],
        },
        {
          id: "supermarket",
          count: 48,
          files: [{ name: "andorra_supermarket_001.asc", bytes: 1980, sha256: "ff66aa77" }],
        },
      ],
    },
  ],
};

export async function fetchIndexData(): Promise<{ data: IndexData; isFallback: boolean }> {
  const indexUrl = process.env.NEXT_PUBLIC_INDEX_URL;
  if (!indexUrl) {
    return { data: DEFAULT_MOCK_INDEX, isFallback: true };
  }

  try {
    const res = await fetch(indexUrl, { next: { revalidate: 3600 } });
    if (!res.ok) {
      throw new Error(`Failed to fetch index (${res.status})`);
    }
    const json = (await res.json()) as IndexData;
    return { data: json, isFallback: false };
  } catch (err) {
    console.warn("Could not fetch remote index.json, using fallback data:", err);
    return { data: DEFAULT_MOCK_INDEX, isFallback: true };
  }
}
