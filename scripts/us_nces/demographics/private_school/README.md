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

### Place Properties of Private Schools (`dcs:PrivateSchool`)
The place import (`NCES_PrivateSchool`) defines `dcs:PrivateSchool` entities with the following properties mapped in `us_nces_demographics_private_place.tmcf`:

| Property | Description | Source ELSI Field | Example / Format |
| :--- | :--- | :--- | :--- |
| `dcid` | Unique Data Commons ID | `School ID - NCES Assigned` | `dcid:nces/00000033` |
| `ncesId` | Canonical 8-character NCES ID | `School ID - NCES Assigned` | `00000033` |
| `name` | Canonical school name | `Private School Name` | `ST JOHN LUTHERAN SCHOOL` |
| `address` | Formatted street address | `Physical Address`, `City`, `State Abbr`, `ZIP`, `ZIP + 4` | `100 MAIN ST, BIRMINGHAM, AL, 35203` |
| `containedInPlace` | County and State administrative places | `ANSI/FIPS County Code`, `ANSI/FIPS State Code` | `geoId/01073`, `geoId/01` |
| `telephone` | Contact phone number | `Phone Number` | `2055551234` |
| `lowestGrade` | Lowest grade offered | `Lowest Grade Taught` | `Prekindergarten`, `1st grade` |
| `highestGrade` | Highest grade offered | `Highest Grade Taught` | `12th grade`, `8th grade` |
| `schoolGradeLevel` | School level classification | `School Level` | `1-Elementary`, `2-Secondary`, `3-Combined` |
| `educationalMethod` | School program/method type | `School Type` | `1-Regular Elementary or Secondary`, `2-Montessori` |
| `religiousOrientation` | Specific religious denomination | `Religious Orientation` | `Roman Catholic`, `Baptist`, `Nonsectarian` |
| `coeducationStatus` | Student gender enrollment status | `Coeducational` | `1-Coed`, `2-All-female`, `3-All-male` |

> [!NOTE]
> * **Latitude / Longitude**: Private schools in PSS do not emit `latitude` or `longitude` coordinates (unlike Public School and School District place imports).
> * **Unmapped Intermediate Columns**: Intermediate survey columns `School's Religious Affiliation` (`relig`) and `School Community Type` (`ucommtyp`) are retained during data extraction for compatibility with the ELSI 58-column layout but are not mapped to Schema.org properties in `us_nces_demographics_private_place.tmcf`.

---

## Upstream Data Anomalies & Normalization Handling

### Student Race Percentage Denominator Discrepancy (> 100%)
* **Upstream Phenomenon**: In earlier PSS survey waves (such as 2001–02 `PSS0102_PU.csv`), NCES reported race student counts (`p310`–`p332`) that included Pre-Kindergarten students (`p305`), whereas total student enrollment (`numstuds`) counted only Kindergarten through Grade 12 + Ungraded students.
* **Impact**: For schools with substantial Pre-K enrollment and low K–12 enrollment, raw ratios and pre-computed percentages (`p_indian`, `p_asian`, `p_hisp`, `p_white`, `p_black`) exceeded 100.0% (up to 250.0%).
* **Pipeline Remediation**: `process.py` validates race percentages via `_format_float_col(..., is_percentage=True)`. Any calculated or upstream percentage exceeding 100.0% is treated as invalid and mapped to the standard NCES missing data symbol (`"†"`). In addition, when computing `p_black = (p325 / numstuds) * 100` for 1997–2015 cycles, `process.py` validates `p325 <= numstuds` to ensure impossible percentages are not generated.

---

### Running Tests

Run the test cases

- `python3 -m unittest scripts/us_nces/demographics/private_school/process_test.py`