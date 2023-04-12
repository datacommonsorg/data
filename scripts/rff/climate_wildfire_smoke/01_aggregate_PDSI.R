library(ncdf4) 
library(raster) 
library(rgdal) 

path <- dirname(rstudioapi::getActiveDocumentContext()$path)

  
# FOREST MASK 
# Source: Parks & Abatzoglou (2020) https://datadryad.org/stash/dataset/doi:10.5061/dryad.tmpg4f4x1
forest <- raster(paste0(path, "doi_10.5061_dryad.tmpg4f4x1__v3/forest.mask/fw_mask.tif"))
forest <- aggregate(forest, fact = 10)
writeRaster(forest, paste0(path, "forest_raster.tif"), format = "GTiff", overwrite = T)

# ADMIN BOUNDARIES 
counties <- tigris::counties(cb=T)
western_states <- c("53", "41", "06", "16", "32", "30", "56", "49", "04", "08", "35")
counties <- subset(counties, STATEFP %in% western_states)
counties <- as(counties, 'Spatial')

# PDSI 
# Source: http://thredds.northwestknowledge.net/thredds/ncss/grid/agg_met_pdsi_1979_CurrentYear_CONUS.nc/dataset.html

nc_data <- nc_open(paste0(path, "agg_met_pdsi_1981_CurrentYear_CONUS.nc"))
print(nc_data)

lon <- ncvar_get(nc_data, "lon")
lat <- ncvar_get(nc_data, "lat")
day <- ncvar_get(nc_data, "day")

dates <- as.Date(day, origin = '1900-01-01')

array <- ncvar_get(nc_data, "daily_mean_palmer_drought_severity_index")

fillvalue <- ncatt_get(nc_data, "daily_mean_palmer_drought_severity_index", "_FillValue")
fillvalue

nc_close(nc_data) 

array[array == fillvalue$value] <- NA
slice <- array[, , 1]
r <- raster(t(slice), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat), crs=CRS("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs+ towgs84=0,0,0"))

# Create forested area weights 
mask <- projectRaster(forest, r)
forest_points <- as.data.frame(rasterToPoints(mask))
colnames(forest_points)[3] <- "forest_cover"
sp <- SpatialPoints(forest_points[,c("x", "y")])
proj4string(sp) <- proj4string(mask)

counties <- spTransform(counties, proj4string(mask))
  
over <- over(sp, counties)
forest_points$state <- over$STATEFP
forest_points$county <- over$GEOID
forest_points <- subset(forest_points, !is.na(county))

county_forest_totals <- aggregate(forest_points$forest_cover, by = list(forest_points$county), FUN = "sum")
colnames(county_forest_totals) <- c("county", "county_forest_sum")
forest_points <- merge(forest_points, county_forest_totals, by = "county")

state_forest_totals <- aggregate(forest_points$forest_cover, by = list(forest_points$state), FUN = "sum")
colnames(state_forest_totals) <- c("state", "state_forest_sum")
forest_points <- merge(forest_points, state_forest_totals, by = "state")

forest_points$west_forest_sum <- sum(forest_points$forest_cover)

forest_points$county_forest_weights <- forest_points$forest_cover/forest_points$county_forest_sum
forest_points$state_forest_weights <- forest_points$forest_cover/forest_points$state_forest_sum
forest_points$west_forest_weights <- forest_points$forest_cover/forest_points$west_forest_sum

write.csv(forest_points, paste0(path, "forest_weights_PDSI.csv"), row.names = F)

west_pdsi <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_pdsi) <- c("year", "mean_pdsi")
west_pdsi$year <- 1981:2020

years <- c(1986:2020)
for(year in years){
  print(year)
  if(year %in% c(1981, 1986, 1991, 1996, 2001, 2006, 2011, 2016)){
    nc_data <- nc_open(paste0(path, "agg_met_pdsi_", year, "_CurrentYear_CONUS.nc"))
    lon <- ncvar_get(nc_data, "lon")
    lat <- ncvar_get(nc_data, "lat")
    day <- ncvar_get(nc_data, "day")
    dates <- as.Date(day, origin = '1900-01-01')
    array <- ncvar_get(nc_data, "daily_mean_palmer_drought_severity_index")
    fillvalue <- ncatt_get(nc_data, "daily_mean_palmer_drought_severity_index", "_FillValue")
    nc_close(nc_data) 
    array[array == fillvalue$value] <- NA
  }
  slice <- array[, , (dates > paste0(year, "-04-01") & dates < paste0(year, "-10-01"))]
  mean <- apply(slice, c(1,2), mean)
  r <- raster(t(mean), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat), crs=CRS("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs+ towgs84=0,0,0"))
  points <- as.data.frame(rasterToPoints(r))
  colnames(points) <- c("x", "y", "pdsi")
  points <- merge(points, forest_points)
  points$county_forest_pdsi <- points$pdsi*points$county_forest_weights
  points$state_forest_pdsi <- points$pdsi*points$state_forest_weights
  points$west_forest_pdsi <- points$pdsi*points$west_forest_weights
  # County 
  county_forest_pdsi <- aggregate(points$county_forest_pdsi, by = list(points$county), FUN = "sum")
  colnames(county_forest_pdsi) <- c("county", "mean_pdsi")
  county_forest_pdsi$year <- year
  if(year==1981){county_pdsi <- county_forest_pdsi}else{county_pdsi <- rbind(county_pdsi, county_forest_pdsi)}
  # State 
  state_forest_pdsi <- aggregate(points$state_forest_pdsi, by = list(points$state), FUN = "sum")
  colnames(state_forest_pdsi) <- c("state", "mean_pdsi")
  state_forest_pdsi$year <- year 
  if(year==1981){state_pdsi <- state_forest_pdsi}else{state_pdsi <- rbind(state_pdsi, state_forest_pdsi)}
  # Western US 
  west_forest_pdsi <- sum(points$west_forest_pdsi)
  west_pdsi[which(west_pdsi$year==year),"mean_pdsi"] <- west_forest_pdsi
}

county_pdsi <- county_pdsi[,c("county", "year", "mean_pdsi")]
state_pdsi <- state_pdsi[,c("state", "year", "mean_pdsi")]

write.csv(county_pdsi, paste0(path, "climate/PDSI_county.csv"), row.names = F)
write.csv(state_pdsi, paste0(path, "climate/PDSI_state.csv"), row.names = F)
write.csv(west_pdsi, paste0(path, "climate/PDSI_west.csv"), row.names = F)


rm(list=ls())
library(ncdf4) 
library(raster) 
library(rgdal) 

path <- dirname(rstudioapi::getActiveDocumentContext()$path)

# ADMIN BOUNDARIES 
counties <- tigris::counties(cb=T)
counties <- subset(counties, !(STATEFP %in% c("02", "15", "60", "66", "69", "72", "78")))
counties <- as(counties, 'Spatial')

# PDSI 
# Source: http://thredds.northwestknowledge.net/thredds/ncss/grid/agg_met_pdsi_1979_CurrentYear_CONUS.nc/dataset.html

nc_data <- nc_open(paste0(path, "agg_met_pdsi_1981_CurrentYear_CONUS.nc"))
print(nc_data)

lon <- ncvar_get(nc_data, "lon")
lat <- ncvar_get(nc_data, "lat")
day <- ncvar_get(nc_data, "day")

dates <- as.Date(day, origin = '1900-01-01')

array <- ncvar_get(nc_data, "daily_mean_palmer_drought_severity_index")

fillvalue <- ncatt_get(nc_data, "daily_mean_palmer_drought_severity_index", "_FillValue")
fillvalue

nc_close(nc_data) 

array[array == fillvalue$value] <- NA
slice <- array[, , 1]
r <- raster(t(slice), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat), crs=CRS("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs+ towgs84=0,0,0"))

# Create forested area weights 
points <- as.data.frame(rasterToPoints(r))
sp <- SpatialPoints(points[,c("x", "y")])
proj4string(sp) <- proj4string(r)

counties <- spTransform(counties, proj4string(r))

over <- over(sp, counties)
points$state <- over$STATEFP
points$county <- over$GEOID
county_points <- subset(points, !is.na(county))

years <- c(1981:2020)
west_pdsi <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_pdsi) <- c("year", "mean_pdsi")
west_pdsi$year <- years

for(year in years){
  print(year)
  if(year %in% c(1981, 1986, 1991, 1996, 2001, 2006, 2011, 2016)){
    nc_data <- nc_open(paste0(path, "agg_met_pdsi_", year, "_CurrentYear_CONUS.nc"))
    lon <- ncvar_get(nc_data, "lon")
    lat <- ncvar_get(nc_data, "lat")
    day <- ncvar_get(nc_data, "day")
    dates <- as.Date(day, origin = '1900-01-01')
    array <- ncvar_get(nc_data, "daily_mean_palmer_drought_severity_index")
    fillvalue <- ncatt_get(nc_data, "daily_mean_palmer_drought_severity_index", "_FillValue")
    nc_close(nc_data) 
    array[array == fillvalue$value] <- NA
  }
  slice <- array[, , (dates > paste0(year, "-04-01") & dates < paste0(year, "-10-01"))]
  mean <- apply(slice, c(1,2), mean)
  r <- raster(t(mean), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat), crs=CRS("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs+ towgs84=0,0,0"))
  points <- as.data.frame(rasterToPoints(r))
  colnames(points) <- c("x", "y", "pdsi")
  points <- merge(points, county_points, by = c("x", "y"))
  # County 
  county_area_pdsi <- aggregate(points$pdsi, by = list(points$county), FUN = "mean")
  colnames(county_area_pdsi) <- c("county", "mean_pdsi")
  county_area_pdsi$year <- year
  if(year==1981){county_pdsi <- county_area_pdsi}else{county_pdsi <- rbind(county_pdsi, county_area_pdsi)}
  # State 
  state_area_pdsi <- aggregate(points$pdsi, by = list(points$state), FUN = "mean")
  colnames(state_area_pdsi) <- c("state", "mean_pdsi")
  state_area_pdsi$year <- year 
  if(year==1981){state_pdsi <- state_area_pdsi}else{state_pdsi <- rbind(state_pdsi, state_area_pdsi)}
  # Western US 
  west_area_pdsi <- mean(points$pdsi)
  west_pdsi[which(west_pdsi$year==year),"mean_pdsi"] <- west_area_pdsi
}

county_pdsi <- county_pdsi[,c("county", "year", "mean_pdsi")]
state_pdsi <- state_pdsi[,c("state", "year", "mean_pdsi")]

write.csv(county_pdsi, paste0(path, "climate/PDSI_county_allarea.csv"), row.names = F)
write.csv(state_pdsi, paste0(path, "climate/PDSI_state_allarea.csv"), row.names = F)
write.csv(west_pdsi, paste0(path, "climate/PDSI_us_allarea.csv"), row.names = F)
