# Importing U.S. Bureau of Labor Statistics Consumer Price Index Into Data Commons

Author: intrepiditee

## Table of Contents

1.  [About the Dataset](#about-the-dataset)
2.  [About the Import](#about-the-import)

## About the Dataset

### Download URL

Xlsx and text files are available for download from
https://www.bls.gov/cpi/data.htm.

### Overview

The Consumer Price Index, short for CPI, is a measure of inflation. It is a
weighted average of market prices of goods and services purchased by consumers.
The U.S. Bureau of Labor Statistics provides datasets of different types of
CPIs. CPIs differ in their methods of calculation, the products they include in
the calculation, and the population groups.

In terms of methods of calculation, a CPI can be chained or unchained and
seasonally adjusted or unadjusted. Unchained CPIs fix the basket of goods and
calculate the prices each month. This leads to substitution bias. When the
prices of some items in the basket rise, consumers will naturally substitute
them with similar goods whose prices are not increasing as fast. Since the
basket is fixed, unchained CPIs will overestimate living expenses. Chained CPIs
try to look at what people buy in multiple months, thus "chaining" the months,
to create a more accurate estimate.

Seasonally unadjusted CPIs do not exclude the effects of some seasonal, periodic
changes. For example, in the summer, the prices for ice creams may predictably
go up. Seasonally unadjusted CPIs may indicate that inflation is higher in the
summer, but the reality is that the price increase is not a result of inflation
but normal market behavior. Seasonally adjusted CPIs try to smooth out the
effects of these seasonal fluctuations on the indices so that they measure
inflation more accurately.

BLS publishes three main types of CPIs: CPI-U, CPI-W, and C-CPI-U. CPI-U stands
for CPI for All Urban Consumers. CPI-W stands for CPI for Urban Wage Earners and
Clerical Workers. The two are both unchained and use the same basket of goods
and prices. The difference is their population group. C-CPI-U stands for Chained
CPI for All Urban Consumers. It is the chained version of CPI-U. Each of the
three can have seasonally adjusted and unadjusted series.

The StatisticalVariable for CPI-U and C-CPI-U is
`ConsumerPriceIndex_ConsumerGoodsAndServices_UrbanConsumer_BLSSeasonallyUnadjusted`,
defined in [cpi_u_1913_2020.mcf](cpi_u_1913_2020.mcf) and
[c_cpi_u_1999_2020.mcf](c_cpi_u_1999_2020.mcf).

The StatisticalVariable for CPI-W is
`ConsumerPriceIndex_ConsumerGoodsAndServices_UrbanWageEarnerAndClericalWorker_BLSSeasonallyUnadjusted`,
defined in [cpi_w_1913_2020.mcf](cpi_w_1913_2020.mcf).

### Notes and Caveats

Since CPIs can have different population groups and baskets of goods and can be
chained or unchained and seasonally adjusted or unadjusted and different
countries and areas have their own CPIs, we should have support for importing
any type of CPI into Data Commons.

### License

This dataset is in the public domain.

The license is available online at https://www.bls.gov/bls/linksite.htm.

### Dataset Documentation and Relevant Links

-   Descriptions of all available series of CPI-U:
    https://download.bls.gov/pub/time.series/cu/cu.series
-   Descriptions of all available series of CPI-W:
    https://download.bls.gov/pub/time.series/cw/cw.series
-   Description of all available series of C-CPI-U:
    https://download.bls.gov/pub/time.series/su/su.series
-   CPI method handbook: https://www.bls.gov/opub/hom/pdf/cpihom.pdf

## About the Import

### Artifacts

#### Cleaned Data

-   [c_cpi_u_1999_2020.csv](c_cpi_u_1999_2020.csv) contains seasonally
    unadjusted Chained CPI for All Urban Consumers (C-CPI-U) data from 1999
    to 2020. Series ID is "SUUR0000SA0".
-   [cpi_u_1913_2020.csv](cpi_u_1913_2020.csv) contains seasonally unadjusted
    CPI for All Urban Consumers (CPI-U) data from 1913 to 2020. Series ID is
    "CUUR0000SA0".
-   [cpi_w_1913_2020.csv](cpi_w_1913_2020.csv) contains seasonally unadjusted
    CPI for Urban Wage Earners and Clerical Workers (CPI-W) data from 1913
    to 2020. Series ID is "CWUR0000SA0".

#### Template MCFs

-   [c_cpi_u_1999_2020.tmcf](c_cpi_u_1999_2020.tmcf)
-   [cpi_u_1913_2020.tmcf](cpi_u_1913_2020.tmcf)
-   [cpi_w_1913_2020.tmcf](cpi_w_1913_2020.tmcf)

#### StatisticalVariable Instance MCF

-   [c_cpi_u_1999_2020_StatisticalVariable.mcf](c_cpi_u_1999_2020_StatisticalVariable.mcf)
-   [cpi_u_1913_2020_StatisticalVariable.mcf](cpi_u_1913_2020_StatisticalVariable.mcf)
-   [cpi_w_1913_2020_StatisticalVariable.mcf](cpi_w_1913_2020_StatisticalVariable.mcf)

#### Scripts

-   [generate_csv.py](generate_csv.py) downloads and converts BLS CPI raw csv
    files to csv files of two columns: "date" and "cpi", where "date" is of the
    form "YYYY-MM" and "cpi" is numeric.

### Import Procedure

1.  Run `python3 generate_csv.py`
