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
2. **Resolve headers via `stat_var_processor.py` and write balanced `StatVarObservation` CSV shards (`output/output_part_*.csv`), `output/output.tmcf`, and StatVar MCFs (`output/output_stat_vars*.mcf`):**
   ```bash
   python3 preprocess.py
   ```
   * Full observation counts across all 42 balanced shards (`output/output_part_*.csv`, totaling `283,560,361` observations) are logged by `preprocess.py`.

## Testing & Generating Expected Test Outputs

Sample raw inputs (2 data rows per file) are located under `test_data/raw_data/`, with expected test outputs (`output_part_0001.csv`–`output_part_0006.csv` and `output.tmcf`) under `test_data/output/`.

Run all commands below from `data/scripts/opportunity_insights_outcomes/`:

1. **Run `preprocess.py` on `test_data/raw_data` to generate `test_data/output/output_part_*.csv` and `test_data/output/output.tmcf`:**
   ```bash
   python3 preprocess.py \
     --input_dir=test_data/raw_data \
     --sv_output_prefix=test_data/output/output \
     --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
   ```

2. **Run unit and integration tests:**
   ```bash
   python3 download_test.py
   ```

---

## Dataset Coverage & Schema Details
* **Geographic Coverage:**
  * **Commuting Zones (`commuting_zone`):** `geoId/cz{cz:05d}` (741 US commuting zones)
  * **Counties (`county`):** `geoId/{state:02d}{county:03d}` (3,219 US counties)
  * **Census Tracts (`tract`):** `geoId/{state:02d}{county:03d}{tract:06d}` (73,461 US census tracts)
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
  * Dimensionless (omitted `unit`) for percentile ranks, fractions, and counts

---

## Directory & File Structure
* `download.py`: Scrapes the Opportunity Insights catalog (`https://opportunityinsights.org/data/`) with canonical fallback URLs, downloads raw CSV/ZIP archives with bounded retries, and extracts them into `raw_data/`.
* `preprocess.py`: Normalizes multi-word column headers, resolves all unique column headers via `stat_var_processor.py` (emitting `output/output_stat_vars*.mcf`), and expands all 6 datasets in parallel across CPU cores into balanced `StatVarObservation` CSV shards (`output/output_part_*.csv`) and `output/output.tmcf` with numeric values formatted to 5 decimal digits.
* `pvmap.csv`: Property-value mapping table translating normalized column tokens (`_`-delimited) into Data Commons `StatisticalVariable` and `StatVarObservation` properties.
* `metadata.csv`: Configuration for `stat_var_processor.py` (`word_delimiter: "_"`, `output_columns: "observationAbout,observationDate,observationPeriod,variableMeasured,value,unit"`).
* `manifest.json`: Automated import specification, script execution sequence, GCS `import_inputs` (`output/output.tmcf` and `output/output_part_*.csv`), `node_mcf` (`output/*.mcf`), monthly cron schedule (`0 8 1 * *`), and resource limits.
* `download_test.py`: Unit and end-to-end integration test suite covering URL discovery, archive extraction, header normalization, balanced parallel shard generation, and `stat_var_processor.py` output equivalence.

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
To validate the generated shards (`output/output_part_*.csv`), `output/output.tmcf`, and StatVar MCFs (`output/*.mcf`) locally with `import-tool.jar`:

```bash
java -Xmx90g -jar ~/Downloads/import-tool.jar genmcf \
  -n=4 \
  output/output_part_*.csv \
  output/output.tmcf \
  output/*.mcf
```

### Summary Metrics
* **Status:** Succeeded with **0 errors / 0 fatals**
* **Total Observations (`NumRowSuccesses`):** `283,560,361` across `output/output_part_*.csv`
* **Total MCF Nodes Generated (`NumNodeSuccesses`):** `283,661,010`
* **Total Property-Value Successes (`NumPVSuccesses`):** `2,276,128,676`
* **Unique StatisticalVariables:** `10,596` active StatVars emitted with observations (out of `11,247` total mapped StatVars across `10,815` existing `dc/` StatVars and `432` new schema StatVars)

### Explanation of Warnings & Data Holes (`report.json`)
All warnings in `dc_generated/report.json` are expected characteristics of the source dataset:

1. **`StatsCheck_Data_Holes` (`640` warnings):**
   * **New vs. Existing Data:** All 640 holes occur exclusively in the **new 2024 annual birth-cohort datasets** (`county_by_cohort_outcomes.csv` and `cz_by_cohort_outcomes.csv`, where each birth cohort `1978`–`1992` maps to an annual `observationDate` `2005`–`2019` with `observationPeriod: P1Y`). The legacy Data Commons import only included multi-year pooled cohorts (single `observationDate` per StatVar/place) and therefore had no multi-date time series on which `StatsCheck_Data_Holes` could trigger.
   * **Root Cause (Valid Source Suppression):** Opportunity Insights suppresses cells (leaving them blank `""` in the raw CSVs) when a county or commuting zone has an insufficient sample size (`kid_n`) for a specific demographic subgroup in a single birth year. For example, in `county_by_cohort_outcomes.csv` for Hill County, MT (`geoId/30041`), `AmericanIndianAndAlaskaNativeAlone` (`aian`) female outcome rows are present for cohorts `1980` (`2007`), `1982` (`2009`), and `1985`–`1992` (`2012`–`2019`), while the intermediate single-year cohorts are suppressed (`""`) in the raw source file.
2. **`StrSplit_EmptyToken_unit` (`275,914,573` warnings):**
   * Expected because the shared `output_columns` schema includes `unit`. Only the dollar-denominated income metrics (`kfi_*` and `kii_*`, `7,645,788` rows) have `unit: USDollar`; the remaining `275,914,573` rows are dimensionless ranks, fractions, or counts with an empty `unit` column.
3. **`StatsCheck_MaxPercentFluctuationGreaterThan100` (`259`), `StatsCheck_MaxPercentFluctuationGreaterThan500` (`86`), and `StatsCheck_3_Sigma` (`41`):**
   * Expected year-to-year variance in the 1-year birth cohort series (`P1Y`) and between the 2010 and 2020 decennial census point-in-time (`P1D`) estimates for small demographic subgroups in smaller counties, commuting zones, and census tracts.
