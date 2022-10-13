# RFF's R code for Weather Variability Computation

The code in this folder is authored by Hannah Druckenmiller
(hdruckenmiller@rff.org), and produces the cleaned CSV used together with
[../WeatherVariability_Additional_Counties.tmcf](WeatherVariability_Additional_Counties.tmcf).

The MASTER.R script runs the whole process from start to finish, but it will
take several days to complete on RFF server.

This will need the following two sets of source data from PRISM:

* PRISM daily tmin, to be extracted under
  `rff/raw_data/prism/daily/4km/src/tmin`
* PRISM monthly tmin, tmax, and ppt to be extracted under
  `rff/raw_data/prism/monthly`

TODO: Add license

TODO: Find pointers for the above datasets
