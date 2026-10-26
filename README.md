# RNS 510 POI Forge

[Română](README_RO.md) | **English**

[![CI](https://github.com/your-username/rns510-poi-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/rns510-poi-forge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Data License: ODbL](https://img.shields.io/badge/Data%20License-ODbL%201.0-green.svg)](https://opendatacommons.org/licenses/odbl/1.0/)

An open-source toolkit to build, validate, and package ready-to-import Personal POI (Points of Interest) databases for the Volkswagen **RNS 510** (and compatible Škoda Columbus / SEAT Media System) head units from OpenStreetMap data.

> [!WARNING]
> **UNVERIFIED FILE FORMAT ON HARDWARE**: The `.asc` file syntax and SD card layout are currently based on community conventions and have **not yet been verified on a physical RNS 510 unit**. Please see [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) to generate probe files and test them on your head unit.

---

## Architecture Overview

The project is structured into three layers:

```
rns510-poi-forge/
├── 1. Python CLI (poi_forge/)      # PBF extract, normalize, chunk, validate, ASC writer
├── 2. CI/CD Automation (.github/)  # Monthly scheduled matrix rebuilds & GitHub Releases
└── 3. Web App (web/)               # Next.js static app with browser-side ZIP builder
```

```
+-------------------------------------------------------------+
|                     OpenStreetMap Data                      |
|            (Geofabrik Extracts / Overpass API)              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   1. Python CLI (poi-forge)                 |
|  - Fast pyosmium extraction & way centroid computation      |
|  - Privacy filtering (strips phone numbers, private emails) |
|  - Configurable ASC writer (CP1250, transliteration, CRLF)  |
|  - Automated chunking (5,000 POIs / 2MB per file)           |
|  - Bounding box and syntax validator                        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              2. GitHub Actions Automation                   |
|  - Monthly scheduled matrix rebuilds for Europe             |
|  - Publishes <country>.zip & index.json as release assets   |
|  - Stable 'latest' pointer for static web consumption       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 3. Next.js Static Web App                   |
|  - Searchable country picker & category checkboxes          |
|  - Instant bilingual toggle (Romanian / English)            |
|  - In-browser ZIP packaging (fflate) with ATTRIBUTION.txt   |
|  - Step-by-step SD card import instructions                 |
+-------------------------------------------------------------+
```

---

## 0. Ground Rules & Legal Disclaimers

- **Disclaimer:** This project is **unofficial and not affiliated with Volkswagen AG**, Škoda Auto, SEAT S.A., or any of their subsidiaries. Importing POI files into your head unit is performed at your own risk. POI data may be incomplete, inaccurate, or outdated.
- **Speed cameras and radar enforcement data are strictly excluded** due to legal restrictions across European countries.
- **No firmware or map files** are hosted, distributed, or linked in this repository.
- **Data License:** POI data is extracted from OpenStreetMap and licensed under the **Open Database License (ODbL) 1.0**. Every distributed package contains `ATTRIBUTION.txt`.
- **Code License:** Licensed under the [MIT License](LICENSE).

---

## 1. Quick Start

### Installation

Requires Python 3.10+ (tested up to Python 3.14):

```bash
# Clone the repository
git clone https://github.com/your-username/rns510-poi-forge.git
cd rns510-poi-forge

# Create and activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run full Python test suite (52 tests)
pytest -v

# Run linter
ruff check .
```

---

## 2. CLI Usage

The CLI tool provides commands for the complete POI building lifecycle:

### List Available Countries
```bash
poi-forge list-countries
```
Queries the live Geofabrik index (`index-v1.json`) and lists all European country extracts with publishing status and sub-region details.

### Hardware Probing
```bash
# Generate default 5-POI probe file
poi-forge probe-file --out probe.asc

# Generate complete 8-variant format matrix (lon/lat, lat/lon, tabs, semicolons, CP1250, UTF-8)
poi-forge probe-file --out probe.asc --generate-matrix
```
Follow instructions in [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) to test the files on your car's head unit.

### Building Country Packages
```bash
# Build all categories for a country (e.g. Romania)
poi-forge build --country romania --zip --out packages

# Build specific categories for Luxembourg
poi-forge build --country luxembourg --categories fuel,ev_charging,supermarket --zip --out packages
```

### Validating Generated Files
```bash
# Validate an individual file or entire directory
poi-forge validate packages/romania
```
Checks WGS84 coordinates, European bounding boxes, string lengths, encodings, file size thresholds, and duplicate coordinates.

### Building Release Index
```bash
poi-forge index --packages packages --out packages/index.json
```
Compiles a Schema-1 `index.json` catalog containing country metadata, category counts, file sizes, and SHA256 checksums.

### Custom Area Mode (Overpass API)
```bash
# Extract POIs around a coordinate within a 10 km radius (strict 25 km safety cap)
poi-forge custom-area --lat 44.4323 --lon 26.1063 --radius-km 10 --categories fuel,ev_charging --zip --out custom_packages
```

---

## 3. Supported POI Categories

Configured in `config/categories.yml`:

| Category ID | Name (RO) | Name (EN) | OSM Filter |
|---|---|---|---|
| `fuel` | Benzinării | Fuel Stations | `amenity=fuel` |
| `lpg` | GPL (Autogas) | LPG (Autogas) | `amenity=fuel` + `fuel:lpg=yes` |
| `ev_charging` | Stații Încărcare EV | EV Charging Stations | `amenity=charging_station` |
| `parking_large` | Parcări Mari & Park+Ride | Large Parking & Park+Ride | `amenity=parking` with name, `park_ride`, or capacity >= 100 |
| `truck_parking` | Parcări Camioane (TIR) | Truck Parking | `amenity=parking` + `hgv=yes\|designated` |
| `rest_area` | Zone Odihnă | Rest Areas & Services | `highway=rest_area\|services` |
| `pharmacy` | Farmacii | Pharmacies | `amenity=pharmacy` |
| `atm` | Bancomate (ATM) | ATMs | `amenity=atm` |
| `hospital` | Spitale & Urgențe | Hospitals & Emergency | `amenity=hospital` |
| `car_repair` | Service Auto | Car Repair | `shop=car_repair` |
| `tyres` | Vulcanizări | Tyre Shops | `shop=tyres` |
| `car_wash` | Spălătorii Auto | Car Washes | `amenity=car_wash` |
| `camping` | Camping & Rulote | Camping & Caravan Sites | `tourism=camp_site\|caravan_site` |
| `supermarket` | Supermarketuri | Supermarkets | `shop=supermarket` |
| `border_crossing` | Puncte Frontieră | Border Crossings | `barrier=border_control` |

---

## 4. Next.js Web Application

The `web/` directory contains a standalone Next.js App Router static web application:

```bash
cd web
npm install
npm run dev     # Starts local development server at http://localhost:3000
npm run test    # Runs Vitest unit tests (4 passed)
npm run build   # Generates production static export for Vercel
```

### Web App Features
- **Client-Side ZIP Generation:** Uses `fflate` to package selected `.asc` files and `ATTRIBUTION.txt` into a ZIP directly in the browser, eliminating server bandwidth and computation.
- **Language Switcher:** Instant toggle between Romanian (`ro`, default) and English (`en`).
- **Interactive Checkbox UI:** Shows live POI counts per category and total selected destinations.
- **Step-by-Step Import Guide:** Embedded walkthrough for SD card preparation and RNS 510 menu navigation.

---

## 5. How to Import on the Car Unit

1. Copy the `.asc` files onto a **FAT32-formatted SD card** (max 32 GB) inside a folder named `PersonalPOI` (or directly in the root).
2. Insert the SD card into the RNS 510.
3. Press **NAV** &rarr; **My special destinations (Personal POI)** &rarr; **Import** &rarr; **Import into database**.
4. Full details: [docs/IMPORT_EN.md](docs/IMPORT_EN.md) | [docs/IMPORT_RO.md](docs/IMPORT_RO.md).

---

## 6. License & Attribution

- **Source Code:** [MIT License](LICENSE).
- **Data:** Derived from OpenStreetMap data, licensed under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/).
- Attribution: **© OpenStreetMap contributors** ([https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)).
