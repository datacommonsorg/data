# PR #2171 Description: Commerce EDA USASpending Import

## Overview

This PR modernizes the **Commerce EDA (Economic Development Administration)** import pipeline (`statvar_imports/commerce_eda_usaspending`) by replacing legacy manual spreadsheet downloads (`eda.gov`) with automated ingestion from the official **USAspending REST API** (`api.usaspending.gov`).

The updated pipeline runs autonomously on a weekly schedule (`cron: 30 05 * * 1`), restores data freshness up to FY 2026 (+5 years beyond the 2021 data freeze), incorporates 4 newly authorized statutory grant programs, expands geographic coverage to 58 states/territories, and enforces robust hermetic testing and DuckDB validation rules.

---

## 1. Programs & Statistical Variables Coverage

The import covers **11 distinct EDA grant programs** plus **Total**, mapped to clean Data Commons Statistical Variables:

| Statistical Variable DCID | Program / CFDA | Description | Status |
| :--- | :--- | :--- | :--- |
| `Amount_Investment` | **Total** | Sum of all positive EDA program investments | Retained & Expanded |
| `Amount_Investment_PublicWorks` | **Public Works** (CFDA 11.300) | Public Works & Economic Development Facilities | Retained & Expanded |
| `Amount_Investment_ProgramPlanning` | **Planning** (CFDA 11.302) | Planning Program for districts, states, and Indian Tribes | Retained & Expanded |
| `Amount_Investment_TechnicalAssistance` | **Technical Assistance** (CFDA 11.020, 11.303) | Local and National Technical Assistance | Retained & Expanded |
| `Amount_Investment_EconomicAdjustmentAssistance` | **Economic Adjustment Assistance** (CFDA 11.307) | Long-term economic distress & disaster recovery | Retained & Expanded |
| `Amount_Investment_TradeAdjustmentAssistance` | **Trade Adjustment Assistance for Firms** (CFDA 11.310, 11.313) | Trade adjustment assistance for trade-impacted companies | Retained & Expanded |
| `Amount_Investment_ResearchNationalTechnicalAssistance` | **Research & National Technical Assistance** (CFDA 11.312) | Research and evaluation programs | Retained & Expanded |
| `Amount_Investment_RegionalInnovationStrategies` | **Regional Innovation Strategies** (CFDA 11.024) | Build to Scale (Venture & Capital Challenges) | Retained & Expanded |
| `Amount_Investment_RegionalTechnologyAndInnovationHubs` | **Regional Technology & Innovation Hubs** (CFDA 11.039) | CHIPS and Science Act Tech Hubs Program | **NEW** |
| `Amount_Investment_DistressedAreaRecompetePilotProgram` | **Distressed Area Recompete Pilot Program** (CFDA 11.040) | Persistent economic distress grant initiatives | **NEW** |
| `Amount_Investment_ScienceAndResearchParkDevelopmentGrants` | **Science & Research Park Development Grants** (CFDA 11.030) | Science & Research Park development infrastructure | **NEW** |
| `Amount_Investment_STEMTalentChallenge` | **STEM Talent Challenge** (CFDA 11.023) | Regional STEM work-and-learn models | **NEW** |

---

## 2. Production vs. USAspending Comparison Summary

A comprehensive audit between legacy production (`gs://datcom-prod-imports/statvar_imports/commerce_eda/Commerce_EDA/`) and the new USAspending pipeline is documented in `PROD_DATA_COMPARISON.md`:

- **Data Continuity (2012–2026):** Resolves a 5-year freeze caused when EDA ceased publishing manual Excel tables in 2021. USAspending adds **+5 fiscal years (2022–2026)** of live grant obligations.
- **Geographic Expansion (58 Places):** Adds **Federated States of Micronesia** (`geoId/64`) and **Marshall Islands** (`geoId/68`), bringing total coverage to 50 states, DC, and 7 outlying territories.
- **De-obligation Handling & Additivity:** Net non-positive program-year totals (resulting from contract de-obligations) are filtered out, and `Total` is computed strictly as the sum of surviving positive program components. This guarantees mathematical consistency (State Total = sum of reported components).
- **Integer Dollar Precision:** Replaces legacy unrounded floating-point cents with clean integer dollars (`round(val)`).
- **PR Sample Strategy:** Capped committed sample file (`input_files/investment_cleaned.csv`) to 200 rows in git to prevent repository bloat, while full automated execution produces 2,643 SVObs.

---

## 3. Validation Rules Rationale (`validation_config.json`)

The validation configuration is tuned specifically for federal grant obligation patterns:

1. **`active_programs_freshness` (DuckDB `SQL_VALIDATOR`):**
   - **Rule:** Asserts that active core programs (`Amount_Investment`, `Amount_Investment_PublicWorks`, `Amount_Investment_EconomicAdjustmentAssistance`, `Amount_Investment_ProgramPlanning`, `Amount_Investment_TechnicalAssistance`) have `MaxDate >= (EXTRACT(YEAR FROM CURRENT_DATE) - 1)`.
   - **Rationale:** Grant obligations operate on federal fiscal years and close asynchronously over several months. A 1-year tolerance ensures freshness without triggering false alarms during early-fiscal-year reporting lag.
2. **Omission of `MAX_DATE_CONSISTENT`:**
   - **Rationale:** Series legitimately terminate in different fiscal years. Newer statutory programs (Tech Hubs, Recompete Pilot) begin in 2024–2025, while legacy grant series terminate earlier. A blanket consistency check across all StatVars would incorrectly fail.
3. **`check_deleted_records_percent` (0.1% Deletion Tolerance):**
   - **Rationale:** Accommodates legitimate post-award de-obligations and multi-year reconciliations while catching unintended widespread data drop-offs.
4. **Omission of Golden Files:**
   - **Rationale:** In accordance with Data Commons guidelines for automated weekly API pipelines (`cron_schedule: 30 05 * * 1`), golden files and `GOLDENS_CHECK` rules are omitted to prevent brittle CI diff breaks on actively evolving datasets where new awards and post-award de-obligations are ingested weekly.

---

## 4. Verification & Testing

- **Hermetic Unit Tests:** 13 unit tests pass in 0.09s (`python3 -m unittest statvar_imports/commerce_eda_usaspending/process_test.py`) covering pagination threshold ceiling, retries, deduplication by `generated_internal_id`, de-obligations, empty award guards, and CFDA mapping.
- **Syntax & Lint:** `python3 -m py_compile` clean; zero lines > 100 characters in code.
- **Cloud Batch Test Execution (`datcom-import-test`):**
  - **Project:** `datcom-infosys-dev`
  - **Target Bucket:** `gs://datcom-import-test/statvar_imports/commerce_eda_usaspending/Commerce_EDA_USASpending/`
  - **Artifacts Generated:** `Investment_output.csv`, `Investment_output.tmcf`, `Investment_output_stat_vars.mcf`, `counters/investment_counters.csv`.
