library(raster)
library(tidyverse)
library(tidycensus)
library(sf)
library(stringr)
library(future.apply)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# Pull in non-fire data ---------------------------------------------------

forest <- raster("forest.mask/fw_mask.tif")

#pull demographic information from ACS of a given year at the zcta level, with geometry 
western_states <- c("AZ","CA","CO","ID","MT","NM","NV","OR","UT","WA","WY")
counties <- get_acs(state = western_states, geography = "county", 
                    variables = "B19301_001", 
                    year = 2019, geometry = TRUE) %>% 
                st_transform(crs(forest))


# Create fire data --------------------------------------------------------

regions <- c("CAC","NM","SW","WM")

fires <- lapply(regions, function(r) 
                  list.files(sprintf("fire.severity/%s/", r), 
                             pattern = "*_CBI_bc_prj.tif", full.names = TRUE)) %>% unlist()
files <- lapply(fires, function(f) str_split(f,"/")[[1]][6]) %>% unlist()
ids <- lapply(files, function(f) str_split(f,"_")[[1]][1]) %>% unlist()
dates <- lapply(ids, function(i) substr(i, str_length(i)-7,str_length(i))) %>% unlist()

# Create fire extent field
get_fire_extent <- function(filename) {

  r <- raster(filename)
  
  fire_extent <- as(extent(r), 'SpatialPolygons') %>% st_as_sf()
  st_crs(fire_extent) <- st_crs(forest)
  
  return(fire_extent$geometry)
  
}

extents <- do.call(rbind, lapply(fires, get_fire_extent))

fire.data <- data.frame(filename = fires, 
                        year = substr(dates,1,4),
                        month = substr(dates,5,6),
                        day = substr(dates,7,8),
                        geometry = extents)
st_geometry(fire.data) <- "geometry"
st_crs(fire.data) <- st_crs(forest)



# Function to calculate fire statistics by county and year ----------------

calc_county_fire_stats <- function(countyfips, year) {
  
  print(year)
  
  # Select county and fires in selected year
  county <- counties[counties$GEOID == countyfips, ]
  county_sp <- as_Spatial(county)
  fire.annual.data <- fire.data[fire.data$year == year,]

  # Identify fires in year that interesect selected county  
  county.fires <- fire.annual.data[st_intersects(county, fire.annual.data)[[1]], ]
  forest_county <- crop(forest, county_sp) %>% mask(county_sp)
  forest_cells <- sum(as.vector(forest_county), na.rm = T)
  
  if (dim(county.fires)[1] > 0) {
  
    # Find encompassing extent of all fires that intersect county in selected year
    total.extent <- extent(county.fires) %>% as('SpatialPolygons') %>% st_as_sf()
    st_crs(total.extent) <- st_crs(forest)
  
    # Crop forest to total encompassing extent of fires  
    forest_crop <- crop(forest,total.extent)
    
    # Combine fires into single raster with value equal to number of times cell burned
    for (i in seq(1,dim(county.fires)[1])) {
  
        r <- raster(county.fires$filename[i])
    
        # Project fire rasters to same extent
        r.project <- projectRaster(r,forest_crop)
    
        r.bin <- raster(r.project)
        r.bin[!is.na(r.project)] <- 1
        r.bin[is.na(r.bin)] <- 0
        
        r.high <- raster(r.project)
        r.high[r.project >= 2.25] <- 1
        r.high[r.project < 2.25] <- 0
        r.high[is.na(r.high)] <- 0

        if (i == 1) { 
          combined <- r.bin 
          combined_high <- r.high
        } else { 
          combined <- raster::mosaic(combined, r.bin, fun = sum)
          combined_high <- raster::mosaic(combined_high, r.high, fun = sum)
          }
        }
    
    # Restrict combined fires to forested area
    combined[forest_crop == 0] <- 0
    combined_high[forest_crop == 0] <- 0
    
    # Make binary raster from combined fire raster to account for possibility that area burned more than
    combined_bin <- raster(combined)
    combined_bin[combined > 0 & !is.na(combined)] <- 1
    # For percent burned at high severity, don't want binary measure
    
    # Mask to county area
    combined_county <- mask(combined, county_sp)
    combined_bin_county <- mask(combined_bin, county_sp)
    combined_high_county <- mask(combined_high, county_sp)
  
    # Calculate percentage forest area burned
    burned_cells <- sum(as.vector(combined_bin_county), na.rm = T)
    
    # Calculated percent burned at high severity
    high_severity <- sum(as.vector(combined_high_county), na.rm = T)
    burned_county <- sum(as.vector(combined_county), na.rm = T) # Total forested cells burned in a given year (needed for calculating weighted averages)
    
    pct_forest_burned <- burned_cells/forest_cells # Share of county forested area burned in a given year
    pct_high_severity <- high_severity/burned_county # Share of forested area burned at high severity
        
  } else { 
    
    pct_forest_burned <- 0
    pct_high_severity <- NA
    burned_county <- 0
    
    }
  
  return(c(countyfips, year, pct_forest_burned, pct_high_severity, forest_cells, burned_county))
  
}


# Run function over counties and years ------------------------------------

tic()

for (c in counties$GEOID) {

  print(c)
  
  plan(multisession, workers = 6)
  stats <- do.call(rbind, future_lapply(unique(fire.data$year), function(y) calc_county_fire_stats(c, y))) %>%
              as.data.frame()
  colnames(stats) <- c("countyfips","year","pct_forest_burned", "pct_high_severity", "forest_cells", "burned_cells")
  
  dst <- "fire/aab/counties/"
  dir.create(dst, recursive = T, showWarnings = F)
  write.csv(stats, sprintf("fire/aab/counties/%s.csv", c))

}

toc()

dst <- dirname(rstudioapi::getActiveDocumentContext()$path)
files <- list.files(dst, full.names = T)
df <- do.call(rbind, lapply(files, read.csv)) %>% 
  mutate(countyfips = str_pad(countyfips, pad = "0", width = 5, side = "left"))
write.csv(df, "aab_western_counties.csv")

