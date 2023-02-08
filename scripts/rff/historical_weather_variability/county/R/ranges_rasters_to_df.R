rm(list=setdiff(ls(), c("master_path", "code_path")))


dir <- master_path

# Precip 
path <- paste0(dir, "replication/data/ranges/ppt/")

files <- list.files(path)
files <- files[nchar(files)==22]

for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  df <- as.data.frame(rasterToPoints(r))
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("precip_range_", 1981:2021))
save(data, file =paste0(path, "precip_ranges_dataframe.Rdata"))

# TMIN
path <- paste0(dir, "replication/data/ranges/tmin/")

files <- list.files(path)
files <- files[nchar(files)==20]

for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  df <- as.data.frame(rasterToPoints(r))
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("tmin_range_", 1981:2021))
save(data, file =paste0(path, "tmin_ranges_dataframe.Rdata"))

# TMAX
path <- paste0(dir, "replication/data/ranges/tmax/")

files <- list.files(path)
files <- files[nchar(files)==20]

for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  df <- as.data.frame(rasterToPoints(r))
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("tmax_range_", 1981:2021))
save(data, file =paste0(path,"tmax_ranges_dataframe.Rdata"))
