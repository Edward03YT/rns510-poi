# RNS 510 POI Forge

**Română** | [English](README.md)

[![CI](https://github.com/your-username/rns510-poi-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/rns510-poi-forge/actions/workflows/ci.yml)
[![Licență Cod: MIT](https://img.shields.io/badge/Licenta-MIT-blue.svg)](LICENSE)
[![Licență Date: ODbL](https://img.shields.io/badge/Licenta%20Date-ODbL%201.0-green.svg)](https://opendatacommons.org/licenses/odbl/1.0/)

Soluție open-source completă pentru generarea, validarea și împachetarea de baze de date de puncte de interes personalizate (Personal POI) pentru unitățile de navigație Volkswagen **RNS 510** (și Škoda Columbus / SEAT Media System) direct din datele OpenStreetMap.

> [!WARNING]
> **FORMAT NECONFIRMAT PE UNITATE FIZICĂ**: Sintaxa fișierelor `.asc` și structura folderelor pe cardul SD se bazează pe convențiile comunității auto și **nu au fost încă validate pe o unitate reală RNS 510**. Consultați [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) pentru a genera fișiere de test și a le proba pe aparatul mașinii dumneavoastră.

---

## Prezentarea Arhitecturii

Proiectul este structurat pe trei straturi complementare:

```
rns510-poi-forge/
├── 1. CLI Python (poi_forge/)      # Extragere PBF, normalizare, chunking, validare, generator ASC
├── 2. Automatizare CI/CD (.github/)# Reconstrucție automată lunară & GitHub Releases
└── 3. Aplicație Web (web/)         # Next.js static cu împachetare ZIP direct în browser
```

```
+-------------------------------------------------------------+
|                     Date OpenStreetMap                      |
|            (Extrase Geofabrik / API Overpass)               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   1. CLI Python (poi-forge)                 |
|  - Extragere rapidă pyosmium & calcul centroizi poligoane   |
|  - Filtrare confidențialitate (elimină telefoane/email-uri) |
|  - Generator ASC configurabil (CP1250, transliterare, CRLF) |
|  - Împărțire automată în chunks (5.000 POI / 2MB per fișier)|
|  - Validator de sintaxă, delimitatori și limite geografice  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              2. Automatizare GitHub Actions                 |
|  - Reconstrucție lunară programată pe matrice pentru Europa |
|  - Publicare arhive <tara>.zip & index.json ca asset-uri    |
|  - Punctator stabil 'latest' pentru consum web static       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 3. Aplicație Web Next.js                    |
|  - Selector căutabil de țări & selecție categorii cu contor |
|  - Comutator bilingv instant (Română / Engleză)             |
|  - Împachetare ZIP în browser (fflate) cu ATTRIBUTION.txt   |
|  - Ghid de import pe cardul SD pas cu pas                   |
+-------------------------------------------------------------+
```

---

## 0. Reguli de Bază și Declinarea Responsabilității

- **Disclaimer:** Acest proiect este **neoficial și nu este afiliat cu Volkswagen AG**, Škoda Auto, SEAT S.A. sau filialele acestora. Importarea fișierelor POI se face pe propria răspundere. Datele OpenStreetMap sunt colectate de voluntari și pot conține erori sau omisiuni.
- **Camerele radar și radarele fixe NU sunt incluse**, în conformitate cu legislațiile țărilor europene.
- **Niciun fișier de firmware sau hartă de navigație** nu este găzduit sau distribuit în acest proiect.
- **Licență Date:** Datele POI sunt licențiate sub **Open Database License (ODbL) 1.0**. Fiecare pachet include fișierul `ATTRIBUTION.txt`.
- **Licență Cod:** Licență open-source [MIT](LICENSE).

---

## 1. Ghid Rapid de Instalare

Necesită Python 3.10+ (testat până la Python 3.14):

```bash
# Clonează depozitul
git clone https://github.com/your-username/rns510-poi-forge.git
cd rns510-poi-forge

# Creează și activează mediul virtual
python -m venv .venv
# Pe Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Pe Linux/macOS:
source .venv/bin/activate

# Instalează în mod editabil cu dependențele de dezvoltare
pip install -e ".[dev]"
```

### Rularea Testelor Automate

```bash
# Rulare teste Python (52 de teste)
pytest -v

# Verificare conformitate cod (linter)
ruff check .
```

---

## 2. Utilizarea Liniei de Comandă (CLI)

### Listarea Țărilor Disponibile
```bash
poi-forge list-countries
```
Interoghează indexul Geofabrik (`index-v1.json`) și afișează toate extrasele europene disponibile.

### Testarea Formatului pe Navigație (Probe)
```bash
# Generează fișierul de test implicit cu 5 POI-uri
poi-forge probe-file --out probe.asc

# Generează matricea completă de 8 variante de sintaxă
poi-forge probe-file --out probe.asc --generate-matrix
```
Urmați instrucțiunile din [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) pentru a testa pe mașină.

### Construirea Pachetelor pentru o Țară
```bash
# Construiește toate categoriile pentru România
poi-forge build --country romania --zip --out packages

# Construiește categorii specifice pentru Luxemburg
poi-forge build --country luxembourg --categories fuel,ev_charging,supermarket --zip --out packages
```

### Validarea Fișierelor Generate
```bash
poi-forge validate packages/romania
```
Verifică coordonatele WGS84, încadrarea în limitele geografice, lungimea numelor, setul de caractere și absența duplicatelor.

### Generarea Indexului de Publicare
```bash
poi-forge index --packages packages --out packages/index.json
```

### Modul Zonă Personalizată (Overpass API)
```bash
# Extrage POI-uri în jurul unei coordonate pe o rază de 10 km (limită strictă de siguranță: max 25 km)
poi-forge custom-area --lat 44.4323 --lon 26.1063 --radius-km 10 --categories fuel,ev_charging --zip --out custom_packages
```

---

## 3. Categorii Suportate

Configurate în `config/categories.yml`:

| ID Categorie | Denumire (RO) | Denumire (EN) | Filtru OSM |
|---|---|---|---|
| `fuel` | Benzinării | Fuel Stations | `amenity=fuel` |
| `lpg` | GPL (Autogas) | LPG (Autogas) | `amenity=fuel` + `fuel:lpg=yes` |
| `ev_charging` | Stații Încărcare EV | EV Charging Stations | `amenity=charging_station` |
| `parking_large` | Parcări Mari & Park+Ride | Large Parking & Park+Ride | `amenity=parking` cu nume, `park_ride` sau capacitate >= 100 |
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

## 4. Aplicația Web Next.js

Folderul `web/` conține aplicația Next.js statică:

```bash
cd web
npm install
npm run dev     # Deschide serverul local la http://localhost:3000
npm run test    # Rulează testele Vitest (4 teste trecute)
npm run build   # Creează exportul static de producție pentru Vercel
```

---

## 5. Procedura de Import pe RNS 510

1. Copiați fișierele `.asc` pe un **card SD formatat FAT32** (max 32GB) într-un folder numit `PersonalPOI` (sau în rădăcina cardului).
2. Introduceți cardul în aparat.
3. Apăsați **NAV** &rarr; **Destinații speciale proprii (Personal POI)** &rarr; **Importare** &rarr; **Import în baza de date**.
4. Ghid detaliat: [docs/IMPORT_RO.md](docs/IMPORT_RO.md) | [docs/IMPORT_EN.md](docs/IMPORT_EN.md).

---

## 6. Licență și Atribuire

- **Cod Sursă:** [Licența MIT](LICENSE).
- **Date Cartografice:** © Contribuitorii OpenStreetMap, sub licența [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/).
