# Opportunity Insights: The Opportunity Atlas Outcomes (`OpportunityInsightsOutcomes`)

This import migrates the legacy `google3` Borg import (`//depot/google3/datacommons/mcf/oi_v3/opportunity_atlas_outcomes_v2.py`) to `stat_var_processor.py`.

## Source Data
* **Provider:** Opportunity Insights (https://opportunityinsights.org/data/)
* **Source Files (`raw_data/`):**
  * `commuting_zone_outcomes.csv` (`geoId/cz{cz:05d}`)
  * `county_outcomes.csv` (`geoId/{state:02d}{county:03d}`)
  * `tract_outcomes.csv` (`geoId/{state:02d}{county:03d}{tract:06d}`, including the 72 `kfi_*` and `kii_*` dollar-level income columns)
  * `tract_outcomes_late_simple.csv` (1984–1989 cohort refresh)
  * `county_by_cohort_outcomes.csv` (1978–1992 annual birth cohorts)
  * `cz_by_cohort_outcomes.csv` (1978–1992 annual birth cohorts)

## Pipeline Steps
1. **Download and extract raw CSVs into `raw_data/`:**
   ```bash
   python3 download.py
   ```
2. **Resolve headers and prepare sharded CSV inputs (`input_files/` and `output/output_part_*.csv`):**
   ```bash
   python3 preprocess.py
   ```
3. **Run `stat_var_processor.py` to generate final MCF, TMCF, CSVs, and counters:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="input_files/*_cleaned.csv" \
     --pv_map=pvmap.csv \
     --config_file=metadata.csv \
     --output_path=output/output \
     --output_counters=counters/output_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

## Testing & Generating Expected Test Outputs

Sample raw inputs (2 data rows per file) are located under `test_data/raw_data/`, mirroring the regular directory layout (`test_data/raw_data/`, `test_data/input_files/`, `test_data/output/`).

Run all commands below from `data/statvar_imports/opportunity_insights_outcomes/`:

1. **Run `preprocess.py` on `test_data/raw_data` to generate `test_data/input_files/*_cleaned.csv` and `test_data/output/output_part_*.csv`:**
   ```bash
   python3 preprocess.py \
     --input_dir=test_data/raw_data \
     --shard_dir=test_data/input_files \
     --sv_output_prefix=test_data/output/output \
     --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
   ```

2. **Run `stat_var_processor.py` to generate `test_data/output/output.csv`, `test_data/output/output.tmcf`, `test_data/output/output_stat_vars.mcf`, and `test_data/counters/output_counters.csv`:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="test_data/input_files/*_cleaned.csv" \
     --pv_map=pvmap.csv \
     --config_file=metadata.csv \
     --output_path=test_data/output/output \
     --output_counters=test_data/counters/output_counters.csv \
     --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
   ```

3. **Run unit and integration tests:**
   ```bash
   python3 download_test.py
   ```

---

## Dataset Coverage & Schema Details
* **Geographic Coverage:**
  * **Commuting Zones (`commuting_zone`):** `geoId/cz{cz:05d}` (741 US commuting zones)
  * **Counties (`county`):** `geoId/{state:02d}{county:03d}` (~3,221 US counties)
  * **Census Tracts (`tract`):** `geoId/{state:02d}{county:03d}{tract:06d}` (~73,438 US census tracts)
* **Temporal Coverage & Cohorts:**
  * **Baseline Cohort (`1978–1983` birth cohorts):** Multi-year pooled estimates (`observationDate` ranging from `1991` to `2015`, `observationPeriod` from `P1D` to `P22Y` depending on outcome age window).
  * **Late Cohort Refresh (`1984–1989` birth cohorts):** `tract_outcomes_late_simple.csv` (`observationDate: 2016` with `P6Y`, `2020-04-01` with `P1D` for incarceration, and `2010-04-01` with `P1D` for child counts).
  * **Annual Birth Cohorts (`1978–1992` single-year cohorts):** `county_by_cohort_outcomes.csv` and `cz_by_cohort_outcomes.csv` mapped via cohort tokens `c1978`–`c1992` to `observationDate: 2005`–`2019` (outcome measured at age 27) with `observationPeriod: P1Y`.
* **Demographic Dimensions:**
  * **Population Type:** `OpportunityInsightsCohort`
  * **Race (`race`):** Pooled (omitted), `USC_AmericanIndianAndAlaskaNativeAlone` (`aian`/`natam`), `USC_AsianAlone` (`asian`), `USC_BlackOrAfricanAmericanAlone` (`black`), `USC_HispanicOrLatinoRace` (`hisp`), `USC_WhiteAloneNotHispanicOrLatino` (`white`), `OI_RaceOther` (`other`)
  * **Gender (`gender`):** Pooled (omitted), `Male` (`male`), `Female` (`female`)
  * **Parent Household Income Percentile (`parentIncome`):** `Percentile1` (`p1`), `Percentile10` (`p10`), `Percentile25` (`p25`), `Percentile50` (`p50`), `Percentile75` (`p75`), `Percentile100` (`p100`)
  * **Statistical Types (`statType`):** `measuredValue` (default), `stdError` (`se`), `meanValue` (`mean`), `meanStdError` (`meanse`), `sampleSize` (`n`)
* **Units:**
  * `USDollar` for dollar-denominated household and individual income variables (`kfi_*` and `kii_*`)
  * Dimensionless (empty `unit`) for percentile ranks, fractions, and counts

---

## Directory & File Structure
* `download.py`: Scrapes the Opportunity Insights catalog (`https://opportunityinsights.org/data/`) with canonical fallback URLs, downloads raw CSV/ZIP archives with bounded retries, and extracts them into `raw_data/`.
* `preprocess.py`: Normalizes multi-word column headers, formats `geoId` DCIDs, writes compact seed CSVs into `input_files/*_cleaned.csv` for `stat_var_processor.py` header resolution, and expands the 283.56M observations in parallel across CPU cores into `output/output_part_0001.csv`..`output_part_0045.csv`.
* `pvmap.csv`: Property-value mapping table translating normalized column tokens (`_`-delimited) into Data Commons `StatisticalVariable` and `StatVarObservation` properties.
* `metadata.csv`: Configuration for `stat_var_processor.py` (`word_delimiter: "_"`, `output_columns: "observationAbout,observationDate,observationPeriod,variableMeasured,value,unit"`).
* `manifest.json`: Automated import specification, script execution sequence, GCS input/source file globs, monthly cron schedule (`0 8 1 * *`), and resource limits.
* `download_test.py`: Unit and end-to-end integration test suite covering URL discovery, archive extraction, header normalization, wide-CSV sharding, and `stat_var_processor.py` output equivalence.

---

## Automated Refresh & Resource Configuration (`manifest.json`)
* **Schedule:** `0 8 1 * *` (Runs at 08:00 UTC on the 1st of every month).
* **Resource Limits:**
  * **CPU:** `32` cores
  * **Memory:** `512` GB RAM
  * **Disk:** `400` GB

---

## Validation & `dc-import` (`genmcf`) Results

### Running `genmcf` Locally
Because the full output contains **283.56 million observations** (~18 GB across 46 CSV shards) and generates ~105 GB of MCF nodes, bound the JVM heap and thread count (`-n=4`) to avoid host OOM kills:

```bash
java -Xmx90g -jar ~/Downloads/import-tool.jar genmcf \
  -n=4 \
  output/*.csv \
  output/output.tmcf \
  schema_from_ws/*.mcf
```

### Summary Metrics (`dc_generated/report.json` & `dc_generated/summary_report.csv`)
* **Status:** Succeeded with **0 errors / 0 fatals** (runtime ~57.5 minutes with `-Xmx90g -n=4`)
* **Total CSV Rows Processed (`NumRowSuccesses`):** `283,560,361`
* **Total MCF Nodes Generated (`NumNodeSuccesses`):** `283,658,483`
* **Total Property-Value Successes (`NumPVSuccesses`):** `2,276,128,676`
* **Existence Checks (`Existence_NumChecks`):** `2,284,368,662` (`Existence_NumDcCalls`: `2,338`)
* **Unique StatisticalVariables:** `10,596`

### Explanation of Warnings & Data Holes (`report.json`)
All warnings in `dc_generated/report.json` are expected characteristics of the source dataset:

1. **`StatsCheck_Data_Holes` (`442` warnings):**
   * **New vs. Existing Data:** All 442 holes occur exclusively in the **new 2024 annual birth-cohort datasets** (`county_by_cohort_outcomes.csv` and `cz_by_cohort_outcomes.csv`, where each birth cohort `1978`–`1992` maps to an annual `observationDate` `2005`–`2019` with `observationPeriod: P1Y`). The legacy Data Commons import only included multi-year pooled cohorts (single `observationDate` per StatVar/place) and therefore had no multi-date time series on which `StatsCheck_Data_Holes` could trigger.
   * **Root Cause (Valid Source Suppression):** Opportunity Insights suppresses cells (leaving them blank `""` in the raw CSVs) when a county or commuting zone has an insufficient sample size (`kid_n`) for a specific demographic subgroup in a single birth year. For example, in `county_by_cohort_outcomes.csv` for Calhoun County, AL (`geoId/01015`), `AsianAlone` (`asian`) rows are present for cohorts `1982` (`2009`), `1984` (`2011`), and `1985` (`2012`), but all `asian` outcome columns are blank (`""`) in the raw source file for cohort `1983` (`2010`).
2. **`StrSplit_EmptyToken_unit` (`275,914,573` warnings):**
   * Expected because the shared `output_columns` schema includes `unit`. Only the dollar-denominated income metrics (`kfi_*` and `kii_*`, `7,645,788` rows) have `unit: USDollar`; the remaining `275,914,573` rows are dimensionless ranks, fractions, or counts with an empty `unit` column.
3. **`StatsCheck_MaxPercentFluctuationGreaterThan100` (`262`), `StatsCheck_MaxPercentFluctuationGreaterThan500` (`76`), and `StatsCheck_3_Sigma` (`38`):**
   * Expected year-to-year variance in the 1-year birth cohort series (`P1Y`) for small demographic subgroups in smaller counties and commuting zones.
