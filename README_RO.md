# RNS 510 POI Forge

**Română** | [English](README.md)

Soluție open-source pentru generarea de pachete de puncte de interes (Personal POI) pentru unitățile de navigație Volkswagen **RNS 510** (și Škoda Columbus / SEAT Media System) direct din datele OpenStreetMap.

> [!WARNING]
> **FORMAT NECONFIRMAT PE UNITATE**: Sintaxa fișierelor `.asc` și regulile de import se bazează momentan pe convențiile comunității auto și **nu au fost încă validate pe o unitate RNS 510 fizică**. Consultați ghidul [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) pentru a genera fișiere de test și a le proba pe unitatea dumneavoastră.

---

## Declinarea Responsabilității (Disclaimer)

Acest proiect este **neoficial și nu este afiliat cu Volkswagen AG**, Škoda Auto, SEAT S.A. sau oricare dintre filialele acestora. Importarea fișierelor POI se face pe propria răspundere. Datele OpenStreetMap sunt colectate de voluntari și pot conține erori, omisiuni sau date învechite.

**Camerele radar și sistemele de detecție a vitezei NU sunt incluse**, din cauza legislațiilor diferite din țările europene privind aceste dispozitive. Niciun fișier de firmware sau hartă de navigație nu este găzduit sau distribuit în acest proiect.

---

## Funcționalități

- **Procesare automată OpenStreetMap:** Extrage POI-uri pe țări și categorii folosind extrasele Geofabrik.
- **Generator ASC configurabil:** Modul flexibil controlat prin `config/format.yml` (ordinea coordonatelor, set de caractere CP1250 / CP1252 / UTF-8, transliterare diacritice).
- **Utilitar de testare hardware:** Comandă dedicată `poi-forge probe-file` pentru generarea de mostre cu cazuri limită (diacritice românești `ș, ț, ă, â, î`, nume lungi, ghilimele) și matrice completă de formate.
- **Automatizare CI/CD:** Flux GitHub Actions pentru reconstruirea lunară a pachetelor.
- **Aplicație web statică:** Interfață web rapidă pentru descărcarea pachetelor sau împachetarea directă în browser într-o arhivă ZIP.

---

## Pasul Curent (Faza 0: Testarea Formatului)

Înainte de a genera pachete complete pentru toată țara, trebuie confirmat formatul exact pe navigația mașinii:

```bash
# Clonează depozitul
git clone https://github.com/your-username/rns510-poi-forge.git
cd rns510-poi-forge

# Creează și activează mediul virtual
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalează pachetul în mod editabil
pip install -e ".[dev]"

# Generează fișierul de probă și matricea de formate
poi-forge probe-file --out probe.asc --generate-matrix
```

Urmați instrucțiunile detaliate din [docs/FORMAT_PROBE.md](docs/FORMAT_PROBE.md) pentru copierea fișierelor pe cardul SD și importul pe unitatea RNS 510.

---

## Licență și Atribuire

- **Cod sursă:** Licență [MIT](LICENSE).
- **Date:** Datele POI extrase din OpenStreetMap sunt licențiate sub [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1.0/).
- Atribuire obligatorie: **© OpenStreetMap contributors** ([https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)).
