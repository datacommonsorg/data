# NCSES Employed College Graduates Import

**Import Name:** `NCSES_Employed_College_Grads_Import`  
**Dataset Provider:** National Center for Science and Engineering Statistics (NCSES), National Science Foundation (NSF)  
**Survey:** National Survey of College Graduates (NSCG)  
**Target Table:** Table 6-2 – *"Employed college graduates, by sex, ethnicity, race, and major occupation: 2003–23"*  
**Provenance URL:** [NCSES Data Explorer](https://ncsesdata.nsf.gov/explorer/datatables?term=race&exactMatch=no&page=1&filterSuperTopic=Demographics&filterTopic=Sex&datatablespage=2)  
**Survey Landing Page:** [NSCG Overview & Data Tables](https://ncses.nsf.gov/surveys/national-survey-college-graduates)  
**Licensing & Terms:** U.S. Federal Government Public Domain ([NSF Open Data Policy](https://www.nsf.gov/policies/open-government))

---

## 1. Dataset Overview & Coverage

This import pipeline ingests longitudinal counts of employed U.S. college graduates holding a bachelor's degree or higher across demographics and occupation groups:

- **Geographic Coverage:** National level (`country/USA`).
- **Temporal Coverage:** Biennial survey cycles: 2003, 2010, 2013, 2015, 2017, 2019, 2021, 2023 and so on.
- **Demographics:**
  - Gender: `Female`, `Male`, and Total (`Both sexes`).
  - Ethnicity: `HispanicOrLatino`.
  - Race: `WhiteAlone`, `BlackOrAfricanAmericanAlone`, `Asian`, `AmericanIndianOrAlaskaNative`, `OtherPacificIslander`, `TwoOrMoreRaces`.
- **Occupations:**
  - S&E Occupations (Biological/agricultural/life scientists, Computer/mathematical scientists, Physical/related scientists, Social/related scientists, Engineers).
  - S&E-Related Occupations.
  - Non-S&E Occupations.
- **Statistical Variables:** 209 canonical StatVars under `dcs:StatVarObservation`.

### Survey Footnote '2023a' & Header Normalization
In Table 6-2 (NSF 25-322), the 2023 column header is labeled `2023a`:
- **What 'a' Represents:** According to official NCSES survey documentation, footnote `a` documents a survey questionnaire wording change for sex:
  > *"The 2023 estimates by sex were based on responses to the question, 'What sex were you assigned at birth, on your original birth certificate? 1. Male, 2. Female,' which was a change from prior survey cycles."*
  (Prior survey cycles asked *"What is your sex?"* in 2021 and *"Are you ... 1. Male, 2. Female"* in 2019 and earlier).
- **Not Provisional Data:** Footnote `a` does **not** indicate preliminary, unverified, or provisional data. NCSES/NSCG does not publish provisional data in these final analytic data releases; all published figures represent final survey estimates.
- **Why It Is Removed:** `stat_var_processor.py` matches year column headers via exact string matching against keys defined in `pv_map.csv` (`2023`). Leaving the footnote suffix intact causes `stat_var_processor.py` to fail to recognize the column, dropping all 2023 observations. Because the numbers represent final official estimates for the 2023 survey cycle, `download.py` safely normalizes `2023a` to `2023` in the header rows (rows 1–4) when generating `source_files/cleaned_<filename>.xlsx`.

---

## 2. Directory Layout

```text
nces_employed_college_grads/
├── README.md                 # Dataset and operational documentation
├── download.py               # Dynamic scraper & header normalizer
├── manifest.json             # Pipeline automation & Cloud Batch execution spec
├── metadata.csv              # Global metadata config (place resolution to country/USA)
├── pv_map.csv                # Property-value mapping rules & #Header directives
├── validation_config.json    # Validation rules (0.1% deletions threshold)
├── source_files/             # Downloaded files (raw nsf*.xlsx and cleaned_*.xlsx)
├── output/                   # Transformed output CSV and TMCF
├── counters/                 # Counter logs produced by stat_var_processor
└── test_data/                # Minimal sample input and expected golden output
```

---

## 3. Execution Workflow

### Step 1: Download & Preprocess Source Data
Scrapes the NSCG landing page to locate the latest Table 6-2 Excel file, saves the raw file to `source_files/` to preserve data provenance, and generates an atomically written `source_files/cleaned_<filename>.xlsx` with normalized year headers:

```bash
python3 download.py
```

### Step 2: Transform & Generate StatisticalVariable Observations
Executes the standard Data Commons `stat_var_processor`:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=source_files/cleaned_*.xlsx \
  --pv_map=pv_map.csv \
  --config_file=metadata.csv \
  --output_path=output/nces_college \
  --output_counters=counters/nces_college.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

### Generated Outputs
- **Cleaned Data:** `output/nces_college.csv` (1,571 observations).
- **Template MCF:** `output/nces_college.tmcf`.
- **Counters:** `counters/nces_college.csv`.

---

## 4. Testing & Validation

### Lint & Formatting Check
Run lint via java jar tool and verify compliance with Google style via YAPF:

```bash
yapf --diff --style=google download.py
```

---

## 5. Pipeline Automation & Refresh Cadence

- **Automation:** Scheduled via Cloud Batch in `manifest.json`.
- **Cron Cadence:** Twice monthly on the 4th and 18th at 07:00 UTC (`0 07 4,18 * *`).
- **Validation:** Enforced via `validation_config.json` with `DELETED_RECORDS_PERCENT` capped at `0.1`.
