library(raster)
library(tidyverse)
library(tidycensus)
library(sf)
library(stringr)
library(future.apply)
library(stats)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# Pull in non-fire data ---------------------------------------------------

forest <- raster("forest.mask/fw_mask.tif")

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


# Function to calculate mean fire severity by fire  ----------------------

calc_mean_severity <- function(countyfips, year) {
  
  print(year)
  
  # Select county and fires in selected year
  county <- counties[counties$GEOID == countyfips, ]
  county_sp <- as_Spatial(county)
  fire.annual.data <- fire.data[fire.data$year == year,]
  
  # Identify fires in year that intersect selected county  
  county.fires <- fire.annual.data[st_intersects(county, fire.annual.data)[[1]], ]
  forest_county <- crop(forest, county_sp) %>% mask(county_sp)
  forest_cells <- sum(as.vector(forest_county), na.rm = T)
  
  calc_severity_by_fire <- function(i) {
    
      r <- raster(county.fires$filename[i])
      
      forest_fire <- projectRaster(forest_crop,r)       # Project fire rasters to same extent
      
      r[forest_crop != 1] <- NA       # Restrict fire data to forested cells
      r.county <- mask(r, county_sp)  # Mask by county boundary

      forest_fire[is.na(r.county)] <- NA # Mask by county boundary
      
      mean_severity <- mean(as.vector(r.county), na.rm = T)
      fire_forest_cells <- sum(as.vector(forest_fire), na.rm = T)
      
      return(c(mean_severity,fire_forest_cells))
      
      }
  
  if (dim(county.fires)[1] > 0)  {
  
    # Find encompassing extent of all fires that intersect county in selected year
    total.extent <- extent(county.fires) %>% as('SpatialPolygons') %>% st_as_sf()
    st_crs(total.extent) <- st_crs(forest)
    
    # Crop forest to total encompassing extent of fires  
    forest_crop <- crop(forest,total.extent)
    
    severity.table <- do.call(rbind, lapply(seq(1, dim(county.fires)[1]), calc_severity_by_fire)) %>% 
      as.data.frame()
    colnames(severity.table) <- c("mean","num_cells")
    
    mean_severity <- weighted.mean(severity.table$mean, severity.table$num_cells)
    total_cells <- sum(severity.table$num_cells, na.rm = T)

  } else {
      mean_severity <- NA
      total_cells <- NA
    }
    
  return(c(countyfips,year,mean_severity,total_cells))
        
}

# Run function over counties and years ------------------------------------

tic()

for (c in counties$GEOID) {
  
  print(c)
  
  plan(multisession, workers = 6)
  stats <- do.call(rbind, future_lapply(unique(fire.data$year), function(y) calc_mean_severity(c, y))) %>%
    as.data.frame()
  colnames(stats) <- c("countyfips","year","mean_severity","total_cells")
  
  dst <- dirname(rstudioapi::getActiveDocumentContext()$path)
  dir.create(dst, recursive = T, showWarnings = F)
  write.csv(stats, sprintf("%s.csv", c))
  
}

dst <- dirname(rstudioapi::getActiveDocumentContext()$path)
files <- list.files(dst, full.names = T)
df <- do.call(rbind, lapply(files, read.csv)) %>% 
        mutate(countyfips = str_pad(countyfips, pad = "0", width = 5, side = "left"))
write.csv(df, "mean_sev_western_counties.csv")
