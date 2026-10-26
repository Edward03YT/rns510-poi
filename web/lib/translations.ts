import { Language } from "./types";

export interface TranslationDictionary {
  appTitle: string;
  appSubtitle: string;
  unverifiedWarningTitle: string;
  unverifiedWarningBody: string;
  probeGuideLink: string;
  selectCountryTitle: string;
  searchCountryPlaceholder: string;
  noCountriesFound: string;
  dataFrom: string;
  selectCategoriesTitle: string;
  selectAll: string;
  deselectAll: string;
  selectedCount: string;
  downloadSectionTitle: string;
  downloadZipButton: string;
  buildingZip: string;
  individualFiles: string;
  size: string;
  instructionsTab: string;
  aboutTab: string;
  importInstructionsTitle: string;
  importStep1: string;
  importStep2: string;
  importStep3: string;
  importStep4: string;
  importNote: string;
  aboutTitle: string;
  aboutOsm: string;
  aboutOdbl: string;
  aboutSpeedCameras: string;
  aboutDisclaimer: string;
  footerDisclaimer: string;
  footerOsmAttribution: string;
  categories: Record<string, string>;
}

export const translations: Record<Language, TranslationDictionary> = {
  ro: {
    appTitle: "RNS 510 POI Forge",
    appSubtitle: "Pachete Personal POI pentru Volkswagen RNS 510 din date OpenStreetMap",
    unverifiedWarningTitle: "Format neconfirmat pe unitate fizică",
    unverifiedWarningBody:
      "Sintaxa fișierelor ASC și structura cardului SD nu au fost încă validate pe un aparat real RNS 510. Generarea folosește convențiile comunității.",
    probeGuideLink: "Consultă ghidul de testare hardware (FORMAT_PROBE.md)",
    selectCountryTitle: "1. Alege Țara",
    searchCountryPlaceholder: "Caută țară (ex: România, Germania)...",
    noCountriesFound: "Nicio țară găsită.",
    dataFrom: "Date extrase la:",
    selectCategoriesTitle: "2. Alege Categoriile",
    selectAll: "Selectează tot",
    deselectAll: "Deselectează tot",
    selectedCount: "puncte de interes selectate",
    downloadSectionTitle: "3. Descarcă Pachetele",
    downloadZipButton: "Descarcă Selecția ca ZIP (cu ATTRIBUTION.txt)",
    buildingZip: "Se generează arhiva în browser...",
    individualFiles: "Descărcare fișiere individuale .ASC:",
    size: "Mărime",
    instructionsTab: "Ghid de Import pe RNS 510",
    aboutTab: "Despre & Limitări",
    importInstructionsTitle: "Cum se importă pe unitatea RNS 510:",
    importStep1: "1. Copiază fișierele .asc pe un card SD / SDHC (max 32GB) formatat FAT32, direct în rădăcină sau în folderul 'PersonalPOI'.",
    importStep2: "2. Introdu cardul SD în slotul frontal al unității RNS 510.",
    importStep3: "3. Apasă butonul NAV, apoi accesează: Destinații speciale proprii (My special destinations / Personal POI).",
    importStep4: "4. Selectează: Importare -> Import în baza de date și confirmă procesul.",
    importNote: "Notă: Denumirile meniurilor pot varia în funcție de limba sistemului și versiunea de firmware.",
    aboutTitle: "Despre Date și Limitări",
    aboutOsm: "Datele provin din OpenStreetMap (OSM) prin extrasele furnizate de Geofabrik. Densitatea și acuratețea pot varia în funcție de regiune.",
    aboutOdbl: "Datele sunt publicate sub licența Open Database License (ODbL) 1.0. © Contribuitorii OpenStreetMap.",
    aboutSpeedCameras: "Important: Camerele radar și radarele fixe NU sunt incluse, conform legislațiilor europene în vigoare.",
    aboutDisclaimer: "Acest utilitar este neoficial și nu este afiliat cu Volkswagen AG sau mărcile asociate. Utilizarea fișierelor se face pe propria răspundere.",
    footerDisclaimer: "Proiect neoficial, neafiliat cu Volkswagen AG. Importul fișierelor POI se face pe răspunderea utilizatorului.",
    footerOsmAttribution: "Date cartografice © Contribuitorii OpenStreetMap, sub licența ODbL.",
    categories: {
      fuel: "Benzinării",
      lpg: "GPL (Autogas)",
      ev_charging: "Stații Încărcare EV",
      parking_large: "Parcări Mari & Park+Ride",
      truck_parking: "Parcări Camioane (TIR)",
      rest_area: "Zone Odihnă & Servicii Autostradă",
      pharmacy: "Farmacii",
      atm: "Bancomate (ATM)",
      hospital: "Spitale & Urgențe",
      car_repair: "Service Auto",
      tyres: "Vulcanizări & Anvelope",
      car_wash: "Spălătorii Auto",
      camping: "Camping & Rulote",
      supermarket: "Supermarketuri",
      border_crossing: "Puncte Trecere Frontieră",
    },
  },
  en: {
    appTitle: "RNS 510 POI Forge",
    appSubtitle: "Personal POI packages for Volkswagen RNS 510 navigation units from OpenStreetMap",
    unverifiedWarningTitle: "Format Not Yet Verified on Physical Unit",
    unverifiedWarningBody:
      "The ASC file syntax and SD card folder structure have not yet been validated on a physical RNS 510 unit. Files are built using community defaults.",
    probeGuideLink: "Read the Hardware Probe Guide (FORMAT_PROBE.md)",
    selectCountryTitle: "1. Select Country",
    searchCountryPlaceholder: "Search country (e.g. Romania, Germany)...",
    noCountriesFound: "No countries found.",
    dataFrom: "Data from:",
    selectCategoriesTitle: "2. Select Categories",
    selectAll: "Select all",
    deselectAll: "Deselect all",
    selectedCount: "POIs selected",
    downloadSectionTitle: "3. Download Packages",
    downloadZipButton: "Download Selection as ZIP (with ATTRIBUTION.txt)",
    buildingZip: "Building ZIP in browser...",
    individualFiles: "Download individual .ASC files:",
    size: "Size",
    instructionsTab: "Import Instructions",
    aboutTab: "About & Limitations",
    importInstructionsTitle: "How to import on your RNS 510 head unit:",
    importStep1: "1. Copy the .asc files to a FAT32-formatted SD card (max 32GB), either in the root directory or in a folder named 'PersonalPOI'.",
    importStep2: "2. Insert the SD card into the front slot of your RNS 510 unit.",
    importStep3: "3. Press the physical NAV button, then navigate to: My special destinations (Personal POI).",
    importStep4: "4. Select: Import -> Import into database and confirm the import dialog.",
    importNote: "Note: Menu item names may vary depending on the unit's active language and firmware version.",
    aboutTitle: "About & Limitations",
    aboutOsm: "Data is sourced from OpenStreetMap (OSM) via Geofabrik country extracts. Density and accuracy may vary by country and category.",
    aboutOdbl: "POI databases are made available under the Open Database License (ODbL) 1.0. © OpenStreetMap contributors.",
    aboutSpeedCameras: "Speed cameras and enforcement radar warnings are strictly excluded due to European legal regulations.",
    aboutDisclaimer: "This project is unofficial and not affiliated with Volkswagen AG. Importing POI files is at the user's own risk.",
    footerDisclaimer: "Unofficial project, not affiliated with Volkswagen AG. POI import is performed at your own risk.",
    footerOsmAttribution: "Map data © OpenStreetMap contributors, licensed under ODbL.",
    categories: {
      fuel: "Fuel Stations",
      lpg: "LPG (Autogas)",
      ev_charging: "EV Charging Stations",
      parking_large: "Large Parking & Park+Ride",
      truck_parking: "Truck Parking",
      rest_area: "Rest Areas & Services",
      pharmacy: "Pharmacies",
      atm: "ATMs",
      hospital: "Hospitals & Emergency",
      car_repair: "Car Repair",
      tyres: "Tyre Shops",
      car_wash: "Car Washes",
      camping: "Camping & Caravan Sites",
      supermarket: "Supermarkets",
      border_crossing: "Border Crossings",
    },
  },
};
