rm(list=setdiff(ls(), c("master_path", "code_path")))

dir <- master_path
out_dir <- paste0(dir, "replication/data/monthly_dataframes/")
setwd(dir)

#TMIN 
unzip(paste0(dir, "raw_data/prism/monthly/PRISM_tmin_stable_4kmM3_198101_202202_bil.zip"),
             exdir = paste0(dir, "raw_data/prism/monthly/PRISM_tmin_stable_4kmM3_198101_202202_bil"))
path <- paste0(dir, "raw_data/prism/monthly/PRISM_tmin_stable_4kmM3_198101_202202_bil/")

files <- list.files(path)
files <- files[((substr(files, 1, 5)=="PRISM") & substr(files, nchar(files)-3, nchar(files))==".bil")]

for(f in 1:length(files)){
  print(f)
  print(substr(files[f], 25, 30))
  slice <- raster(paste0(path, files[f]))
  points <- as.data.frame(rasterToPoints(slice))
  ppt <- points[,3]
  ppt <- as.integer(ppt*1000)
  if(f==1){
    coords <- points[,c("x","y")]
    data <- as.data.frame(ppt)
  }else{
    data <- cbind(data, ppt)
  }
  colnames(data)[f] <- paste0("t", substr(files[f], 25, 30))
  rm(slice, points, ppt)
}

data <- t(data)
save(data, file = paste0(out_dir, "monthly_tmin.Rdata"))
write.csv(coords, file = paste0(out_dir, "month_tmin_coordinates.csv"), row.names = F)


#TMAX
unzip(paste0(dir, "raw_data/prism/monthly/PRISM_tmax_stable_4kmM3_198101_202202_bil.zip"),
      exdir = paste0(dir, "raw_data/prism/monthly/PRISM_tmax_stable_4kmM3_198101_202202_bil"))
path <- paste0(dir, "raw_data/prism/monthly/PRISM_tmax_stable_4kmM3_198101_202202_bil/")

files <- list.files(path)
files <- files[((substr(files, 1, 5)=="PRISM") & substr(files, nchar(files)-3, nchar(files))==".bil")]

for(f in 1:length(files)){
  print(f)
  print(substr(files[f], 25, 30))
  slice <- raster(paste0(path, files[f]))
  points <- as.data.frame(rasterToPoints(slice))
  ppt <- points[,3]
  ppt <- as.integer(ppt*1000)
  if(f==1){
    coords <- points[,c("x","y")]
    data <- as.data.frame(ppt)
  }else{
    data <- cbind(data, ppt)
  }
  colnames(data)[f] <- paste0("t", substr(files[f], 25, 30))
  rm(slice, points, ppt)
}

data <- t(data)
save(data, file = paste0(out_dir, "monthly_tmax.Rdata"))
write.csv(coords, file = paste0(out_dir, "month_tmax_coordinates.csv"), row.names = F)



#PPT
unzip(paste0(dir, "raw_data/prism/monthly/PRISM_ppt_stable_4kmM3_198101_202202_bil.zip"),
      exdir = paste0(dir, "raw_data/prism/monthly/PRISM_ppt_stable_4kmM3_198101_202202_bil"))
path <- paste0(dir, "raw_data/prism/monthly/PRISM_ppt_stable_4kmM3_198101_202202_bil/")

files <- list.files(path)
files <- files[((substr(files, 1, 5)=="PRISM") & substr(files, nchar(files)-3, nchar(files))==".bil")]

for(f in 1:length(files)){
  print(f)
  print(substr(files[f], 24, 29))
  slice <- raster(paste0(path, files[f]))
  points <- as.data.frame(rasterToPoints(slice))
  ppt <- points[,3]
  ppt <- as.integer(ppt*1000)
  if(f==1){
    coords <- points[,c("x","y")]
    data <- as.data.frame(ppt)
  }else{
    data <- cbind(data, ppt)
  }
  colnames(data)[f] <- paste0("t", substr(files[f], 24, 29))
  rm(slice, points, ppt)
}

data <- t(data)
save(data, file = paste0(out_dir, "monthly_ppt.Rdata"))
write.csv(coords, file = paste0(out_dir, "month_ppt_coordinates.csv"), row.names = F)

