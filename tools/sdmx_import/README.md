# SDMX CLI

Command-line tool for downloading SDMX data and metadata from REST APIs.

## Usage

```bash
python sdmx_cli.py <command> [flags]
```

## Commands

### Download Metadata
```bash
python sdmx_cli.py download-metadata \
  --endpoint=https://sdmx.oecd.org/public/rest/ \
  --agency=OECD.SDD.NAD \
  --dataflow=DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD \
  --output_path=metadata.xml
```

### Download Data
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