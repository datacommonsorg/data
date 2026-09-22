1. import_name": "Zurich_Population_Number_Of_Company_Workplace_Employees"

2. Import Overview
Number of companies, workplaces and employees in Zurich city at City, District (Kreise), and Quarter (Quartiere) Level.
Source URL: [BFS WIR STATENT Data](https://data.stadt-zuerich.ch/dataset/bfs_wir_statent_ast_beschaeftigte_vza_rechtsform_betrgr_jahr_od2552)
Import Type: Fully Autorefresh
Source Data Availability: 2011 to 2024
Release Frequency: P1Y

3. Preprocessing Steps (Yes)
Generate rollups from the downloaded dataset:
python3 wir_2552_wiki/generate_rollups.py

Rollup Logic & Explanation (`wir_2552_wiki/generate_rollups.py`):
- **Why Filter on Value `'0'` (`RechtsformSort == 0` & `BetriebsgrSort == 0`)**:
  - In the upstream dataset (`WIR255OD2552.csv`), category code **`0` represents the official aggregate total row** across all sub-categories: `RechtsformSort == 0` is *"Alle Rechtsformen"* (all legal forms combined) and `BetriebsgrSort == 0` is *"Alle Betriebsgrössen"* (all company sizes combined). Non-zero values (`1`, `2`, etc.) represent granular sub-category breakdowns (e.g., public-law vs. private-law entities, micro-businesses `<10` vs. small businesses `10–49`).
  - **Matches Target StatVar Schema**: The Data Commons StatVars emitted by this import (`Count_Company`, `Count_Person_Employed`, `Count_Person_Employed_Female`, `Count_Person_Employed_Male`, `Count_Person_FullTimeEmployee`, etc.) represent overall totals per place and year without legal form or company size constraints.
  - **Prevents Conflicting Duplicate Observations**: Retaining non-zero breakdown rows would cause `stat_var_processor.py` to map multiple sub-category rows to the exact same `(place, year, StatVar)` tuple, causing observation collisions.
  - **Avoids Undercounting from Suppressed Cells (`'K'`)**: Individual sub-category breakdown rows frequently contain `'K'` (confidentiality suppression for small counts). Summing non-zero breakdown rows manually would undercount true totals, whereas the official `(0, 0)` row provides the complete, authoritative total published by Statistics Zurich.
- **Unknown Region Exclusion**: Filters out unknown/unassigned region rows (`RaumSort` `990` ["Kreis Unbekannt"] and `999` ["Quartier Unbekannt"]) that do not map to valid geographic places.
- **Numeric Coercion**: Coerces metric columns (`Arbeitsstaetten`, `AnzBesch`, `AnzBeschW`, `AnzBeschM`, `AnzVZA`, `AnzVZAW`, `AnzVZAM`) to numeric values, converting non-numeric markers (e.g., `'K'` for confidential/suppressed entries) to `NaN` so they are cleanly skipped during StatVar observation generation.

4. Autorefresh Type

Fully Autorefresh:"0 2 1,15 * * " (Runs at 2:00 AM on the 1st and 15th day of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bfs_wir_statent_ast_beschaeftigte_vza_rechtsform_betrgr_jahr_od2552/download/WIR255OD2552.csv --output_folder=wir_2552_wiki/input_files && python3 wir_2552_wiki/generate_rollups.py && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=wir_2552_wiki/input_files/WIR255OD2552_rollups.csv --pv_map=wir_2552_wiki/wir_2552_wiki_pvmap.csv --config_file=wir_2552_wiki/wir_2552_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=wir_2552_wiki/output/zurich_population_wir_2552_wiki --output_counters=wir_2552_wiki/counters/zurich_population_wir_2552_wiki_counters.csv "

#####


1. import_name": "Zurich_Population"

2. Import Overview
Total population of Zurich city by quarter and year at Quarter (Quartiere) Level.
Source URL: [BEV324OD3240 Dataset](https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_od3240)
Import Type: Fully Autorefresh
Source Data Availability: 1941 to 2025
Release Frequency: P1Y

3. Preprocessing Steps (No)

4. Autorefresh Type

Fully Autorefresh:" 30 11 1,15 * * " (Runs at 11:30 AM on the 1st and 15th of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_od3240/download/BEV324OD3240.csv --output_folder=bev_3240_wiki/input_files && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=bev_3240_wiki/input_files/BEV324OD3240.csv --pv_map=bev_3240_wiki/bev_3240_wiki_pvmap.csv --config_file=bev_3240_wiki/bev_3240_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=bev_3240_wiki/output/zurich_population_bev_3240_wiki --output_counters=bev_3240_wiki/counters/zurich_population_bev_3240_wiki_counters.csv "

#####


1. import_name": "Zurich_Population_By_Age_Sex_Origin_Combined"

2. Import Overview
Population of Zurich city by age, sex, and origin at City, District (Kreise), and Quarter (Quartiere) Level.
Source URL: [BEV390OD3903 Dataset](https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903)
Import Type: Fully Autorefresh
Source Data Availability: 1993 to 2025
Release Frequency: P1Y

3. Preprocessing Steps (Yes)
Generate demographic and geographic rollups from the downloaded dataset:
python3 bev_3903_all/generate_rollups.py

Rollup Logic & Explanation (`bev_3903_all/generate_rollups.py`):
- **Why Rollup Aggregation is Required**:
  - The upstream dataset (`BEV390OD3903.csv`) publishes granular single-year-of-age (`AlterVCd` `0`–`100`) rows grouped into 10-year age brackets (`AlterV10Kurz`) crossed with gender (`SexKurz`) and nativity (`HerkunftLang`) at the Quarter (`QuarLang`) level, with District (`KreisLang`) provided as an attribute column. It does not publish pre-aggregated rows for Districts (`Kreis 1`–`12`), the City total (`Ganze Stadt`), or marginal 2-way, 1-way, and total demographic breakdowns.
  - Consolidating these breakdowns into a single script replaces the 3 separate legacy imports (`Zurich_Population_By_Age`, `Zurich_Population_By_Origin`, `Zurich_Population_By_Sex`) into one unified import.
- **Spatial Levels Aggregated**: Computes aggregations across all 3 geographic levels: Quarter (`QuarLang`), District (`KreisLang` mapped to `QuarLang`), and City (`Ganze Stadt`).
- **Demographic Slices Generated**: For each spatial level and year (`StichtagDatJahr`), computes all 8 combinations:
  1. Full 3-way: `AlterV10Kurz` x `SexKurz` x `HerkunftLang`
  2. 2-way marginals: `AlterV10Kurz` x `SexKurz`, `AlterV10Kurz` x `HerkunftLang`, `SexKurz` x `HerkunftLang`
  3. 1-way marginals: `AlterV10Kurz` only, `SexKurz` only, `HerkunftLang` only
  4. Total population (`Count_Person` with all demographic dimensions empty)
- **Unknown Region Exclusion & Numeric Coercion**: Filters out unknown region rows (`QuarSort`/`QuarCd`/`KreisCd` `990` or `999`, or `'Unbekannt'`), coerces `AnzBestWir` to numeric, uses `sum(min_count=1)` and `.dropna()` so suppressed (`'K'`) slices are dropped rather than emitted as false `0` counts, and casts valid sums back to integers.

4. Autorefresh Type

Fully Autorefresh:" 0 6 1,15 * * " (Runs at 6:00 AM on the 1st and 15th of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903/download/BEV390OD3903.csv --output_folder=bev_3903_all/input_files && python3 bev_3903_all/generate_rollups.py && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=bev_3903_all/input_files/BEV390OD3903_rollups.csv --pv_map=bev_3903_all/bev_3903_wiki_pvmap.csv --config_file=bev_3903_all/bev_3903_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=bev_3903_all/output/zurich_population_bev_3903_wiki --output_counters=bev_3903_all/counters/zurich_population_bev_3903_wiki_counters.csv "

#####


1. import_name": "Zurich_Births_By_Sex_Origin_Combined"

2. Import Overview
Births in Zurich city by sex and origin at City, District (Kreise), and Quarter (Quartiere) Level.
Source URL: [BEV403OD4031 Dataset](https://data.stadt-zuerich.ch/dataset/bev_tag_geburten_quartier_geschl_ag_herkunft_od4031)
Import Type: Fully Autorefresh
Source Data Availability: 1998 to 2026
Release Frequency: P1Y

3. Preprocessing Steps (Yes)
Generate demographic and geographic rollups from the downloaded dataset:
python3 bev_4031_all/generate_rollups.py

Rollup Logic & Explanation (`bev_4031_all/generate_rollups.py`):
- **Why Rollup Aggregation is Required**:
  - The upstream dataset (`BEV403OD4031.csv`) publishes daily birth records (`GueltigAbDatMM`, `GueltigAbDatDD`) crossed with gender (`SexLang`) and nativity (`HerkunftLang`) at the Quarter (`QuarLang`) level, with District (`KreisLang`) provided as an attribute column. It does not publish annual sums (`GueltigAbDatJahr`), District or City totals (`Ganze Stadt`), or marginal 1-way and total birth counts.
  - Consolidating these breakdowns into a single script replaces the 3 separate legacy imports (`Zurich_Population_Number_Of_Birth`, `Zurich_Population_Number_Of_Birth_By_Origin`, `Zurich_Population_Number_Of_Birth_By_Sex`) into one unified import.
- **Temporal & Spatial Aggregation**: Aggregates daily births into annual totals (`GueltigAbDatJahr`) across all 3 geographic levels: Quarter (`QuarLang`), District (`KreisLang` mapped to `QuarLang`), and City (`Ganze Stadt`).
- **Demographic Slices Generated**: For each spatial level and year, computes all 4 combinations:
  1. Full 2-way: `SexLang` x `HerkunftLang`
  2. 1-way marginals: `SexLang` only, `HerkunftLang` only
  3. Total births (`Count_BirthEvent` with both demographic dimensions empty)
- **Unknown Region Exclusion & Numeric Coercion**: Filters out unknown region rows (`QuarCd`/`KreisCd` `990` or `999`, or `'Unbekannt'`), coerces `AnzGebuWir` to numeric, uses `sum(min_count=1)` and `.dropna()` so suppressed (`'K'`) slices are dropped rather than emitted as false `0` counts, and casts valid sums back to integers.

4. Autorefresh Type

Fully Autorefresh:" 0 20 1,15 * * " (Runs at 8:00 PM on the 1st and 15th of every month).

5. Script Execution Details

" python3 ../../util/download_util_script.py --download_url=https://data.stadt-zuerich.ch/dataset/bev_tag_geburten_quartier_geschl_ag_herkunft_od4031/download/BEV403OD4031.csv --output_folder=bev_4031_all/input_files && python3 bev_4031_all/generate_rollups.py && python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=bev_4031_all/input_files/BEV403OD4031_rollups.csv --pv_map=bev_4031_all/bev_4031_wiki_pvmap.csv --config_file=bev_4031_all/bev_4031_wiki_metadata.csv --output_columns=observationAbout,observationDate,value,variableMeasured --output_path=bev_4031_all/output/zurich_bev_4031_wiki --output_counters=bev_4031_all/counters/zurich_bev_4031_wiki_counters.csv "
