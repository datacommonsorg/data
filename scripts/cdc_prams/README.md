# US: CDC Pregnancy Risk Assessment Monitoring System (PRAMS)

## About the Dataset
This dataset provides Population Estimates and Maternal and Child Health (MCH) indicators from the Pregnancy Risk Assessment Monitoring System (PRAMS) in the USA for the years 2016 through 2020.

The population is categorized across 14 indicator topics:
1. Nutrition (Multivitamin use)
2. Pre-Pregnancy Weight (Underweight, Overweight, Obese)
3. Substance Use (Cigarettes, E-Cigarettes, Hookah, Heavy Drinking)
4. Intimate Partner Violence (Before and during pregnancy)
5. Depression (Self-reported depression before, during, and postpartum)
6. Health Care Services (Flu shot, prenatal care, maternal checkup)
7. Pregnancy Intention (Intended, mistimed, unwanted, unsure)
8. Postpartum Family Planning (Sterilization, LARC, moderate, least effective methods)
9. Oral Health (Teeth cleaned during pregnancy)
10. Health Insurance Status One Month Before Pregnancy (Private, Medicaid, No Insurance)
11. Health Insurance Status for Prenatal Care (Private, Medicaid, No Insurance)
12. Health Insurance Status Postpartum (Private, Medicaid, No Insurance)
13. Infant Sleep Practices (Baby often laid on back to sleep)
14. Breastfeeding Practices (Ever breastfed, breastfeeding at 8 weeks)

Each indicator is measured across 4 statistical properties:
- **SampleSize_Count**: Sample count (`statType: dcs:sampleSize`, `measuredProperty: dcs:count`)
- **Percent**: Percentage fraction (`statType: dcs:measuredValue`, `measurementDenominator: dcs:Count_BirthEvent_LiveBirth`, `scalingFactor: 100`)
- **ConfidenceIntervalLowerLimit**: Lower CI limit (`statType: dcs:confidenceIntervalLowerLimit`)
- **ConfidenceIntervalUpperLimit**: Upper CI limit (`statType: dcs:confidenceIntervalUpperLimit`)

Total Statistical Variables: 168

### Source Download URL
The data is downloaded from the CDC PRAMS repository:
`https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/`

Example file:
`https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/Alabama-PRAMS-MCH-Indicators-508.pdf`

---

## Import Automation & Directory Structure

```
scripts/cdc_prams/
├── manifest.json              # Import automation specification (Cloud Batch/Scheduler)
├── validation_config.json     # Import validation framework configuration
├── golden_data/
│   ├── golden_observations.csv   # Golden place DCIDs for validation
│   └── golden_summary_report.csv # Golden schema and property summaries
├── download.py                # Download utility with retries, timeouts, and headers
├── download_input_files.py    # Downloads all 49 state/territory/national PDFs
├── process.py                 # Extracts PDF tables with tabula-py and produces CSV/MCF/TMCF
├── process_test.py            # Unit test comparing output against expected fixtures
├── constants.py               # MCF templates and property mappings
├── statvar.py                 # Statistical variable name mappings
├── test_data/                 # Test sample fixtures (9 PDFs and expected outputs)
└── output/                    # Generated output directory (.gitignored)
    ├── PRAMS.csv
    ├── PRAMS.mcf
    └── PRAMS.tmcf
```

---

## Running the Import

### 1. Download Input PDFs
```bash
python3 scripts/cdc_prams/download_input_files.py
```
This downloads all 49 state, NYC, DC, Puerto Rico, and national PDF files into `scripts/cdc_prams/input_files/`.

### 2. Process and Generate Output Files
```bash
python3 scripts/cdc_prams/process.py
```
This parses the downloaded PDFs and produces:
- `output/PRAMS.csv`
- `output/PRAMS.mcf`
- `output/PRAMS.tmcf`

---

## Running Tests

### Unit Tests
```bash
python3 scripts/cdc_prams/process_test.py
```
or via unittest:
```bash
python3 -m unittest scripts/cdc_prams/process_test.py
```

### Validating Against Goldens
```bash
python3 tools/import_validation/validator_goldens.py \
    --validate_goldens_input=scripts/cdc_prams/output/PRAMS.csv \
    --validate_goldens=scripts/cdc_prams/golden_data/golden_observations.csv \
    --goldens_key_property=Geo
```