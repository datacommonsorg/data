# Indonesia Census - Demographic Population (`Indonesia_Census_Demographics`) StatVar Import

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Demographics`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/`
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/domain/0000/var/{2790,2791,2792}/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/{2790,2791,2792}/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Geographic Coverage:**
  * Country (`country/IDN`)
  * 38 Provinces (`AdministrativeArea1`, `wikidataId/Q...`, including the 4 new Papua provinces split in late 2022: `Southwest Papua`, `South Papua`, `Central Papua`, `Highland Papua`)
  * 514 Regencies and Cities (`AdministrativeArea2` / `City`, `Kabupaten` / `Kota`, `wikidataId/Q...`)

---

## 2. Datasets & Consolidation Architecture

This import consolidates the **403 legacy Demographic CSVs** (`1971–2022`) from `/cns/jv-d/home/datcom/v3_mcf/country/indonesia/` into 2 historical baseline CSVs and automates the `2023–2025+` refresh from BPS WebAPI:

1. **Historical Baseline (1971–2022)** (`consolidate_historical.py`):
   * `idn_population_historical_1971_2022.csv`: Consolidated from 218 legacy Total Population CSVs (8 AA1 + 210 AA2).
   * `idn_age_gender_historical_2010_2022.csv`: Consolidated from 185 legacy Age & Gender CSVs (5 AA1 + 180 AA2).
   * Shared template MCF: `common_tmcf.tmcf`.

2. **Automated BPS WebAPI Refresh (2023–2025+)** (`download.py` + `stat_var_processor.py`):
   * **BPS Variable IDs**:
     * `var_id=2790`: *Jumlah Penduduk menurut Kabupaten/Kota dan Kelompok Umur* (Total Population by Regency/City and Age Group)
     * `var_id=2791`: *Jumlah Penduduk Laki-Laki menurut Kabupaten/Kota dan Kelompok umur* (Male Population by Regency/City and Age Group)
     * `var_id=2792`: *Jumlah Penduduk Perempuan menurut Kabupaten Kota dan Kelompok Umur* (Female Population by Regency/City and Age Group)
   * **Generated Input Files**:
     * `input_files/idn_population_2023_2025.csv` (processed with `pvmaps/idn_population_pvmap.csv`)
     * `input_files/idn_age_gender_2023_2025.csv` (processed with `pvmaps/idn_age_gender_pvmap.csv`)
   * **StatVars (`52` total)**:
     * `dcid:Count_Person`
     * `dcid:Count_Person_Male`, `dcid:Count_Person_Female`
     * 16 five-year age brackets (`0To4Years` .. `75OrMoreYears`) across Total, Male, and Female (`Count_Person_{Age}`, `Count_Person_{Age}_Male`, `Count_Person_{Age}_Female`).

---

## 3. How to Run

1. **Download and preprocess the source data from BPS WebAPI into `input_files/`:**
   ```bash
   python3 statvar_imports/indonesia_census/demographic_population/download.py \
     --output_dir=statvar_imports/indonesia_census/demographic_population/input_files
   ```

2. **Run the full pipeline (`run.sh`) or `stat_var_processor.py` directly:**
   ```bash
   bash statvar_imports/indonesia_census/demographic_population/run.sh
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/demographic_population -p "*_test.py"
   ```
