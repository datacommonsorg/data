# Utility libraries for importing data into Data Commons

[TOC]

This folder hosts utility libraries helpful for creating Meta Content Framework
(MCF) files that the Data Commons graph can ingest. While you are free to use
any programming language to construct JSON-LD, RDFa, or MCF files, we suggest
using Python or Golang to write MCF, which we find to be a simple and very
readable format.

To date, all our util libraries cater to writing MCF.

## Python

### Util libraries

-   `alpha2_to_dcid`: This library contains mappings from 2-character country
    and US state codes to their unique Data Commons IDs.

-   `name_to_alpha2`: This library contains mappings from US state names to
    their 2-character codes.

-   `sharding_writer`: Data Commons strongly prefers that input files to our
    graph remain under 100 MB, so we've provided a class that will abstract
    writing to sharded files. See the file docstring for more detail.

-   `mcf_template_filler`: Much of statistical data falls nicely into
    Schema.org's
    [StatisticalPopulation](https://schema.org/StatisticalPopulation) and
    [Observation](https://schema.org/Observation) model. We provide this
    templating library that helps handle Python string templating. See the file
    docstring for more detail.

-   `statvar_dcid_generator`: This library helps to generate the dcid for
    statistical variables.
 
### Testing libraries

#### Testing `mcf_template_filler`

`python3 -m unittest mcf_template_filler_test`

#### Testing `statvar_dcid_generator`

`python3 -m unittest statvar_dcid_generator_test.py`

#### Testing `sharding_writer`

Test coming soon.

## Go

### Util libraries

-   `util/geo`: This package contains various mappings between geographic
    identifiers (such as 2-character country codes) and Data Commons IDs.

-   `util/sharding_writer`: This package implements an io.Writer that shard
    files to a given size boundary to help match Data Common's preference of
    input files remaining under 100 MB.

Additional libraries coming soon.

### Testing libraries

To test all the packages within the util tree:

```
go test ./util/...
```
