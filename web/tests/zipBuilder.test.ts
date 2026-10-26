import { describe, it, expect } from "vitest";
import { unzipSync } from "fflate";
import { buildBrowserZip } from "../lib/zipBuilder";
import { CategoryEntry } from "../lib/types";

describe("Browser ZIP Builder", () => {
  it("builds a valid zip with ATTRIBUTION.txt and selected categories", async () => {
    const categories: CategoryEntry[] = [
      {
        id: "fuel",
        count: 5,
        files: [{ name: "romania_fuel_001.asc", bytes: 100, sha256: "abc" }],
      },
      {
        id: "pharmacy",
        count: 10,
        files: [{ name: "romania_pharmacy_001.asc", bytes: 200, sha256: "def" }],
      },
    ];

    const selected = new Set(["fuel"]);
    const zipBytes = await buildBrowserZip("romania", categories, selected);

    expect(zipBytes).toBeDefined();
    expect(zipBytes.length).toBeGreaterThan(0);

    // Unzip and verify contents
    const unzipped = unzipSync(zipBytes);
    expect(unzipped["ATTRIBUTION.txt"]).toBeDefined();
    expect(unzipped["romania/fuel/romania_fuel_001.asc"]).toBeDefined();
    // Pharmacy was not selected, should not be in zip
    expect(unzipped["romania/pharmacy/romania_pharmacy_001.asc"]).toBeUndefined();
  });
});
