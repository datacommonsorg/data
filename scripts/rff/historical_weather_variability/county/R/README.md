# RFF's R code for Weather Variability Computation

The code in this folder is authored by Hannah Druckenmiller
(hdruckenmiller@rff.org), and produces the cleaned CSV used together with
[WeatherVariability_Additional_Counties.tmcf](../WeatherVariability_Additional_Counties.tmcf).

The `main.R` script runs the whole process from start to finish, but it will
take several days to complete on RFF server.

This will need the following two sets of source data from PRISM:

* PRISM daily tmin, to be extracted under
  `rff/raw_data/prism/daily/4km/src/tmin`. Daily minimum temperature data from
  PRISM can be downloaded from https://prism.oregonstate.edu/recent/ for the
  years 1981 to present.
  *  Select "minimum temperature" under the Climate variable heading and "daily
     data" under the Temporal period heading. You can then download one full
     year of daily values at a time using the "Download All Data for Year
     (.bil)" button.

* PRISM monthly tmin, tmax, and ppt to be extracted under
  `rff/raw_data/prism/monthly`.  Monthly PRISM data can be downloaded from
  https://prism.oregonstate.edu/recent/ for the years 1981 to present.
  *  Select the climate variable (precipitation, minimum temperature, or maximum
     temperature) and then choose "monthly data" under the Temporal period
     heading.  You can download all monthly values for the 40-year time period
     at once using the "Download All Data for All Years (.bil)" button.

Terms of Use:
* When using these data, please clearly and prominently state the PRISM Climate
  Group and their URL.
* According to PRISM’s terms of use, these data may be freely reproduced and
  distributed for non-commercial purposes only.
