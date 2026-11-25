# Utility libraries for importing data into Data Commons

## Table of contents

- [Python](#python)
  - [Python util libraries](#python-util-libraries)
  - [Python testing libraries](#python-testing-libraries)
- [Go](#go)
  - [Go util libraries](#go-util-libraries)
  - [Go testing libraries](#go-testing-libraries)

This folder hosts utility libraries helpful for creating Meta Content Framework
(MCF) files that the Data Commons graph can ingest. While you are free to use
any programming language to construct JSON-LD, RDFa, or MCF files, we suggest
using Python or Golang to write MCF, which we find to be a simple and very
readable format.

To date, all our util libraries cater to writing MCF.

## Python

### Python util libraries

-   `alpha2_to_dcid`: This library contains mappings from 2-character country
    and US state codes to their unique Data Commons IDs.

-   `file_dict_io`: Reads and writes structured records (CSV, TSV, JSON,
    JSON Lines, MCF, Avro, and sharded file collections) as Python dictionaries,
    with seekable byte-range chunking for parallel workers. See the
    [`file_dict_io` documentation](file_dict_io/README.md).

-   `file_sharder`: Partitions large tabular and graph datasets into sharded
    output files by key hash, row count, or fixed shard count with
    multi-threaded chunk processing, deduplication, and sampling. See the
    [File Sharder documentation](doc/file_sharder.md).

-   `latlng_recon_geojson`: This library helps map lat/lng coordinate pairs to
    US States, Countries and Continents.  It does so by using the GeoJSONs from
    DC KG, and this is reasonably fast for a large number of lat/lng pairs.

-   `latlng_recon_service`: This library helps map lat/lng coordinate pairs, in
    bulk, to all DC geos that we have boundaries for (like countries, Eurostat
    NUTS, India/Pak/Bangla districts, US states/zip/school-districts, and so
    on).  It does so by calling the Recon Service.  Although the calls are
    batched, this is slow owing to the API latencies (e.g., a few seconds for
    100 lat/lngs).  So prefer the `_geojson` version unless you want
    fine-grained geos.

-   `latlng2place_mapsapi`: This library helps map a lat/lng coordinate pair to
    list of admin-area and country geos by using the Maps API to find the
    place-ids, and then the DC recon API to map to DCIDs.  The advantage of this
    over the `latlng_recon_*` APIs is that we do not depend on the existence of
    GeoJSONs for admin-areas in the KG for resolution.

    NOTE: As of Oct 2022, only a small subset of countries have sub-national
    geojsons.  So, for resolving non-US lat/lngs to sub-national DCIDs, this is
    the preferred library to use.

-   `mcf_template_filler`: Much of statistical data falls nicely into
    Schema.org's
    [StatisticalPopulation](https://schema.org/StatisticalPopulation) and
    [Observation](https://schema.org/Observation) model. We provide this
    templating library that helps handle Python string templating. See the file
    docstring for more detail.

-   `name_to_alpha2`: This library contains mappings from US state names to
    their 2-character codes.

-   `sharding_writer`: Data Commons strongly prefers that input files to our
    graph remain under 100 MB, so we've provided a class that will abstract
    writing to sharded files. See the file docstring for more detail.

-   `dcid_generator`: Generates deterministic Data Commons IDs (`dcid`) for
    `StatVarObservation` (`dc/o/<id>` via 64-bit FarmHash),
    `StatisticalVariable` (`dc/<id>`), `Place`, and general MCF graph nodes
    (matching `DcidGenerator.java` in `datacommonsorg/import`).

-   `statvar_dcid_generator`: This library helps to generate the dcid for
    statistical variables.

### Python testing libraries

#### Testing `mcf_template_filler`

`python3 -m unittest mcf_template_filler_test`

#### Testing `dcid_generator`

`python3 -m unittest dcid_generator_test.py`

#### Testing `statvar_dcid_generator`

`python3 -m unittest statvar_dcid_generator_test.py`

#### Testing `sharding_writer`

Test coming soon.

#### Testing `file_sharder`

`python3 -m unittest file_sharder_test.py`

#### Testing `file_dict_io`

`python3 -m unittest discover -s file_dict_io -p "*_test.py"`

## Go

### Go util libraries

-   `util/geo`: This package contains various mappings between geographic
    identifiers (such as 2-character country codes) and Data Commons IDs.

-   `util/sharding_writer`: This package implements an io.Writer that shard
    files to a given size boundary to help match Data Common's preference of
    input files remaining under 100 MB.

Additional libraries coming soon.

### Go testing libraries

To test all the packages within the util tree:

```
go test ./util/...
```
