rm(list=setdiff(ls(), c("master_path", "code_path")))

path <- master_path
setwd(path)

temp_dir <- paste0(path, "replication/data/temp")
tmin_path <- paste0(path, "raw_data/prism/daily/4km/src/tmin/")
folders <- list.files(tmin_path)

# Make 85th percentile raster 
years <- c(1981:2000)
months <- c("07", "08")

setwd(temp_dir)

rm(r,s,y85, p85, s85)
# Make full stack 
for (y in years){
  print(y)
  rm(s)
  for (m in months){
    daily_folders <- folders[substr(folders, 1, 6)==paste0(y, m)]
    for(f in daily_folders){
      unzip(paste0(tmin_path, f))
      r <- raster(paste0("PRISM_tmin_stable_4kmD2_", substr(f, 1, 8), "_bil.bil"))
      if("s" %in% ls()){s <- stack(s, r)}else{s <- r}
    }
  }
  y85 <- calc(s, fun = function(x) quantile(x, 0.85, na.rm = T))
  unlink(paste0(temp_dir, "/*"))
  if("s85" %in% ls()){s85 <- stack(s85, y85)}else{s85 <- y85}
}
p85 <- calc(s85, fun = mean)
writeRaster(p85, paste0(tmin_path, "summer_85p"), format = "GTiff", overwrite = T)

p85 <- raster(paste0(tmin_path, "summer_85p.tif"))

years <- c(1981:2020)
months <- c("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12")
rm(se, st)
for (y in years){
  print(y)
  rm(se, st)
  print("Loading raw data")
  for (m in months){
    daily_folders <- folders[substr(folders, 1, 6)==paste0(y, m)]
    for(f in daily_folders){
      unzip(paste0(tmin_path, f))
      r <- raster(paste0("PRISM_tmin_stable_4kmD2_", substr(f, 1, 8), "_bil.bil"))
      e <- r > p85
      if("st" %in% ls()){st <- stack(st, r)}else{st <- r}
      if("se" %in% ls()){se <- stack(se, e)}else{se <- e}
    }
  }
  # Identify days with heatwave 
  print("Calculating heat wave days")
  rm(hw_days, hw_counts)
  for(d in 2:(dim(se)[3]-1)){
    pair_1 <- se[[(d-1):d]]
    pair_2 <- se[[d:(d+1)]]
    rep_1 <- calc(pair_1, fun=sum)
    rep_2 <- calc(pair_2, fun=sum)
    hw_day <- (rep_1==2 | rep_2==2)
    if(d==2){first <- rep_1==2}
    if(d==(dim(se)[3]-1)){last <- rep_2==2}
    if("hw_days" %in% ls()){hw_days <- stack(hw_days, hw_day)}else{hw_days <- hw_day}
  }
  hw_days <- stack(first, hw_days, last)
  
  # Calculate number of heatwaves
  print("Calculating count and length")
  for(d in 2:(dim(hw_days)[3])){
    rep <- overlay(hw_days[[d]], hw_days[[d-1]], fun=function(r1,r2){return(r1 - r2)})
    hw_count <- rep==1
    if("hw_counts" %in% ls()){hw_counts <- stack(hw_counts, hw_count)}else{hw_counts <- hw_count}
  }
  heatwave_counts <- calc(hw_counts, fun=sum)
  
  # Calculate length of heatwaves 
  total_hw_days <- calc(hw_days, fun = sum)
  heatwave_lengths <- overlay(total_hw_days, heatwave_counts, fun=function(r1,r2){return(r1/r2)})
  
  # Calculate average 
  print("Calculating intensity")
  hw_temps <- st
  hw_temps[hw_days==0] <- NA
  heatwave_intensity <- calc(hw_temps, fun = mean, na.rm = T)
  heatwave_intensity <- heatwave_intensity - p85
  
  plot(heatwave_counts, main = paste("Counts", y))
  plot(heatwave_lengths, main = paste("Lengths", y))
  plot(heatwave_intensity, main = paste("Intensity", y))
  
  writeRaster(heatwave_counts, paste0(path, "replication/data/heatwaves/4km/annual/hw_count_", y), format = "GTiff", overwrite = T)
  writeRaster(heatwave_lengths, paste0(path, "replication/data/heatwaves/4km/annual/hw_length_", y), format = "GTiff", overwrite = T)
  writeRaster(heatwave_intensity, paste0(path, "replication/data/heatwaves/4km/annual/hw_intensity_", y), format = "GTiff", overwrite = T)
  
  unlink(paste0(temp_dir, "/*"))
  unlink(tempdir(), recursive = T)
}