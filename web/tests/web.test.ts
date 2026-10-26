import { describe, it, expect } from "vitest";
import { DEFAULT_MOCK_INDEX } from "../lib/indexLoader";
import { translations } from "../lib/translations";
import { formatNumber, formatDate } from "../lib/format";

describe("Web App Index & Translations", () => {
  it("validates mock index data adheres to Schema 1", () => {
    expect(DEFAULT_MOCK_INDEX.schema).toBe(1);
    expect(DEFAULT_MOCK_INDEX.format.verified).toBe(false);
    expect(DEFAULT_MOCK_INDEX.countries.length).toBeGreaterThan(0);

    const ro = DEFAULT_MOCK_INDEX.countries.find((c) => c.id === "romania");
    expect(ro).toBeDefined();
    expect(ro?.name.ro).toBe("România");
    expect(ro?.categories.length).toBeGreaterThan(0);
  });

  it("ensures translation keys are identical between RO and EN", () => {
    const roKeys = Object.keys(translations.ro).sort();
    const enKeys = Object.keys(translations.en).sort();
    expect(roKeys).toEqual(enKeys);

    // Check categories dictionary completeness
    const roCatKeys = Object.keys(translations.ro.categories).sort();
    const enCatKeys = Object.keys(translations.en.categories).sort();
    expect(roCatKeys).toEqual(enCatKeys);
  });

  it("checks country sorting by language", () => {
    const countries = [
      { id: "germany", name: { ro: "Germania", en: "Germany" } },
      { id: "andorra", name: { ro: "Andorra", en: "Andorra" } },
      { id: "romania", name: { ro: "România", en: "Romania" } },
    ];

    const sortedRo = [...countries].sort((a, b) => a.name.ro.localeCompare(b.name.ro, "ro"));
    expect(sortedRo[0].id).toBe("andorra");
    expect(sortedRo[1].id).toBe("germany");
    expect(sortedRo[2].id).toBe("romania");
  });

  it("formats numbers and dates deterministically across SSR and browser", () => {
    // Number formatting
    expect(formatNumber(63900, "ro")).toBe("63.900");
    expect(formatNumber(63900, "en")).toBe("63,900");
    expect(formatNumber(1234567, "ro")).toBe("1.234.567");
    expect(formatNumber(42, "ro")).toBe("42");

    // Date formatting
    expect(formatDate("2026-10-26T00:00:00Z", "ro")).toBe("26 oct. 2026");
    expect(formatDate("2026-10-26T00:00:00Z", "en")).toBe("26 Oct 2026");
    expect(formatDate("invalid-date", "ro")).toBe("invalid-date");
    expect(formatDate("", "ro")).toBe("");
  });
});
