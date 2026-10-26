# RNS 510 Personal POI Format Probe Guide
# Ghid de Testare si Validare a Formatului POI pe RNS 510

[English](#english-version) | [Română](#versiunea-in-limba-romana)

---

## Versiunea in limba romana

### 1. Context si Importanta Testului

Unitatea multimedia **Volkswagen RNS 510** (cunoscuta si ca Skoda Columbus sau SEAT Media System) suporta importul de puncte de interes personalizate (Personal POI) de pe un card SD prin fisiere text cu extensia `.asc`.

Cu toate acestea, **specificatiile exacte nu sunt documentate oficial de producator**:
- Ordinea coordonatelor (Longitudine, Latitudine vs. Latitudine, Longitudine);
- Delimitatorul acceptat (virgula, punct si virgula, tab);
- Suportul pentru caractere speciale si diacritice romanesti (`ș`, `ț`, `ă`, `â`, `î`);
- Setul de caractere (CP1250, CP1252, UTF-8);
- Limita de caractere pentru denumire si descriere;
- Numarul maxim de POI-uri pe fisier (limite de memorie si stabilitate);
- Structura folderelor pe cardul SD (`/` radacina vs. `/PersonalPOI/`).

Pana cand acesti parametri nu sunt confirmati pe un aparat fizic, **toate fisierele generate sunt marcate ca `UNVERIFIED` (neconfirmate)**.

---

### 2. Echipament Necesar

1. Unitate **VW RNS 510** / Skoda Columbus instalata pe masina (sau pe banc de test).
2. Card **SD / SDHC** (capacitate recomandata: 2GB - 32GB), formatat **FAT32**.
3. Un computer cu Python pentru a rula utilitarul de test sau pentru a copia fisierele.

---

### 3. Pasul 1: Generarea Fisierelor de Test (Probe)

Ruleaza comanda CLI pentru a genera fisierul de proba implicit sau matricea completa de variante:

```bash
# Genereaza fisierul standard de 5 POI-uri centrat pe Bucuresti
python -m poi_forge.cli probe-file --out probe.asc

# SAU genereaza matricea completa de formate (recomandat!)
python -m poi_forge.cli probe-file --out probe.asc --generate-matrix

# Daca doresti alte coordonate (ex: Cluj-Napoca: 46.7712, 23.6236)
python -m poi_forge.cli probe-file --lat 46.7712 --lon 23.6236 --out probe.asc
```

Optiunea `--generate-matrix` creeaza in folderul `probe_matrix/` fisiere cu variatiuni:
- `01_default_lon_lat_comma_quoted.asc`
- `02_lat_lon_comma_quoted.asc`
- `03_lon_lat_tab_quoted.asc`
- `04_lon_lat_semicolon_quoted.asc`
- `05_lon_lat_comma_unquoted.asc`
- `06_utf8_encoding.asc`
- `07_cp1250_with_diacritics.asc`
- `08_lf_line_endings.asc`

---

### 4. Pasul 2: Pregatirea Cardului SD

1. Formateaza cardul SD in format **FAT32** (dimensiune alocare standard 4096 bytes).
2. Creeaza pe card urmatoarea structura:
   - Copiaza `probe.asc` direct in radacina cardului (`SD:\probe.asc`).
   - Creeaza un folder numit `PersonalPOI` si copiaza si acolo fisierul (`SD:\PersonalPOI\probe.asc`).
   - Daca testezi fisierele din matrice, adauga-le pe rand sau in subfoldere pentru a vedea cum reactioneaza unitatea.

---

### 5. Pasul 3: Procedura de Import pe RNS 510

1. Pune contactul sau porneste unitatea RNS 510.
2. Introdu cardul SD in slotul frontal al unitatii.
3. Apasa butonul fizic **NAV** (Navigatie).
4. Acceseaza meniul:
   - **My special destinations (Personal POI)** / *Destinatii speciale proprii*
   - Apoi selecteaza: **Import** / *Importare*
   - Selecteaza: **Import into database** / *Import in baza de date*
5. Confirma procesul de import.

---

### 6. Chestionar de Observatii (Ce trebuie notat)

Cand testezi, urmareste si noteaza urmatoarele puncte:

| Nr. | Intrebare | Rezultat constatat |
|---|---|---|
| 1 | Unitatea a gasit fisierul? Din radacina sau din folderul `PersonalPOI`? | |
| 2 | A aparut mesaj de eroare la import? Daca da, ce text exact a afisat? | |
| 3 | POI-urile apar pe harta in locatia corecta? Daca pinii apar in ocean/Africa, coordonatele sunt inversate (Lat/Lon in loc de Lon/Lat). | |
| 4 | Cum se vad diacriticele romanesti (`ș`, `ț`, `ă`, `â`, `î`)? Sunt afisate corect, inlocuite cu litere simple (`s, t, a, i`) sau caractere ciudate (`?`, semne chinezesti)? | |
| 5 | POI-ul cu numele lung (>60 caractere) a fost trunchiat? La cate caractere aproximativ? | |
| 6 | Ghilimelele si virgulele din denumire au provocat erori sau au fost afisate corect? | |
| 7 | Campul "Descriere" este vizibil in meniul de detalii al POI-ului? | |

#### Teste de volum (limite practice):
Dupa ce formatul de baza functioneaza, testeaza capacitatea maxima generand fisiere sintetice:
```bash
# Test 1.000 POI-uri
python -m poi_forge.cli probe-file --preset grid -n 1000 --out stress_1k.asc

# Test 10.000 POI-uri
python -m poi_forge.cli probe-file --preset grid -n 10000 --out stress_10k.asc
```
Noteaza daca unitatea se blocheaza, daca importul dureaza excesiv sau daca exista o limita maxima admisa de puncte de interes.

---

### 7. Pasul 4: Actualizarea Configuratiei `config/format.yml`

Dupa ce ai identificat combinatia exacta care functioneaza pe aparatul tau:
1. Deschide `config/format.yml`.
2. Actualizeaza parametrii confirmati (`coordinate_order`, `separator`, `charset`, `line_endings`, etc.).
3. Seteaza `verified: true`.
4. Completeaza campul `verification_note` cu specificatiile hardware:
   ```yaml
   verified: true
   verification_note: "Verified on VW RNS 510 HW 09, SW 5238, Maps V17 (East Europe). SD Card FAT32, /PersonalPOI folder."
   ```

---
---

## English Version

### 1. Context and Objective

The **Volkswagen RNS 510** (and Skoda Columbus / SEAT Media System) head unit can import custom Personal POIs from an SD card using plain text `.asc` files.

However, **the exact file specification is not officially documented by VW**:
- Coordinate ordering (Lon,Lat vs Lat,Lon);
- Field separator (comma, tab, semicolon);
- Text quoting and quote escaping;
- Character set and diacritics support (CP1250, CP1252, UTF-8);
- Field length limits (max name and description lengths);
- POI capacity limits per file;
- SD card directory location (root `/` vs `/PersonalPOI/`).

Until confirmed on physical hardware, all generated data packages remain marked as **`UNVERIFIED`**.

---

### 2. Requirements

1. A VW RNS 510 / Skoda Columbus navigation unit installed in a car or test bench.
2. An SD or SDHC memory card (2GB - 32GB recommended), formatted as **FAT32**.
3. A computer to run the CLI and write to the SD card.

---

### 3. Step 1: Generate Probe Files

Run the CLI command:

```bash
# Generate default 5-POI probe file
python -m poi_forge.cli probe-file --out probe.asc

# Generate the full matrix of format variants (recommended!)
python -m poi_forge.cli probe-file --out probe.asc --generate-matrix

# Custom center coordinates
python -m poi_forge.cli probe-file --lat 44.4323 --lon 26.1063 --out probe.asc
```

---

### 4. Step 2: Prepare the SD Card

1. Format the SD card as **FAT32**.
2. Copy `probe.asc` to:
   - Root of SD card: `SD:\probe.asc`
   - A folder named `PersonalPOI`: `SD:\PersonalPOI\probe.asc`
3. If using `--generate-matrix`, try the files one by one to determine which syntax variant the RNS 510 accepts.

---

### 5. Step 3: Import Procedure on RNS 510

1. Power on the RNS 510 unit.
2. Insert the SD card into the front slot.
3. Press **NAV**.
4. Navigate to:
   - **My special destinations (Personal POI)**
   - **Import**
   - **Import into database**
5. Observe the import dialog and confirmation.

---

### 6. Observation Checklist

1. **File Detection:** Was `probe.asc` detected in the root directory or in `/PersonalPOI/`?
2. **Coordinates:** Do map pins appear at the intended location, or inverted (e.g. in the Indian Ocean / Somalia)?
3. **Diacritics & Special Characters:** How are characters like `ș`, `ț`, `ă`, `â`, `î` displayed? Clean, transliterated, or corrupted?
4. **Name Length:** Is the long name truncated? Count the displayed character limit.
5. **Quotes & Commas:** Did embedded quotes or commas cause line parsing errors?
6. **Stress Testing:** Generate and test 1,000 and 10,000 POI files:
   ```bash
   python -m poi_forge.cli probe-file --preset grid -n 1000 --out stress_1k.asc
   python -m poi_forge.cli probe-file --preset grid -n 10000 --out stress_10k.asc
   ```

---

### 7. Step 4: Update `config/format.yml`

Once confirmed:
1. Update `config/format.yml` with your findings.
2. Set `verified: true`.
3. Add your hardware/firmware details in `verification_note`:
   ```yaml
   verified: true
   verification_note: "Verified on VW RNS 510 HW 09, FW 5238, Maps V17."
   ```
