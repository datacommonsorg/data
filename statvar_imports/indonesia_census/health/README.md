# Indonesia Census - Health (`Indonesia_Census_Health`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Health`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/` *(Note: BPS HTML web pages including `https://www.bps.go.id/` and `https://www.bps.go.id/en/statistics-table?subject=519` return HTTP 403 `cf-mitigated: challenge` from GCP datacenter IPs due to Cloudflare bot protection; automated data ingestion exclusively uses the official BPS WebAPI at `https://webapi.bps.go.id/v1/api/` — developer portal: `https://webapi.bps.go.id/developer/`.)*
* **Source Data URL:** `https://webapi.bps.go.id/developer/` *(BPS WebAPI developer portal; human-browsable HTML table catalog: `https://www.bps.go.id/en/statistics-table?subject=519`)*
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/domain/0000/var/{var_id}/lang/eng/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/domain/0000/var/{var_id}/th/{th_ids}/lang/eng/`
  * `https://webapi.bps.go.id/v1/api/view/domain/0000/model/statictable/lang/ind/id/{table_id}/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, matching `Indonesia_Census_Demographics` and `auto1w`; `P1Y` source release frequency)
* **Date Range in KG:** `2000` – `2025`
* **Total Observations:** `33,757` observations across `61` `StatisticalVariable` nodes and `553` unique place DCIDs (`553` place-name rows in `indonesia_health_places_resolved.csv` covering `country/IDN`, `38` Provinces, and `514` Regencies/Cities).

---

## 2. Datasets Covered

1. **Mortality**
   - **Life Expectancy by Regency/City & Gender (`var_id=455`, `2010–2024`)**: `input_files/life_expectancy_by_regency_city_and_gender.csv` (`LifeExpectancy_Person_Male`, `LifeExpectancy_Person_Female`).
   - **Infant Mortality Rate by Province (`var_id=1584`, `2012, 2017`)**: `input_files/infant_mortality_rate_by_province.csv` (`Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth`).
2. **Disease**
   - **Disease Cases by Province (`var_id=42`, `2007–2015`)**: `input_files/disease_cases_by_province.csv` (`8` disease incident count StatVars: Malaria, Tuberculosis, Pneumonia, Leprosy, Tetanus Neonatorum, Measles, Diarrhea, DHF).
   - **Malaria Incidence per 1,000 Population (`var_id=1393`, `2010–2021`)**: `input_files/malaria_incidence_per_1000_population.csv` (`Count_MedicalConditionIncident_ConditionMalaria_AsAFractionOf_Count_Person`).
   - **Tuberculosis Incidence per 100,000 Population (`var_id=1763`, `2015–2021`)**: `input_files/tuberculosis_incidence_per_100000_population.csv` (`Count_MedicalConditionIncident_ConditionTuberculosis_AsAFractionOf_Count_Person`).
   - **AIDS Cases by Province (`table_id=1569`, `2008–2012`)**: `input_files/aids_cases_by_province.csv` (`5` AIDS StatVars: `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase`, `Annual_CumulativeCount_MedicalConditionIncident_AIDS_ConfirmedCase`, `Annual_Count_MedicalConditionIncident_AIDS_PatientDeceased`, `Annual_Count_MedicalConditionIncident_AIDS_NewlyConfirmedCase`, and `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase_AsAFractionOf_Count_Person`).
   - **Health Complaint by Province (`table_id=1617`, `2009–2025`)**: `input_files/health_complaint_by_province.csv` (`6` StatVars by sex and urban/rural classification).
3. **Risk Factors**
   - **Smoked Tobacco Aged 15+ by Province (`var_id=1435`, `2015–2025`)**: `input_files/smoked_tobacco_by_province.csv` (`Count_Person_15OrMoreYears_Smoking_AsFractionOf_Count_Person_15OrMoreYears`).
   - **Obesity Prevalence Aged 18+ by Urban/Rural (`var_id=1481`, `2007–2018`)**: `input_files/obesity_prevalence_by_urban_rural.csv` (`3` StatVars: `Percent_Person_Obesity`, `Count_Person_18OrMoreYears_Obesity_Urban_AsAFractionOf_Count_Person_18OrMoreYears_Urban`, `Count_Person_18OrMoreYears_Obesity_Rural_AsAFractionOf_Count_Person_18OrMoreYears_Rural`).
   - **Obesity Prevalence Aged 18+ by Sex (`var_id=1781`, `2007–2018`)**: `input_files/obesity_prevalence_by_gender.csv` (`2` StatVars: `Count_Person_18OrMoreYears_Male_Obesity_AsAFractionOf_Count_Person_18OrMoreYears_Male`, `Count_Person_18OrMoreYears_Female_Obesity_AsAFractionOf_Count_Person_18OrMoreYears_Female`).
   - **Contraception Method Among Married Women Aged 15–49 (`var_id=218`, `2000–2024`)**: `input_files/contraception_method_by_province.csv` (`Count_Person_15To49Years_ContraceptionMethod_Female_Married_AsAFractionOf_Count_Person_15To49Year_Female_Married`).
4. **Health Service Utilization**
   - **General Hospitals, Special Hospitals, & Public Health Centers (`var_id=232`, `2012–2015`)**: `input_files/hospitals_and_public_health_centers_by_province.csv` (`3` StatVars).
   - **Unmet Need of Health Services by Province (`var_id=1402`, `2015–2025`)**: `input_files/unmet_need_of_health_services_by_province.csv` (`Count_HealthEstablishment_WithUnmetNeed`).
   - **Outpatient Treatment by Province & Sex (`table_id=1620`, `2009–2025`)**: `input_files/outpatient_treatment_male_by_province.csv` and `input_files/outpatient_treatment_female_by_province.csv` (`26` StatVars across 13 facility types and sex).

---

## 3. Custom Preprocessing, Place Resolution & Refresh Notes

- **BPS WebAPI Normalization (`download.py`)**:
  - Archives raw JSON responses in `raw_files/` and writes normalized CSV tables into `input_files/`.
  - Prefixes 4-digit year column headers as `Year <YYYY>` (`Year 2000`–`Year 2030`) so `stat_var_processor.py` treats year headers purely as column headers and never matches data cells whose numeric values fall between `2000` and `2030` (preserving valid disease counts such as `2015`, `2023`, and `2026`).
  - Normalizes Indonesian dot and space thousands separators (e.g., `4.969` -> `4969`, `2 727` -> `2727`) and comma decimal separators (e.g., `11,34` -> `11.34`), normalizes abbreviated province names (`KEP. BANGKA BELITUNG` -> `Kepulauan Bangka Belitung`, `Kep. Riau` -> `Kepulauan Riau`), and strips redundant `Jumlah` (`100.00%` total) columns in static table `1620`.
- **Canonical StatVar Resolution & Remapping (`statvar_remap.csv` & `--existing_statvar_mcf`)**:
  - Uses `statvar_remap.csv` to map generated StatVars to canonical `Indonesia_Census` / legacy CNS StatVar DCIDs for Smoked Tobacco (`Count_Person_15OrMoreYears_Smoking_AsFractionOf_Count_Person_15OrMoreYears`), Obesity (`Percent_Person_Obesity`, `Count_Person_18OrMoreYears_{Male,Female,Urban,Rural}_Obesity_...`), Contraception (`Count_Person_15To49Years_ContraceptionMethod_Female_Married_AsAFractionOf_Count_Person_15To49Year_Female_Married`), and Doctor Practice / Polyclinic (`Count_HealthEstablishment_{Male,Female}_DoctorPracticeOrPolyclinic` -> `Count_HealthEstablishment_{Male,Female}_DoctorsPracticeOrPolyclinic`).
  - Resolves existing standard KG StatVars such as Infant Mortality Rate (`Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth`), Life Expectancy, Disease Cases, Malaria Incidence, and Tuberculosis Incidence via `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.
  - Uses single non-concatenated `Or`-joined `HealthEstablishmentTypeEnum` nodes (`DoctorPracticeOrPolyclinic`, `PracticingDoctorOrMidwife`, `JointClinicOrDoctorPractice`, `VillageMaternityClinicOrIntegratedServiceOrMedicalCenter`, `PracticeTraditionalOrAlternativeMedicine`) in `indonesia_health_schema.mcf` (matching `Provisional_Indonesia_Health_Schema.mcf`). `manifest.json` scopes generated node MCFs to `output_files/*_stat_vars.mcf` to avoid re-ingesting auto-generated `Property` nodes from `*_stat_vars_schema.mcf`; once `Provisional_Indonesia_Health_Schema.mcf` is submitted in google3, `indonesia_health_schema.mcf` can be removed from `node_mcf`.
- **Place Resolution & One-Time Baseline Migrations (`2024_04_02_cns_baseline`)**:
  - Includes the 4 newly established Papua provinces (`wikidataId/Q115253263` Papua Barat Daya, `wikidataId/Q112810104` Papua Pegunungan, `wikidataId/Q61439296` Papua Selatan, and `wikidataId/Q12486766` Papua Tengah).
  - Disambiguates Gorontalo Province (`vervar['val'] = '7500'`, `wikidataId/Q5067`) vs. Gorontalo Regency (`vervar['val'] = '7502'`, mapped to `Kab. Gorontalo` / `wikidataId/Q24578250`) by BPS `vervar['val']` code.
  - When diffed against the unmodified `/cns/jv-d/home/datcom/v3_mcf/country/indonesia/20240402/` Health nodes (`28,122` SVOs, syntax-normalized `unit: "Percent"` -> `unit: dcid:Percent`) plus the `582` legacy production `dc/base/Indonesia_Census` Health rows (`28,704` total baseline SVOs), `15,328` non-migrated observations match identically (`0` modified, `0` unexpected deletions) and `13,376` expected one-time migration diffs occur (`458` DCID/place deletions + `12,918` Life Expectancy unit facet-key migrations; `+18,429` added -> `33,757` total SVOs):
    - **`315` Smoked Tobacco DCID migration deletions**: Legacy `20240402` CNS nodes used `Percent_Person_CountPerson15OrMoreYears_TobaccoSmoking` (`2015–2023`), which is migrated to the canonical production `Indonesia_Census` DCID `Count_Person_15OrMoreYears_Smoking_AsFractionOf_Count_Person_15OrMoreYears`.
    - **`119` AIDS cumulative case rate DCID migration deletions**: Legacy `20240402` CNS nodes used the contradictory DCID `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase_AsAFractionOf_Annual_Count_MedicalConditionIncident` (`28` in `2008`, `31` in `2009`, `30` in `2010`, `30` in `2011`), which is migrated to `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase_AsAFractionOf_Count_Person` to match `measurementDenominator: dcid:Count_Person` (`per 100,000 population`).
    - **`24` `Siau Tagulandang Biaro` place DCID migration deletions**: Resolves `Siau Tagulandang Biaro` to the canonical Regency node `wikidataId/Q15840` (Siau Tagulandang Biaro Islands Regency) instead of the legacy island-group node `wikidataId/Q26761494` (`LifeExpectancy_Person_Male` and `LifeExpectancy_Person_Female`, `2010–2021`).
    - **`12,918` Life Expectancy unit fixes (`Percent` -> `Years`)**: Corrects the legacy `unit: dcid:Percent` on `LifeExpectancy_Person_Male` and `LifeExpectancy_Person_Female` in `20240402` to `unit: dcid:Years` (counted as delete+add by `import_differ.py` because `unit` is part of the observation facet key; combined with the `24` Siau rows, `6,472` Female + `6,470` Male = `12,942` legacy `Percent` rows are replaced).

---

## 4. How to Run

1. **Configure BPS WebAPI Credentials and Download Source Data:**
   Set the `BPS_API_KEY` environment variable (or pass `--api_key=<KEY>` / `--api_key_gcs_path=<PATH>`):
   ```bash
   export BPS_API_KEY="<YOUR_BPS_API_KEY>"
   python3 statvar_imports/indonesia_census/health/download.py \
     --output_dir=statvar_imports/indonesia_census/health/input_files \
     --raw_output_dir=statvar_imports/indonesia_census/health/raw_files
   ```

2. **Run `stat_var_processor.py` to generate CSV, TMCF, and StatVar/Schema MCF outputs:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/health/input_files/*.csv \
     --pv_map=statvar_imports/indonesia_census/health/indonesia_health_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/health/indonesia_health_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/health/indonesia_health_places_resolved.csv \
     --statvar_dcid_remap_csv=statvar_imports/indonesia_census/health/statvar_remap.csv \
     --existing_schema_mcf=statvar_imports/indonesia_census/health/indonesia_health_schema.mcf \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/health/output_files/indonesia_health_output \
     --output_counters=statvar_imports/indonesia_census/health/counters/indonesia_health_counters.csv
   ```

3. **Run Unit Tests:**
   ```bash
   ./run_tests.sh -p statvar_imports/indonesia_census/health
   ```
