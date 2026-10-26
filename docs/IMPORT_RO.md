# Ghid de Import Personal POI pe RNS 510 (Română)

Acest ghid explică pas cu pas cum se importă pachetele de puncte de interes (Personal POI) în format `.asc` generate de **rns510-poi-forge** pe sistemele de navigație Volkswagen **RNS 510**, **Škoda Columbus** și **SEAT Media System**.

---

## 1. Cerințe și Echipament

- Unitate multimedia **Volkswagen RNS 510**, **Škoda Columbus** sau **SEAT Media System**.
- Card de memorie **SD sau SDHC** (capacitate recomandată: între 2 GB și 32 GB), formatat **FAT32**.
  > [!TIP]
  > Adaptoarele MicroSD către SD funcționează fără probleme, dacă este respectată formatarea FAT32 (unitate de alocare standard 4096 bytes).
- Fișierele `.asc` descărcate din secțiunea de versiuni (Releases), generate local prin CLI sau descărcate din aplicația web.

---

## 2. Pregătirea Cardului SD

1. **Formatarea cardului:** Asigurați-vă că este formatat în sistemul de fișiere **FAT32** (nu exFAT sau NTFS).
2. **Structura folderelor:** În funcție de versiunea de firmware a aparatului RNS 510:
   - Recomandat: Creați un folder numit `PersonalPOI` în rădăcina cardului SD:
     ```
     SD:\
     ├── PersonalPOI\
     │   ├── romania_fuel_001.asc
     │   ├── romania_ev_charging_001.asc
     │   └── romania_pharmacy_001.asc
     └── ATTRIBUTION.txt
     ```
   - Dacă unitatea nu detectează fișierele din folderul `/PersonalPOI/`, copiați fișierele `.asc` direct în rădăcina cardului (`SD:\romania_fuel_001.asc`).

---

## 3. Procedura de Import pe Unitatea RNS 510

1. **Porniți unitatea** (puneți contactul mașinii).
2. **Introduceți cardul SD** în slotul de sub ecran.
3. Apăsați butonul fizic **NAV** (Navigație).
4. Apăsați butonul fizic **Setup** sau atingeți pictograma de setări de pe ecran.
5. În meniul de setări Navigație, navigați la:
   - **Navigație** (Navigation)
   - **Destinații speciale proprii** (My special destinations / Personal POI)
   - **Importare** (Import)
   - **Import în baza de date** (Import into database)
6. Unitatea va citi cardul SD și vă va solicita confirmarea pentru a adăuga punctele de interes în baza de date de pe hard disk-ul intern (HDD).
7. Confirmați importul și așteptați finalizarea barei de progres.

---

## 4. Activarea Afișării POI-urilor pe Hartă

După finalizarea importului, trebuie să bifați categoriile dorite pentru a fi desenate pe hartă:

1. Reveniți la vizualizarea hărții apăsând **NAV**.
2. Atingeți butonul de setări hartă / ecran.
3. Selectați **Afișare destinații speciale** (Select POI categories).
4. Derulați până la noile categorii importate (ex: *Benzinării*, *Stații Încărcare EV*, *Farmacii*) și bifați căsuțele corespunzătoare.
5. Punctele de interes vor fi afișate acum pe traseu!

---

## 5. Ghid de Depanare (Troubleshooting)

| Problemă | Cauză posibilă | Rezolvare |
|---|---|---|
| "Nu s-au găsit date pe cardul SD" | Folder greșit sau format card | Testați plasarea fișierelor atât în `SD:\PersonalPOI\`, cât și direct în rădăcina cardului `SD:\`. Verificați formatul FAT32. |
| Cardul SD nu este recunoscut | Capacitate > 32GB sau format exFAT | Folosiți un card SDHC de maxim 32GB formatat FAT32. |
| Punctele apar în ocean sau Africa | Coordonate inversate | Rulați `poi-forge probe-file --generate-matrix` pentru a testa ordinea Lon/Lat conform `docs/FORMAT_PROBE.md`. |
| Diacriticele românești sunt ilizibile | Setul de caractere nu este suportat | Păstrați opțiunea implicită `ascii_transliterate: true` din `config/format.yml` pentru caractere sigure. |
| Unitatea se blochează la import | Prea multe puncte într-un fișier | Fisierele sunt împărțite automat la 5.000 de puncte. Dacă unitatea are firmware vechi, micșorați pragul la 2.000 în `config/format.yml`. |

---

## 6. Declinarea Responsabilității

Acest software este neoficial și nu este afiliat cu Volkswagen AG sau mărcile grupului. Importul fișierelor se face pe propria răspundere. Datele OpenStreetMap sunt furnizate conform licenței ODbL 1.0.
