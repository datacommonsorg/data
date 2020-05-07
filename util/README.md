# Utility libraries for importing data into Data Commons

This folder hosts utility libraries helpful for creating Meta Content
Framework (MCF) files that the Data Commons graph can ingest. While you
are free to use any programming language to construct JSON-LD, RDFa, or MCF
files, we suggest using Python or Golang to write MCF, which we find to be a
simple and very readable format.
To date, all our util libraries cater to writing MCF.

## Python util libraries

- `alpha2_to_dcid`: This library contains mappings from 2-character country and US
  state codes to their unique Data Commons IDs.

- `name_to_alpha2`: This library contains mappings from US state names to their
  2-character codes.

- `sharding_writer`: Data Commons strongly prefers that input files to our graph
  remain under 100 MB, so we've provided a class that will abstract writing to
  sharded files. See the file docstring for more detail.

- `mcf_template_filler`: Much of statistical data falls nicely into Schema.org's
  [StatisticalPopulation](https://schema.org/StatisticalPopulation) and
  [Observation](https://schema.org/Observation) model. We provide this
  templating library that helps handle Python string templating. See the file
  docstring for more detail.

## Golang util libraries

Coming soon.

## Testing util libraries

### Testing `mcf_template_filler`

`python3 -m unittest mcf_template_filler_test`

### Testing `sharding_writer`

Test coming soon.
