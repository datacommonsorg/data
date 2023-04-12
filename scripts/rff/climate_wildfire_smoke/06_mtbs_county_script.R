library(tidycensus)
library(sf)
library(tidyverse)
library(units)
library(data.table)

# Set directory to project directory
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Read in fire data
fire_data = st_read('mtbs_perims_DD.dbf')

# Read in county data
counties = get_acs(geography = "county", variables = "B19013_001", year = 2020, geometry = TRUE)

# Project both datasets to the same projection, suitable for calculating area, e.g. Albers
fire_data = st_transform(fire_data, crs = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96")
counties = st_transform(counties, crs = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96")

fire_data = fire_data %>% mutate(fire_year = str_sub(Event_ID,-8,-5))

# Function to calculate area burned in a given county and year 
calc_county_fire_area_burned = function(county_fips, year) {
  # Filter the fire data to only include the specified year
  fires = fire_data %>% filter(fire_year == year)
  
  # Filter the county data to only include the specified county
  county = counties %>% filter(GEOID == county_fips)
  
  # Identify fires that intersect the county
  fires_intersect = st_intersection(fires, county)
  
  # Plotting, comment out for the actual loops
  # plot(county$geometry, axes = TRUE)
  # plot(fires_intersect$geometry, axes = TRUE, add = TRUE)
  # plot(fires_intersect$geometry, add = TRUE, col = 'red')
  
  
  # Calculate the total area of fires in acres
  fire_area = sum(units::set_units(st_area(fires_intersect), 'acres'))
  
  # Calculate the total area of the county in acres
  #county_area = sum(county$acres)

  county_area = units::set_units(st_area(county), 'acres') 
  
  return(list(county_fips, year, fire_area, county_area))
}

# Loop over counties and years
df = do.call(rbind, lapply(unique(counties$GEOID), function(c) {
  do.call(rbind, lapply(unique(fire_data$fire_year), function(y) {
    calc_county_fire_area_burned(c, y)
  }))
}))

write_csv(df, "mtbs_county.csv")


# Some sample tests

lake_county = calc_county_fire_area_burned('06033', 2020)

trinity_county = calc_county_fire_area_burned('06105', 2020)

shasta_county = calc_county_fire_area_burned('06089', 2020)

