# Indonesia Census - Health (`Indonesia_Census_Health`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Health`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/`
* **Source Data URL:** `https://www.bps.go.id/en/statistics-table?subject=519`
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/domain/0000/var/{var_id}/lang/eng/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/domain/0000/var/{var_id}/th/{th_ids}/lang/eng/`
  * `https://webapi.bps.go.id/v1/api/view/domain/0000/model/statictable/lang/ind/id/{table_id}/`
* **Release Frequency / Refresh Schedule:** Monthly check (`0 9 1 * *`, `P1Y` source release frequency)
* **Date Range in KG:** `2000` – `2025`
* **Total Observations:** `33,757` observations across `61` `StatisticalVariable` nodes and `552` unique place DCIDs (`555` place-name rows in `indonesia_health_places_resolved.csv` covering `country/IDN`, `38` Provinces, and `513` Regencies/Cities).

---

## 2. Datasets Covered

1. **Mortality**
   - **Life Expectancy by Regency/City & Gender (`var_id=455`, `2010–2024`)**: `input_files/life_expectancy_by_regency_city_and_gender.csv` (`LifeExpectancy_Person_Male`, `LifeExpectancy_Person_Female`).
   - **Infant Mortality Rate by Province (`var_id=1584`, `2012, 2017`)**: `input_files/infant_mortality_rate_by_province.csv` (`Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth`).
2. **Disease**
   - **Disease Cases by Province (`var_id=42`, `2007–2015`)**: `input_files/disease_cases_by_province.csv` (`8` disease incident count StatVars: Malaria, Tuberculosis, Pneumonia, Leprosy, Tetanus Neonatorum, Measles, Diarrhea, DHF).
   - **Malaria Incidence per 1,000 Population (`var_id=1393`, `2010–2021`)**: `input_files/malaria_incidence_per_1000_population.csv` (`Count_MedicalConditionIncident_ConditionMalaria_AsAFractionOf_Count_Person`).
   - **Tuberculosis Incidence per 100,000 Population (`var_id=1763`, `2015–2021`)**: `input_files/tuberculosis_incidence_per_100000_population.csv` (`Count_MedicalConditionIncident_ConditionTuberculosis_AsAFractionOf_Count_Person`).
   - **AIDS Cases by Province (`table_id=1569`, `2008–2012`)**: `input_files/aids_cases_by_province.csv` (`5` AIDS StatVars: `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase`, `Annual_CumulativeCount_MedicalConditionIncident_AIDS_ConfirmedCase`, `Annual_Count_MedicalConditionIncident_AIDS_PatientDeceased`, `Annual_Count_MedicalConditionIncident_AIDS_NewlyConfirmedCase`, and `Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase_AsAFractionOf_Annual_Count_MedicalConditionIncident`).
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
  - Normalizes Indonesian dot and space thousands separators (e.g., `4.969` -> `4969`, `2 727` -> `2727`) and comma decimal separators (e.g., `11,34` -> `11.34`), and strips redundant `Jumlah` (`100.00%` total) columns in static table `1620`.
- **Canonical StatVar Remapping (`statvar_remap.csv`)**:
  - Reuses the existing canonical `Indonesia_Census` StatVar DCIDs for Smoked Tobacco (`Count_Person_15OrMoreYears_Smoking_AsFractionOf_Count_Person_15OrMoreYears`), Obesity (`Percent_Person_Obesity`, `Count_Person_18OrMoreYears_{Male,Female,Urban,Rural}_Obesity_...`), Infant Mortality Rate (`Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth`), and AIDS cumulative case rate (`Annual_Count_MedicalConditionIncident_AIDS_ConfirmedCase_AsAFractionOf_Annual_Count_MedicalConditionIncident`).
- **Place Resolution & Historical Baseline Comparison**:
  - Includes the 4 newly established Papua provinces (`wikidataId/Q115253263` Papua Barat Daya, `wikidataId/Q112810104` Papua Pegunungan, `wikidataId/Q61439296` Papua Selatan, and `wikidataId/Q12486766` Papua Tengah).
  - Resolves `Siau Tagulandang Biaro` to the canonical Regency node `wikidataId/Q15840` (Siau Tagulandang Biaro Islands Regency) instead of the legacy island-group node `wikidataId/Q26761494` used in the manual `/cns/jv-d/home/datcom/v3_mcf/country/indonesia/20240402/` snapshot, accounting for 24 place-DCID migration deletions (`LifeExpectancy_Person_Male` and `LifeExpectancy_Person_Female`, `2010–2022`) when diffed against the unmodified `20240402` CNS slice.

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
     --output_path=statvar_imports/indonesia_census/health/output_files/indonesia_health_output
   ```

3. **Run Unit Tests:**
   ```bash
   ./run_tests.sh -p statvar_imports/indonesia_census/health
   ```
