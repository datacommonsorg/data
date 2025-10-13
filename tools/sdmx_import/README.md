# SDMX CLI

Command-line tool for downloading SDMX data and metadata from REST APIs.

## Supported SDMX Version

This tool supports **SDMX 2.1** standard.

## Usage

```bash
python sdmx_cli.py <command> [flags]
```

## Commands

### Download Metadata

- Downloads complete metadata for a dataflow
- Uses SDMX REST API endpoint with `references=all` parameter
- Retrieves all associated codelists, concept schemes, and data structure definitions
- Output format: SDMX-ML (XML)

```bash
python sdmx_cli.py download-metadata \
  --endpoint=https://sdmx.oecd.org/public/rest/ \
  --agency=OECD.SDD.NAD \
  --dataflow=DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD \
  --output_path=metadata.xml
```

### Download Data

- Downloads data from a dataflow
- Automatically converts to CSV format if endpoint does not provide it
- Supports filtering with key dimensions and query parameters
- Output format: CSV

```bash
python sdmx_cli.py download-data \
  --endpoint=https://sdmx.oecd.org/public/rest/ \
  --agency=OECD.SDD.NAD \
  --dataflow=DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD \
  --key=FREQ:Q --key=REF_AREA:USA \
  --param=startPeriod:2022 \
  --output_path=data.csv
```

## Help

For detailed flag information:
```bash
python sdmx_cli.py <command> --help
```