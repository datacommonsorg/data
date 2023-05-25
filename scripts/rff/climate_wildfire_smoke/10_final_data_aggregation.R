if (!require("pacman")) install.packages("pacman")
pacman::p_load(tidyverse,
               readr)


setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

forest_burned_acres_county <- read_csv("forest_burned_acres/forest_burned_acres_county") %>% select(-1) %>%
  rename(Date = year, Geoid = countyfips) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))

forest_burned_acres_county_decadal <- read_csv("forest_burned_acres/forest_burned_acres_county_decadal") %>% select(-1) %>%
  rename(Date = decade, Geoid = countyfips, forest_burned_acres = variable) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(Date, 1, 4)))

forest_burned_acres_state <- read_csv("forest_burned_acres/forest_burned_acres_state") %>% select(-1) %>%
  rename(Date = year, Geoid = st_fips, forest_burned_acres = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))

forest_burned_acres_state_decadal <- read_csv("forest_burned_acres/forest_burned_acres_state_decadal") %>% select(-1) %>%
  rename(Date = decade, Geoid = st_fips, forest_burned_acres = variable) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(Date, 1, 4)))

forest_burned_acres_west <- read_csv("forest_burned_acres/forest_burned_acres_west") %>% select(-1) %>%
  rename(Date = year, forest_burned_acres = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4')

forest_burned_acres_west_decadal <- read_csv("forest_burned_acres/forest_burned_acres_west_decadal") %>% select(-1)  %>%
  rename(forest_burned_acres = variable, Date = decade) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = 'dcid:geoId/4', Date = as.numeric(substr(Date, 1, 4)))

forest_burned_acres =  bind_rows(forest_burned_acres_county, forest_burned_acres_county_decadal, 
                                  forest_burned_acres_state, forest_burned_acres_state_decadal,
                                  forest_burned_acres_west, forest_burned_acres_west_decadal)

pct_forest_burned_county <- read_csv("pct_forest_burned/pct_forest_burned_county") %>% select(-1) %>%
  rename(Date = year, Geoid = countyfips) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid), pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned_county_decadal <- read_csv("pct_forest_burned/pct_forest_burned_county_decadal") %>% select(-1) %>%
  rename(Date = decade, Geoid = countyfips, pct_forest_burned = variable) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(Date, 1, 4)), pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned_state <- read_csv("pct_forest_burned/pct_forest_burned_state") %>% select(-1) %>%
  rename(Date = year, Geoid = st_fips, pct_forest_burned = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid), pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned_state_decadal <- read_csv("pct_forest_burned/pct_forest_burned_state_decadal") %>% select(-1) %>%
  rename(Date = decade, Geoid = st_fips, pct_forest_burned = variable) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(Date, 1, 4)), pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned_west <- read_csv("pct_forest_burned/pct_forest_burned_west") %>% select(-1) %>%
  rename(Date = year, pct_forest_burned = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4', pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned_west_decadal <- read_csv("pct_forest_burned/pct_forest_burned_west_decadal") %>% select(-1)  %>%
  rename(pct_forest_burned = variable, Date = decade) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = 'dcid:geoId/4', Date = as.numeric(substr(Date, 1, 4)), pct_forest_burned = pct_forest_burned * 100)

pct_forest_burned =  bind_rows(pct_forest_burned_county, pct_forest_burned_county_decadal, 
                                 pct_forest_burned_state, pct_forest_burned_state_decadal,
                                 pct_forest_burned_west, pct_forest_burned_west_decadal)

pct_high_severity_county <- read_csv("pct_high_severity/pct_high_severity_county") %>% select(-1) %>%
  rename(Date = year, Geoid = countyfips) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid), pct_high_severity = pct_high_severity * 100)

pct_high_severity_state <- read_csv("pct_high_severity/pct_high_severity_state") %>% select(-1) %>%
  rename(Date = year, Geoid = st_fips, pct_high_severity = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid), pct_high_severity = pct_high_severity * 100)

pct_high_severity_west <- read_csv("pct_high_severity/pct_high_severity_west") %>% select(-1) %>%
  rename(Date = year, pct_high_severity = variable) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4', pct_high_severity = pct_high_severity * 100)

pct_high_severity =  bind_rows(pct_high_severity_county, 
                               pct_high_severity_state,
                               pct_high_severity_west)

PDSI_county <- read_csv("climate/PDSI_county.csv") %>%
  rename(Date = year, Geoid = county, mean_pdsi_forestarea = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
PDSI_state <- read_csv("climate/PDSI_state.csv") %>%
  rename(Date = year, Geoid = state, mean_pdsi_forestarea = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
PDSI_west <- read_csv("climate/PDSI_west.csv") %>%
  rename(Date = year, mean_pdsi_forestarea = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4')

PDSI =  bind_rows(PDSI_county, 
                  PDSI_state,
                  PDSI_west)

tmax_county <- read_csv("climate/tmax_county.csv") %>%
  rename(Date = year, Geoid = county, mean_tmax_forestarea = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
tmax_state <- read_csv("climate/tmax_state.csv") %>%
  rename(Date = year, Geoid = state, mean_tmax_forestarea = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
tmax_west <- read_csv("climate/tmax_west.csv") %>%
  rename(Date = year, mean_tmax_forestarea = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4')

tmax =  bind_rows(tmax_county, 
                  tmax_state,
                  tmax_west)

VPD_county <- read_csv("climate/VPD_county.csv") %>%
  rename(Date = year, Geoid = county, mean_vpd_forestarea = max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
VPD_state <- read_csv("climate/VPD_state.csv") %>%
  rename(Date = year, Geoid = state, mean_vpd_forestarea = max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
VPD_west <- read_csv("climate/VPD_west.csv") %>%
  rename(Date = year, mean_vpd_forestarea = mean_max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/4')

VPD =  bind_rows(VPD_county, 
                  VPD_state,
                  VPD_west)

VPD_county_allarea <- read_csv("climate/VPD_county_allarea.csv") %>%
  rename(Date = year, Geoid = county, mean_vpd_county = mean_max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
VPD_state_allarea <- read_csv("climate/VPD_state_allarea.csv") %>%
  rename(Date = year, Geoid = state, mean_vpd_county = mean_max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
VPD_west_allarea <- read_csv("climate/VPD_us_allarea.csv") %>%
  rename(Date = year, mean_vpd_county = mean_max_vpd) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/US')

VPD_allarea =  bind_rows(VPD_county_allarea, 
                 VPD_state_allarea,
                 VPD_west_allarea)

tmax_county_allarea <- read_csv("climate/tmax_county_allarea.csv") %>%
  rename(Date = year, Geoid = county, mean_tmax_county = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
tmax_state_allarea <- read_csv("climate/tmax_state_allarea.csv") %>%
  rename(Date = year, Geoid = state, mean_tmax_county = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
tmax_west_allarea <- read_csv("climate/tmax_us_allarea.csv") %>%
  rename(Date = year, mean_tmax_county = mean_tmax) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/US')

tmax_allarea =  bind_rows(tmax_county_allarea, 
                         tmax_state_allarea,
                         tmax_west_allarea)

PDSI_county_allarea <- read_csv("climate/PDSI_county_allarea.csv") %>%
  rename(Date = year, Geoid = county, mean_pdsi_county = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
PDSI_state_allarea <- read_csv("climate/PDSI_state_allarea.csv") %>%
  rename(Date = year, Geoid = state, mean_pdsi_county = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid))
PDSI_west_allarea <- read_csv("climate/PDSI_us_allarea.csv") %>%
  rename(Date = year, mean_pdsi_county = mean_pdsi) %>% mutate(TimeIntervalType = 'P1Y', Geoid = 'dcid:geoId/US')

PDSI_allarea =  bind_rows(PDSI_county_allarea, 
                          PDSI_state_allarea,
                          PDSI_west_allarea)


mtbs_county <- read_csv("mtbs_county.csv") %>% rename(area = county_area, Geoid = fips)

mtbs_state = mtbs_county %>%
  group_by(year, Geoid = substr(Geoid, 1, 2)) %>%
  summarize(area_burned = sum(area_burned),
            area = sum(area)) %>% ungroup %>% filter(Geoid != '72')

mtbs_region = mtbs_state %>%
  mutate(Geoid = case_when(
    Geoid %in% c('09', '23', '25', '33', '44', '50', '34', '36', '42') ~ '1',
    Geoid %in% c('18', '17', '26', '39', '55', '19', '20', '27', '29', '31', '38', '46') ~ '2',
    Geoid %in% c('10', '11', '12', '13', '24', '37', '45', '51', '54', '01', '21', '28', '47', '05', '22', '40', '48') ~ '3',
    Geoid %in% c('04', '08', '16', '35', '30', '49', '32', '56', '02', '06', '15', '41', '53') ~ '4')) %>%
  group_by(year, Geoid) %>%
  summarize(area_burned = sum(area_burned),
            area = sum(area)) %>% ungroup

mtbs_us = mtbs_region %>%
  group_by(year) %>%
  summarize(area_burned = sum(area_burned),
            area = sum(area)) %>% 
  ungroup %>% mutate(Geoid = str_c('US'))

decade_county = mtbs_county %>% 
  mutate(decade = (year - 1) %/% 10) %>% 
  group_by(decade, Geoid) %>% 
  mutate(decade = paste(range(year), collapse="-")) %>% 
  group_by(decade, Geoid) %>% summarise(area_burned=mean(area_burned), area=mean(area)) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(decade, 1, 4))) %>%
  ungroup %>% select(-decade)

decade_state = mtbs_state %>% 
  mutate(decade = (year - 1) %/% 10) %>% 
  group_by(decade, Geoid) %>% 
  mutate(decade = paste(range(year), collapse="-")) %>% 
  group_by(decade, Geoid) %>% summarise(area_burned=mean(area_burned), area=mean(area)) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(decade, 1, 4))) %>%
  ungroup %>% select(-decade)

decade_region = mtbs_region %>% 
  mutate(decade = (year - 1) %/% 10) %>% 
  group_by(decade, Geoid) %>% 
  mutate(decade = paste(range(year), collapse="-")) %>% 
  group_by(decade, Geoid) %>% summarise(area_burned=mean(area_burned), area=mean(area)) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = str_c('dcid:geoId/', Geoid), Date = as.numeric(substr(decade, 1, 4))) %>%
  ungroup %>% select(-decade)

decade_us = mtbs_us %>% 
  mutate(decade = (year - 1) %/% 10) %>% 
  group_by(decade) %>% 
  mutate(decade = paste(range(year), collapse="-")) %>% 
  group_by(decade) %>% summarise(area_burned=mean(area_burned), area=mean(area)) %>% 
  mutate(TimeIntervalType = 'P10Y', Geoid = 'dcid:geoId/US', Date = as.numeric(substr(decade, 1, 4))) %>% select(-decade)

decade_mtbs = bind_rows(decade_us, decade_region, decade_state, decade_county)
bind_mtbs = bind_rows(mtbs_us, mtbs_region, mtbs_state, mtbs_county) %>% 
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', Geoid)) %>% rename(Date = year)
bind_mtbs = bind_rows(decade_mtbs, bind_mtbs) %>%
  mutate(pct_area_burned = area_burned / area * 100) %>% select(-area)


heatwave <- read_csv("climate/national_heatwave.csv") %>% select(-1) %>%
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/US')) %>%
  rename(Date = YEAR)

heatwave_state <- read_csv("climate/state_heatwave.csv") %>% select(-1) %>%
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', STATEFP)) %>%
  rename(Date = YEAR) %>% select(-STATEFP)

state_smokePM <- read_csv("state_smokePM.csv") %>% select(-1) %>%
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', STATEFP)) %>%
  rename(Date = YEAR) %>% select(-STATEFP)

national_smokePM <- read_csv("national_smokePM.csv") %>% select(-1) %>%
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/US')) %>%
  rename(Date = YEAR)

smoke_heatwave =  bind_rows(heatwave, 
                            heatwave_state,
                            state_smokePM,
                            national_smokePM)

smokePM25_annual_county_stats <- read_csv("smokePM25_annual_county_stats.csv") %>% 
  mutate(TimeIntervalType = 'P1Y', Geoid = str_c('dcid:geoId/', str_pad(GEOID, 5, 'left', '0'))) %>%
  rename(Date = year) %>% select(-GEOID)
smokePM25_5year_county_stats_revised <- read_csv("smokePM25_5year_county_stats_revised.csv") %>% 
  mutate(TimeIntervalType = 'P5Y', Geoid = str_c('dcid:geoId/', str_pad(GEOID, 5, 'left', '0'))) %>%
  rename(Date = year) %>% select(-GEOID)

smoke_pm25 =  bind_rows(smokePM25_annual_county_stats, 
                            smokePM25_5year_county_stats_revised)

merge1 = merge(forest_burned_acres, pct_forest_burned, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge2 = merge(merge1, pct_high_severity, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge3 = merge(merge2, bind_mtbs, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)


pm25_smokepm25_merged <- read_csv("pm25_smokepm25_merged.csv") %>%
  mutate(TimeIntervalType = 'P1D', Geoid = str_c('dcid:geoId/', fips)) %>% 
  select(-fips, -year) %>% rename(Date = date) %>% mutate(Date = as.character(Date))

merge5 = merge(merge3, PDSI, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge6 = merge(merge5, tmax, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge7 = merge(merge6, VPD, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge8 = merge(merge7, VPD_allarea, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge9 = merge(merge8, PDSI_allarea, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge10 = merge(merge9, tmax_allarea, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge11 = merge(merge10, smoke_heatwave, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)
merge12 = merge(merge11, smoke_pm25, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)

merge4 = merge(merge12, pm25_smokepm25_merged, by = c('Geoid', 'Date', 'TimeIntervalType'), all = TRUE)


write_csv(merge4, "all_merged.csv", na="")

