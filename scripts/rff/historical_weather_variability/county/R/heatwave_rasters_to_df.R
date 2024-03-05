rm(list=setdiff(ls(), c("master_path", "code_path")))

dir <- master_path
setwd(dir)

# HW COUNT
path <- paste0(dir, "replication/data/heatwaves/4km/annual")

files <- list.files(path)
files <- files[substr(files, 1,8)=="hw_count"]
files <- files[nchar(files)==17]

for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  df <- as.data.frame(rasterToPoints(r))
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("hw_count_", 1981:2020))
save(data, file =paste0(dir, "replication/data/heatwaves/hw_count_dataframe.Rdata"))


# HW LENGTH
path <- paste0(dir, "replication/data/heatwaves/4km/annual")

files <- list.files(path)
files <- files[substr(files, 1,9)=="hw_length"]
files <- files[nchar(files)==18]

ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))


for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  r[(is.na(r) & !is.na(ref))] <- -999
  df <- as.data.frame(rasterToPoints(r))
  df[df[,3]==-999, 3] <- NA
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("hw_length_", 1981:2020))
save(data, file =paste0(dir, "replication/data/heatwaves/hw_length_dataframe.Rdata"))


# HW INTENSITY
path <- paste0(dir, "replication/data/heatwaves/4km/annual")

files <- list.files(path)
files <- files[substr(files, 1,6)=="hw_int"]
files <- files[nchar(files)==21]

for(file in files){
  print(file)
  r <- raster(paste0(path, "/", file))
  r[(is.na(r) & !is.na(ref))] <- -999
  df <- as.data.frame(rasterToPoints(r))
  df[df[,3]==-999, 3] <- NA
  if(file==files[1]){data <- df}else{data <- cbind(data, df[,3])}
}

colnames(data) <-  c("x", "y", paste0("hw_intensity_", 1981:2020))
save(data, file =paste0(dir, "replication/data/heatwaves/hw_intensity_dataframe.Rdata"))

