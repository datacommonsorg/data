# US: National Center for Education Statistics - Private School Universe Survey (PSS)

## Import Overview
This pipeline ingests demographic and institutional data from the **National Center for Education Statistics (NCES) Private School Universe Survey (PSS)** for all biennial survey cycles.

* **Source URL**: [https://nces.ed.gov/surveys/pss/pssdata.asp](https://nces.ed.gov/surveys/pss/pssdata.asp)
* **Data Nature**: Canonical Census/NCES public-use survey microdata (`pss*.csv` / `pss*.txt`) with up to 335 columns per wave.
* **Periodicity**: Biennial (`P2Y`).
* **Entities**: ~65,648 unique private schools.
* **Observations**: ~9,082,570 demographic observation rows across 35 Statistical Variables.

---

## Autorefresh Type: Automated

## Import Architecture & Cron Scheduling
Private School is structured as two independent, staggered Cloud Batch imports in [manifest.json](manifest.json):

```text
[TIER 1: Week 1 (Day 3)]                 [TIER 2: Week 2 (Day 10, +7d)]
========================                 ==============================

NCES_PrivateSchool (Place) ─────────────► NCES_PrivateSchoolStats (Stats)
(Defines: dcid:nces/...)                  (Refs: observationAbout: dcs:nces/...)
```

### Staggered Quarterly Cron Schedule
| Import Name | Domain | Script Invocations | Staggered `cron_schedule` |
| :--- | :--- | :--- | :--- |
| **`NCES_PrivateSchool`** | Place Entities | `download.py`<br>`process.py --mode=place` | `"30 4 3 3,6,9,12 *"` (Day 3, 04:30 UTC) |
| **`NCES_PrivateSchoolStats`** | Statistical Observations | `download.py`<br>`process.py --mode=stats` | `"30 7 10 3,6,9,12 *"` (Day 10, 07:30 UTC) |

The 7-day interval guarantees that newly onboarded private school entities from modern survey waves (2021–22 and 2023–24) are ingested and indexed in Data Commons before the Stats import processes observations about them.

---

## Script Execution Details

### Step 1: Download Survey Data
Run the standalone PSS downloader:
```bash
python3 download.py
```
* Dynamically scrapes `https://nces.ed.gov/surveys/pss/pssdata.asp`.
* Downloads and normalizes ZIP archives for all 14 survey waves (1997–2023).
* Converts historical tab-delimited TXT files (1997–2011) to comma-separated CSVs.
* Extracts data atomically into `gcs_folder/input_files/<start_year>/`.

### Step 2: Process Data
The `process.py` script supports the `--mode` flag (`place`, `stats`, or `all`, default: `all`):

```bash
# Generate Place artifacts only (NCES_PrivateSchool)
python3 process.py --mode=place

# Generate Stats artifacts only (NCES_PrivateSchoolStats)
python3 process.py --mode=stats

# Generate both Place and Stats artifacts (Unified local execution)
python3 process.py
```

### Step 3: Run Unit Tests
Validate transformation and parsing logic:
```bash
python3 -m unittest process_test.py
```

---

## Output Artifacts

### Place Import (`--mode=place`)
* **Cleaned Place CSV**: `gcs_folder/output_place/us_nces_demographics_private_place.csv` (~65.6K schools)
* **Place Template MCF**: `gcs_folder/output_place/us_nces_demographics_private_place.tmcf`
* **Provisional Node MCF**: [ProvisionalNodePlaces.mcf](ProvisionalNodePlaces.mcf) (Defines 5,421 provisional nodes for new 2021/2023 schools)

### Stats Import (`--mode=stats`)
* **Observations CSV**: `gcs_folder/output_files/us_nces_demographics_private_school.csv` (~9.08M rows)
* **Observations Template MCF**: `gcs_folder/output_files/us_nces_demographics_private_school.tmcf`
* **Statistical Variables MCF**: `gcs_folder/output_files/us_nces_demographics_private_school.mcf`

---

## Statistical Variables & Place Properties

### Statistical Variables (35 SVs)
Population estimates categorized across:
1. Count of Students categorized by Race (White, Black, Hispanic, Asian, American Indian/Alaska Native, Pacific Islander, Two or More Races).
2. Count of Students categorized by Grade Level (Pre-Kindergarten to Grade 12, Ungraded).
3. Student Enrollment Subtotals (Grades 1–8, Grades 9–12, PK & K, Total Ungraded & K–12, Total Ungraded & PK–12).
4. Full-Time Equivalent (FTE) Teachers.
5. Pupil/Teacher Ratio.

### Place Properties of Private Schools
1. `School ID - NCES Assigned` (`dcid:nces/...`)
2. `Private School Name`
3. `Physical Address`, `City`, `State Abbr`, `ZIP`, `ZIP + 4`
4. `ANSI/FIPS State Code` & `ANSI/FIPS County Code`
5. `Phone Number`
6. `Lowest Grade Taught` & `Highest Grade Taught`
7. `School Level` (Elementary, Secondary, Combined)
8. `School Type` (Regular, Montessori, Special Education, Alternative, etc.)
9. `Coeducational` (Coed, All-female, All-male)
10. `Religious Orientation` & `School's Religious Affiliation`
11. `School Community Type` (City, Suburb, Town, Rural)

---
### Running Tests

Run the test cases

- `python3 -m unittest scripts/us_nces/demographics/private_school/process_test.py`