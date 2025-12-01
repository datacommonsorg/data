# SDMX CLI

Command-line tool for downloading SDMX data and metadata from REST APIs.

## Supported SDMX Version

This tool supports **SDMX 2.1** standard.

## Usage

```bash
python sdmx_cli.py <command> [flags]
```

### Required Flags

All commands require these flags:
- `--endpoint`: SDMX REST API endpoint URL
- `--agency`: Agency ID (e.g., OECD.SDD.NAD)
- `--dataflow`: Dataflow ID
- `--output_path`: Output file path

### Logging Options

- `--verbose`: Enable detailed debug logging
- `--quiet`: Show only error messages

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

> [!NOTE]
> For **Agentic Import**, the downloaded XML metadata is typically converted to a simplified JSON format. Refer to the [Agentic Import documentation](../agentic_import/README.md#sdmx-downloads) for instructions on using `sdmx_metadata_extractor.py`.

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

## Error Handling

If a download fails due to network errors or invalid requests:
- Error details are logged to console
- Response content is saved to an HTML file (e.g., `metadata_error_<dataflow>.html`, `data_error_<dataflow>.html`)
- Check the error file for detailed API response information

## Help

For detailed flag information:
```bash
python sdmx_cli.py <command> --help
```

## Programmatic Usage

The SDMX library can also be used programmatically through the `SdmxClient` class available in `sdmx_client.py`. For complete examples, see the `samples/` directory.
