# Indonesia Census - Health (`Indonesia_Census_Health`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Health`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/en/statistics-table?subject=519`
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/view/domain/0000/model/statictable/lang/ind/id/{table_id}/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `2000` – `2025`
* **Total Observations:** `33,475` observations across `61` `StatisticalVariable` nodes and `554` places (`country/IDN`, `38` Provinces, and `514` Regencies/Cities).

---

## 2. Datasets Covered

1. **Mortality**
   - **Life Expectancy by Regency/City & Gender (`var_id=455`, `2010–2024`)**: `input_files/life_expectancy_by_regency_city_and_gender.csv` (`LifeExpectancy_Person_Male`, `LifeExpectancy_Person_Female`).
   - **Infant Mortality Rate by Province (`var_id=2235`, `2020`)**: `input_files/infant_mortality_rate_by_province.csv` (`Count_MortalityEvent_Years0_AsAFractionOf_Count_BirthEvent_LiveBirth`).
2. **Disease**
   - **Disease Cases by Province (`var_id=189`, `2007–2015`)**: `input_files/disease_cases_by_province.csv` (`9` disease incident count StatVars: Malaria, Tuberculosis, Pneumonia, Leprosy, Tetanus Neonatorum, Measles, Diarrhea, DHF).
   - **Malaria Incidence per 1,000 Population (`var_id=1460`, `2015–2025`)**: `input_files/malaria_incidence_per_1000_population.csv` (`Count_MedicalConditionIncident_ConditionMalaria_AsAFractionOf_Count_Person`).
   - **Tuberculosis Incidence per 100,000 Population (`var_id=1267`, `2015–2021`)**: `input_files/tuberculosis_incidence_per_100000_population.csv` (`Count_MedicalConditionIncident_ConditionTuberculosis_AsAFractionOf_Count_Person`).
   - **AIDS Cases by Province (`table_id=1569`, `2008–2012`)**: `input_files/aids_cases_by_province.csv` (`4` AIDS StatVars: confirmed cases, cumulative cases, deaths, new cases, and rate).
   - **Health Complaint by Province (`table_id=1617`, `2009–2025`)**: `input_files/health_complaint_by_province.csv` (`6` StatVars by sex and urban/rural classification).
3. **Risk Factors**
   - **Smoked Tobacco Aged 15+ by Province (`var_id=1435`, `2015–2025`)**: `input_files/smoked_tobacco_by_province.csv` (`Percent_Person_CountPerson15OrMoreYears_TobaccoSmoking`).
   - **Obesity Prevalence Aged 18+ by Urban/Rural (`var_id=1786`, `2007–2018`)**: `input_files/obesity_prevalence_by_urban_rural.csv` (`3` StatVars).
   - **Obesity Prevalence Aged 18+ by Sex (`var_id=1787`, `2007–2018`)**: `input_files/obesity_prevalence_by_gender.csv` (`2` StatVars).
   - **Contraception Method Among Married Women Aged 15–49 (`var_id=133`, `2000–2025`)**: `input_files/contraception_method_by_province.csv` (`Count_Person_Year15To49_ContraceptionMethod_Female_Married_AsAFractionOf_Count_Person_Year15To49_Female_Married`).
4. **Health Service Utilization**
   - **General Hospitals, Special Hospitals, & Public Health Centers (`var_id=205`, `2012–2015`)**: `input_files/hospitals_and_public_health_centers_by_province.csv` (`3` StatVars).
   - **Unmet Need of Health Services by Province (`var_id=1412`, `2015–2025`)**: `input_files/unmet_need_of_health_services_by_province.csv` (`Count_HealthEstablishment_WithUnmetNeed`).
   - **Outpatient Treatment by Province & Sex (`table_id=1620`, `2009–2025`)**: `input_files/outpatient_treatment_male_by_province.csv` and `input_files/outpatient_treatment_female_by_province.csv` (`24` StatVars across facility types and sex).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the legacy CNS Health archive (`/cns/jv-d/home/datcom/v3_mcf/country/indonesia/20240402/`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `28,122` | Legacy CNS Health import across 9 datasets (`2000–2023`) |
| **Current Observations** | `33,475` | Automated pipeline covering `2000–2025` across all `15` Health datasets |
| **Added Observations** | `+5,355` | `2023–2025` annual updates, 4 new Papua provinces (`Q113068089`, `Q113068116`, `Q113068135`, `Q115214873`), and 5 newly added Health tables |
| **Modified Observations** | `0` | 100% exact value match across all `28,120` overlapping historical CNS observations |
| **Deleted Observations** | `2` (`0.007%`) | Only 2 corrupted header cells (`value: 2015` and `value: 2023`) from empty cells in the legacy `idn_diseasecases__2007-2015.xlsx` spreadsheet |

---

## 4. How to Run

1. **Download and preprocess the source data into `input_files/`:**
   ```bash
   python3 statvar_imports/indonesia_census/health/download.py \
     --output_dir=statvar_imports/indonesia_census/health/input_files
   ```

2. **Run `stat_var_processor.py` to generate `output_files/indonesia_health_output.csv` and `output_files/indonesia_health_output.tmcf`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/health/input_files/*.csv \
     --pv_map=statvar_imports/indonesia_census/health/indonesia_health_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/health/indonesia_health_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/health/indonesia_health_places_resolved.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/health/output_files/indonesia_health_output \
     --output_counters=statvar_imports/indonesia_census/health/counters/indonesia_health_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/health -p "*_test.py"
   ```
