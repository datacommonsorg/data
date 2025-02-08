rm(list=setdiff(ls(), c("master_path", "code_path")))


# TMAX 
path <- master_path

load(paste0(path, "replication/data/monthly_dataframes/monthly_tmax.Rdata"))

data <- data[-which(substr(rownames(data),2,5)=="2022"),]

ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))

coords <- read.csv(paste0(path, "replication/data/monthly_dataframes/month_tmax_coordinates.csv"))

#monthly <- cbind(coords, monthly)


years <- c(1981:2021)

for(y in years){
  print(y)
  df <- data[substr(rownames(data), 2,5)==y,]
  df <- df/1000
  df <- as.data.frame(t(df))
  df$min <- apply(df, 1, FUN = min)
  df$max <- apply(df, 1, FUN = max)
  df$range <- df$max - df$min
  df <- cbind(coords, df$range)
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  plot(r, main = y)
  writeRaster(r, paste0(path, "replication/data/ranges/tmax/tmax_ranges_", y), 
              format = "GTiff", overwrite = T)
}

# TMIN 
rm(list=setdiff(ls(), c("master_path", "code_path")))

path <- master_path


load(paste0(path, "replication/data/monthly_dataframes/monthly_tmin.Rdata"))

data <- data[-which(substr(rownames(data),2,5)=="2022"),]

ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))


coords <- read.csv(paste0(path, "replication/data/monthly_dataframes/month_tmin_coordinates.csv"))

#monthly <- cbind(coords, monthly)


years <- c(1981:2021)

for(y in years){
  print(y)
  df <- data[substr(rownames(data), 2,5)==y,]
  df <- df/1000
  df <- as.data.frame(t(df))
  df$min <- apply(df, 1, FUN = min)
  df$max <- apply(df, 1, FUN = max)
  df$range <- df$max - df$min
  df <- cbind(coords, df$range)
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  plot(r, main = y)
  writeRaster(r, paste0(path, "replication/data/ranges/tmin/tmin_ranges_", y), 
              format = "GTiff", overwrite = T)
}


# PPT 
rm(list=setdiff(ls(), c("master_path", "code_path")))

path <- master_path


load(paste0(path, "replication/data/monthly_dataframes/monthly_ppt.Rdata"))

data <- data[-which(substr(rownames(data),2,5)=="2022"),]

ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))


coords <- read.csv(paste0(path, "replication/data/monthly_dataframes/month_ppt_coordinates.csv"))

#monthly <- cbind(coords, monthly)


years <- c(1981:2021)

for(y in years){
  print(y)
  df <- data[substr(rownames(data), 2,5)==y,]
  df <- df/1000
  df <- as.data.frame(t(df))
  df$min <- apply(df, 1, FUN = min)
  df$max <- apply(df, 1, FUN = max)
  df$range <- df$max - df$min
  df <- cbind(coords, df$range)
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  plot(r, main = y)
  writeRaster(r, paste0(path, "replication/data/ranges/ppt/ppt_ranges_", y), 
              format = "GTiff", overwrite = T)
}


  
  