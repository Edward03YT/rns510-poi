export type Language = "ro" | "en";

export interface CategoryFile {
  name: string;
  bytes: number;
  sha256: string;
}

export interface CategoryEntry {
  id: string;
  count: number;
  files: CategoryFile[];
}

export interface CountryEntry {
  id: string;
  name: {
    ro: string;
    en: string;
  };
  osm_extract_date: string;
  categories: CategoryEntry[];
}

export interface FormatStatus {
  verified: boolean;
  note: string;
}

export interface IndexData {
  schema: number;
  generated: string;
  format: FormatStatus;
  countries: CountryEntry[];
}
