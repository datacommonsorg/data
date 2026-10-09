# US Census 2025 Gazetteer & USGS Containment Dataset

## Overview
This dataset imports and merges the 2025 US Census Gazetteer files with USGS Federal Codes. It updates foundational geographic nodes (Places, Counties, Tracts, ZCTAs, Congressional Districts, etc.) with 2025 boundary representations (land/water area), coordinates (LatLong), and Legal/Statistical Area Descriptions (LSADs), while strictly preserving historical entity identifiers and names from the Knowledge Graph.

## Data Source
**Census 2025 Gazetteer Files:**
* Source URL: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/
* Contains geographic coordinates, areas, and legal classifications for US geographies.

**USGS National Federal Codes:**
* Source URL: https://www.usgs.gov/u.s.-board-on-geographic-names
* Used to determine cross-county containment mappings (`containedInPlace`) for US Places.

## Processing Instructions
To execute the complete 2025 Gazetteer pipeline locally and generate the final MCF files, ensure you are in the project root directory and follow the steps below in order.

### Pre-requisites: USGS Federal Codes & Historical MCFs
Ensure the USGS mapping file `FederalCodes_National.txt` is manually placed inside the `gazetteer/` directory. Additionally, you must have the 2018–2022 historical MCF files placed inside the `gazetteer/hist_mcf/` directory to allow the pipeline to run the diffing and merging comparisons.

### Step 1: Download Raw Data
Execute the bash script to fetch and unzip the 2025 Gazetteer files directly from the US Census servers into the `gazetteer/raw_data_2025` directory.
```bash
 download_2025.sh
```

### Step 2: Parse Gazetteer Data to MCF
Parse the raw text files downloaded from the 2025 US Census into the standardized Data Commons MCF format. This script enforces strict historical property orderings, injects required schema prefixes (e.g., schema:City), drops unnecessary ZCTA country-level containments, and formats geographic coordinates (LatLong) and area metrics.
```bash
python3 gazetteer.py
```

### Step 3: Merge with Historical Context
Merge the newly generated 2025 MCF data directly onto the existing 2018–2022 historical MCF files. This automated pipeline handles the pure-text "Last-Writer-Wins" merge (2025 data overwrites older data) and safely injects deleted historical names back into the final nodes as alternateName to ensure no historical search context is lost in the Knowledge Graph.
```bash
python3 run_pipeline.py
```

### Step 4: Map USGS County Containment
Read the external USGS FederalCodes_National.txt file and cross-reference it against the newly merged 2025 Place MCFs. Because some cities cross multiple county lines, this script aggregates all valid county intersections for a given place and generates accurate, comma-separated geographic containment strings (containedInPlace).
```bash
python3 place_usgs.py
```