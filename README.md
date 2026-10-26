# RNS 510 POI Forge

[Română](README_RO.md) | **English**

Open-source toolkit to build Personal POI (Point of Interest) packages for Volkswagen **RNS 510** (and compatible Škoda Columbus / SEAT Media System) navigation units directly from OpenStreetMap data.

> [!WARNING]
> **UNVERIFIED FILE FORMAT**: The `.asc` file syntax and import specifications are currently based on community conventions and have **not yet been verified on a physical RNS 510 unit**. Please see [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) to generate probe files and test them on your head unit.

---

## Disclaimer

This project is **unofficial and not affiliated with Volkswagen AG**, Škoda Auto, SEAT S.A., or any of their subsidiaries. Importing custom POI files into your head unit is performed at your own risk. OpenStreetMap data is contributed by volunteers and may be incomplete, inaccurate, or outdated.

**Speed cameras and radar enforcement warnings are strictly out of scope** due to differing legal regulations across European countries. No firmware, maps, or proprietary vehicle software are hosted or linked in this repository.

---

## Features

- **Automated OpenStreetMap Processing:** Extracts POIs per country and category using Geofabrik country extracts.
- **Configurable ASC Writer:** Flexible formatting engine controlled by `config/format.yml` with coordinate ordering, character encoding (CP1250, CP1252, UTF-8), and diacritic transliteration.
- **Hardware Probing CLI:** Built-in `poi-forge probe-file` command to generate test files with edge cases (diacritics, long strings, quoting) and format matrices for hardware validation.
- **Repository Automation:** Scheduled GitHub Actions to periodically refresh and publish packages.
- **Static Web App:** Browser-based catalog to select countries and categories, download files, or package custom ZIP archives directly in the browser.

---

## Quick Start (Phase 0: Format Probing)

Before building full country packages, test the file format on your car's RNS 510:

```bash
# Clone the repository
git clone https://github.com/your-username/rns510-poi-forge.git
cd rns510-poi-forge

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"

# Generate probe file and format variant matrix
poi-forge probe-file --out probe.asc --generate-matrix
```

Follow the step-by-step instructions in [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) to copy the files to an SD card and test importing them on your unit.

---

## Project Structure

```
rns510-poi-forge/
├── poi_forge/                     # Python package
│   ├── cli.py                     # CLI entrypoint & subcommands
│   ├── formats/
│   │   ├── base.py                # Writer interface & POIRecord
│   │   └── rns510_asc.py          # RNS 510 configurable ASC writer
├── config/
│   └── format.yml                 # ASC format configuration (UNVERIFIED)
├── docs/
│   └── FORMAT_PROBE.md            # Hardware probing guide (RO / EN)
├── tests/                         # Pytest test suite
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## License & Attribution

- **Code:** Licensed under the [MIT License](LICENSE).
- **Data:** POI data extracted from OpenStreetMap is licensed under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/).
- Attribution: **© OpenStreetMap contributors** ([https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)).
