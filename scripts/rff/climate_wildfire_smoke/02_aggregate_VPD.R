library(raster)
library(stringr)
library(tigris)

path <- dirname(rstudioapi::getActiveDocumentContext()$path)
  
# FOREST MASK 
# Source: Parks & Abatzoglou (2020) https://datadryad.org/stash/dataset/doi:10.5061/dryad.tmpg4f4x1
# aggregate_PDSI.R generates this aggregated raster from original forest maks 
forest <- raster(paste0(path, "forest_raster.tif"))

# PRISM RASTER 
# Source: PRISM Monthly Maximum VPD https://prism.oregonstate.edu/recent/
vpd <- raster(paste0(path, "PRISM_vpdmax_stable_4kmM3_198101_202205_bil/PRISM_vpdmax_stable_4kmM3_198101_bil.bil"))

# ADMIN BOUNDARIES 
counties <- tigris::counties(cb=T)
western_states <- c("53", "41", "06", "16", "32", "30", "56", "49", "04", "08", "35")
counties <- subset(counties, STATEFP %in% western_states)
counties <- as(counties, 'Spatial')

# Create forested area weights 
mask <- projectRaster(forest, vpd)
forest_points <- as.data.frame(rasterToPoints(mask))
colnames(forest_points)[3] <- "forest_cover"
sp <- SpatialPoints(forest_points[,c("x", "y")])
proj4string(sp) <- proj4string(vpd)
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

write.csv(forest_points, paste0(path, "forest_weights_PRISM.csv"), row.names = F)

years <- c(1981:2020)
months <- str_pad(c(4:9), 2, pad = "0")

# VPD 
west_vpd <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_vpd) <- c("year", "mean_max_vpd")
west_vpd$year <- 1981:2020

for(year in years){
  print(year)
  for (month in months){
    vpd <- raster(paste0(path, "PRISM_vpdmax_stable_4kmM3_198101_202205_bil/PRISM_vpdmax_stable_4kmM3_", year, month, "_bil.bil"))
    if(month == months[1]){data <- vpd}else{data <- stack(data, vpd)}
  }
  mean_vpd <- mean(data)
  points <- as.data.frame(rasterToPoints(mean_vpd))
  colnames(points) <- c("x", "y", "max_vpd")
  points <- merge(points, forest_points)
  points$county_forest_vpd <- points$max_vpd*points$county_forest_weights
  points$state_forest_vpd <- points$max_vpd*points$state_forest_weights
  points$west_forest_vpd <- points$max_vpd*points$west_forest_weights
  # County 
  county_forest_vpd <- aggregate(points$county_forest_vpd, by = list(points$county), FUN = "sum")
  colnames(county_forest_vpd) <- c("county", "mean_max_vpd")
  county_forest_vpd$year <- year
  if(year==years[1]){county_vpd <- county_forest_vpd}else{county_vpd <- rbind(county_vpd, county_forest_vpd)}
  # State 
  state_forest_vpd <- aggregate(points$state_forest_vpd, by = list(points$state), FUN = "sum")
  colnames(state_forest_vpd) <- c("state", "mean_max_vpd")
  state_forest_vpd$year <- year 
  if(year==years[1]){state_vpd <- state_forest_vpd}else{state_vpd <- rbind(state_vpd, state_forest_vpd)}
  # Western US 
  west_forest_vpd <- sum(points$west_forest_vpd)
  west_vpd[which(west_vpd$year==year),"mean_max_vpd"] <- west_forest_vpd
}

county_vpd <- county_vpd[,c("county", "year", "max_vpd")]
state_vpd <- state_vpd[,c("state", "year", "max_vpd")]

write.csv(county_vpd, paste0(path, "climate/VPD_county.csv"), row.names = F)
write.csv(state_vpd, paste0(path, "climate/VPD_state.csv"), row.names = F)
write.csv(west_vpd, paste0(path, "climate/VPD_west.csv"), row.names = F)


# TMAX 
west_tmax <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_tmax) <- c("year", "mean_tmax")
west_tmax$year <- 1981:2020

for(year in years){
  print(year)
  for (month in months){
    tmax <- raster(paste0(path, "PRISM_tmax_stable_4kmM3_198101_202205_bil/PRISM_tmax_stable_4kmM3_", year, month, "_bil.bil"))
    if(month == months[1]){data <- tmax}else{data <- stack(data, tmax)}
  }
  mean_tmax <- mean(data)
  points <- as.data.frame(rasterToPoints(mean_tmax))
  colnames(points) <- c("x", "y", "tmax")
  points <- merge(points, forest_points)
  points$county_forest_tmax <- points$tmax*points$county_forest_weights
  points$state_forest_tmax <- points$tmax*points$state_forest_weights
  points$west_forest_tmax <- points$tmax*points$west_forest_weights
  # County 
  county_forest_tmax <- aggregate(points$county_forest_tmax, by = list(points$county), FUN = "sum")
  colnames(county_forest_tmax) <- c("county", "mean_tmax")
  county_forest_tmax$year <- year
  if(year==years[1]){county_tmax <- county_forest_tmax}else{county_tmax <- rbind(county_tmax, county_forest_tmax)}
  # State 
  state_forest_tmax <- aggregate(points$state_forest_tmax, by = list(points$state), FUN = "sum")
  colnames(state_forest_tmax) <- c("state", "mean_tmax")
  state_forest_tmax$year <- year 
  if(year==years[1]){state_tmax <- state_forest_tmax}else{state_tmax <- rbind(state_tmax, state_forest_tmax)}
  # Western US 
  west_forest_tmax <- sum(points$west_forest_tmax)
  west_tmax[which(west_tmax$year==year),"mean_tmax"] <- west_forest_tmax
}

county_tmax <- county_tmax[,c("county", "year", "mean_tmax")]
state_tmax <- state_tmax[,c("state", "year", "mean_tmax")]

write.csv(county_tmax, paste0(path, "climate/tmax_county.csv"), row.names = F)
write.csv(state_tmax, paste0(path, "climate/tmax_state.csv"), row.names = F)
write.csv(west_tmax, paste0(path, "climate/tmax_west.csv"), row.names = F)



rm(list=ls())
library(raster)
library(stringr)
library(tigris)

path <- dirname(rstudioapi::getActiveDocumentContext()$path)

# PRISM RASTER 
# Source: PRISM Monthly Maximum VPD https://prism.oregonstate.edu/recent/
vpd <- raster(paste0(path, "PRISM_vpdmax_stable_4kmM3_198101_202207_bil/PRISM_vpdmax_stable_4kmM3_198101_bil.bil"))


# ADMIN BOUNDARIES 
counties <- tigris::counties(cb=T)
counties <- subset(counties, !(STATEFP %in% c("02", "15", "60", "66", "69", "72", "78")))
counties <- as(counties, 'Spatial')

# Create forested area weights 
points <- as.data.frame(rasterToPoints(vpd))
sp <- SpatialPoints(points[,c("x", "y")])
proj4string(sp) <- proj4string(vpd)
over <- over(sp, counties)
points$state <- over$STATEFP
points$county <- over$GEOID
county_points <- subset(points, !is.na(county))

years <- c(1981:2020)
months <- str_pad(c(4:9), 2, pad = "0")

# VPD 
west_vpd <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_vpd) <- c("year", "mean_max_vpd")
west_vpd$year <- 1981:2020

for(year in years){
  print(year)
  for (month in months){
    vpd <- raster(paste0(path, "PRISM_vpdmax_stable_4kmM3_198101_202207_bil/PRISM_vpdmax_stable_4kmM3_", year, month, "_bil.bil"))
    if(month == months[1]){data <- vpd}else{data <- stack(data, vpd)}
  }
  mean_vpd <- mean(data)
  points <- as.data.frame(rasterToPoints(mean_vpd))
  colnames(points) <- c("x", "y", "max_vpd")
  points <- merge(points, county_points)
  # County 
  county_area_vpd <- aggregate(points$max_vpd, by = list(points$county), FUN = "mean")
  colnames(county_area_vpd) <- c("county", "mean_max_vpd")
  county_area_vpd$year <- year
  if(year==years[1]){county_vpd <- county_area_vpd}else{county_vpd <- rbind(county_vpd, county_area_vpd)}
  # State 
  state_area_vpd <- aggregate(points$max_vpd, by = list(points$state), FUN = "mean")
  colnames(state_area_vpd) <- c("state", "mean_max_vpd")
  state_area_vpd$year <- year 
  if(year==years[1]){state_vpd <- state_area_vpd}else{state_vpd <- rbind(state_vpd, state_area_vpd)}
  # Western US 
  west_area_vpd <- mean(points$max_vpd)
  west_vpd[which(west_vpd$year==year),"mean_max_vpd"] <- west_area_vpd
}

county_vpd <- county_vpd[,c("county", "year", "max_vpd")]
state_vpd <- state_vpd[,c("state", "year", "max_vpd")]

write.csv(county_vpd, paste0(path, "climate/VPD_county_allarea.csv"), row.names = F)
write.csv(state_vpd, paste0(path, "climate/VPD_state_allarea.csv"), row.names = F)
write.csv(west_vpd, paste0(path, "climate/VPD_us_allarea.csv"), row.names = F)


# TMAX 
west_tmax <- as.data.frame(matrix(NA, length(years), 2))
colnames(west_tmax) <- c("year", "mean_tmax")
west_tmax$year <- 1981:2020

for(year in years){
  print(year)
  for (month in months){
    tmax <- raster(paste0(path, "PRISM_tmax_stable_4kmM3_198101_202207_bil/PRISM_tmax_stable_4kmM3_", year, month, "_bil.bil"))
    if(month == months[1]){data <- tmax}else{data <- stack(data, tmax)}
  }
  mean_tmax <- mean(data)
  points <- as.data.frame(rasterToPoints(mean_tmax))
  colnames(points) <- c("x", "y", "tmax")
  points <- merge(points, county_points)
  # County 
  county_area_tmax <- aggregate(points$tmax, by = list(points$county), FUN = "mean")
  colnames(county_area_tmax) <- c("county", "mean_tmax")
  county_area_tmax$year <- year
  if(year==years[1]){county_tmax <- county_area_tmax}else{county_tmax <- rbind(county_tmax, county_area_tmax)}
  # State 
  state_area_tmax <- aggregate(points$tmax, by = list(points$state), FUN = "mean")
  colnames(state_area_tmax) <- c("state", "mean_tmax")
  state_area_tmax$year <- year 
  if(year==years[1]){state_tmax <- state_area_tmax}else{state_tmax <- rbind(state_tmax, state_area_tmax)}
  # Western US 
  west_area_tmax <- mean(points$tmax)
  west_tmax[which(west_tmax$year==year),"mean_tmax"] <- west_area_tmax
}

county_tmax <- county_tmax[,c("county", "year", "mean_tmax")]
state_tmax <- state_tmax[,c("state", "year", "mean_tmax")]

write.csv(county_tmax, paste0(path, "climate/tmax_county_allarea.csv"), row.names = F)
write.csv(state_tmax, paste0(path, "climate/tmax_state_allarea.csv"), row.names = F)
write.csv(west_tmax, paste0(path, "climate/tmax_us_allarea.csv"), row.names = F)

