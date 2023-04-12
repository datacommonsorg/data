## Load/install packages
if (!require("pacman")) install.packages("pacman")
pacman::p_load(tidyverse,
               dplyr,
               ggplot2,
               raster,
               tidync,
               sf,
               future.apply,
               tidycensus,
               stars,
               data.table)

`%ni%` <- Negate(`%in%`)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# Import data -------------------------------------------------------------

counties <- get_acs(geography = "county", variables = "B19013_001", year = 2020, geometry = TRUE)

smoke <- read.csv("smokePM2pt5_predictions_daily_county_20060101-20201231.csv") %>% 
          mutate(GEOID = str_pad(GEOID, width = 5, side = "left", pad = "0")) %>% 
          as.data.table()

# Note: smoke data set does not include records for every day, only days with smoke
# Expand data set to ensure there is at least one record for each county in each year
county_years <- expand.grid(counties$GEOID, seq(2006,2020))
colnames(county_years) <- c("GEOID", "year")
smoke <- merge(smoke, county_years, by = c("GEOID","year"), all.y = TRUE)

# Calculate summary statistics --------------------------------------------

# Summary statistics needed:

# Mean daily PM2.5

# Annual max PM2.5

# Number of days with PM2.5 above 12, 35.4, 55.4, 150.4, 250.4
# These numbers are breakpoints for the AQI for PM2.5, from the EPA 2012 AQI Factsheet:
# https://www.epa.gov/sites/default/files/2016-04/documents/2012_aqi_factsheet.pdf
# Note that this will be PM2.5 from smoke, not total PM2.5

smoke_ann <- smoke[ , ':=' (year = as.numeric(substr(date,1,4)),
                          month = as.numeric(substr(date,5,6)),
                          day = as.numeric(substr(date,7,8))) ] %>% 
              .[ , .(days12 = sum(as.numeric(smokePM_pred > 12), na.rm = TRUE),
                         days35 = sum(as.numeric(smokePM_pred > 35.4), na.rm = TRUE),
                         days55 = sum(as.numeric(smokePM_pred > 55.4), na.rm = TRUE ),
                         days150 = sum(as.numeric(smokePM_pred > 150.4), na.rm = TRUE),
                         days250 = sum(as.numeric(smokePM_pred > 250.4), na.rm = TRUE),
                         ann_mean_smokePM = mean(smokePM_pred, na.rm = TRUE),
                         ann_max_smokePM = max(smokePM_pred, na.rm = TRUE)),
                 by = c("GEOID","year")] 


write.csv(smoke_ann, "smokePM25_annual_county_stats.csv")



