# Rwanda Census

- Source: https://rwanda.opendataforafrica.org/

## Overview
This dataset contains Rwanda Census data covering Demographics, Economy, and Education across Country and AdministrativeArea1 levels for the years 2002 to 2023.

## Semi-Automated Ingestion Workflow
Due to Cloudflare bot protection on the upstream portal, programmatic scraping and browser-mimicking requests fail. These datasets can only be downloaded manually in a local browser.

### Dataset Source URLs:
| Dataset | Source URL | Description |
|---|---|---|
| `edvtatd` | https://rwanda.opendataforafrica.org/edvtatd | Population 16+ by labour force status and marital status |
| `eoefmac` | https://rwanda.opendataforafrica.org/eoefmac | Population 16+ by labour force status and educational attainment |
| `hivlaeg` | https://rwanda.opendataforafrica.org/hivlaeg | Population 16+ by labour force status, sex, age group, urban/rural |
| `kbadgkf` | https://rwanda.opendataforafrica.org/kbadgkf | Educational attainment & field of education by labour market status |
| `kwekfdd` | https://rwanda.opendataforafrica.org/kwekfdd | Employed population by sex, age group, urban/rural |
| `mnoirpd` | https://rwanda.opendataforafrica.org/mnoirpd | Summary labour force indicators |
| `qavhudd` | https://rwanda.opendataforafrica.org/qavhudd | Population 16+ by labour force status and marital status |
| `shdirje` | https://rwanda.opendataforafrica.org/shdirje | Age, gender indicators |
| `uymcezb` | https://rwanda.opendataforafrica.org/uymcezb | Consumer Price Index |
| `vafqyfg` | https://rwanda.opendataforafrica.org/vafqyfg | Employed population by sex, occupation group, urban/rural |
| `ztaoyl` | https://rwanda.opendataforafrica.org/ztaoyl | Population by sex, age group and urban/rural area |

1. **Source Data Storage**:
   Raw input CSV files are maintained in Google Cloud Storage:
   `gs://unresolved_mcf/opendataforafrica/rwanda_census/input_files/`

2. **Updating Source Files**:
   When updated census data is published, download the CSV files in a local browser from the URLs above and upload them to GCS:
   ```bash
   gcloud storage cp *.csv gs://unresolved_mcf/opendataforafrica/rwanda_census/input_files/
   ```

3. **Download Step**:
   The import script `download.sh` copies the raw CSV files from GCS to `gcs_output/input_files/`:
   ```bash
   mkdir -p gcs_output/input_files
   gcloud storage cp --recursive "gs://unresolved_mcf/opendataforafrica/rwanda_census/input_files/*" gcs_output/input_files/
   ```

## Running the Import

### Running Individual Dataset Processing:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=gcs_output/input_files/ztaoyl.csv \
  --pv_map=ztaoyl_pv_map.csv \
  --config_file=ztaoyl_metadata.csv \
  --output_path=gcs_output/output/ztaoyl
```

- If place resolution is involved (e.g. `qavhudd`), pass `--places_resolved_csv=places_resolved_csv.csv`.
- If statvar remapping is involved (e.g. `edvtatd`), pass `--statvar_dcid_remap_csv=edvtatd_statvar_remap.csv`.