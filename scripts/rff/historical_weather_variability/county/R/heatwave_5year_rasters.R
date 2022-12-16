rm(list=setdiff(ls(), c("master_path", "code_path")))


path <- master_path 
setwd(path)

# count 
load(paste0(path, "replication/data/heatwaves/hw_count_dataframe.Rdata"))
ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))

data$count_1981_1985 = data$hw_count_1981 + data$hw_count_1982 + 
  data$hw_count_1983 + data$hw_count_1984 + data$hw_count_1985

data$count_1986_1990 = data$hw_count_1986 + data$hw_count_1987 + 
  data$hw_count_1988 + data$hw_count_1989 + data$hw_count_1990

data$count_1991_1995 = data$hw_count_1991 + data$hw_count_1992 + 
  data$hw_count_1993 + data$hw_count_1994 + data$hw_count_1995

data$count_1996_2000 = data$hw_count_1996 + data$hw_count_1997 + 
  data$hw_count_1998 + data$hw_count_1999 + data$hw_count_2000

data$count_2001_2005 = data$hw_count_2001 + data$hw_count_2002 + 
  data$hw_count_2003 + data$hw_count_2004 + data$hw_count_2005

data$count_2006_2010 = data$hw_count_2006 + data$hw_count_2007 + 
  data$hw_count_2008 + data$hw_count_2009 + data$hw_count_2010

data$count_2011_2015 = data$hw_count_2011 + data$hw_count_2012 + 
  data$hw_count_2013 + data$hw_count_2014 + data$hw_count_2015

data$count_2016_2020 = data$hw_count_2016 + data$hw_count_2017 + 
  data$hw_count_2018 + data$hw_count_2019 + data$hw_count_2020

data <- data[,c(1,2,43:50)]
save(data, file=paste0(path, "replication/data/heatwaves/hw_count_5y_dataframe.Rdata"))

for(t in 3:10){
  print(t)
  df <- data[,c(1,2,t)]
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  plot(r, main = colnames(df)[3])
  writeRaster(r, paste0(path, "replication/data/heatwaves/4km/year5/hw_",
                        colnames(df)[3]), format = "GTiff", overwrite = T)
}

# length
rm(list=setdiff(ls(), c("master_path", "code_path")))
path <- master_path 

load(paste0(path, "replication/data/heatwaves/hw_length_dataframe.Rdata"))
ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))

data$length_1981_1985 = apply(data[,3:7], 1, FUN = mean, na.rm=T)

data$length_1986_1990 = apply(data[,8:12], 1, FUN = mean, na.rm=T)

data$length_1991_1995 = apply(data[,13:17], 1, FUN = mean, na.rm=T)

data$length_1996_2000 = apply(data[,18:22], 1, FUN = mean, na.rm=T)

data$length_2001_2005 = apply(data[,23:27], 1, FUN = mean, na.rm=T)

data$length_2006_2010 = apply(data[,28:32], 1, FUN = mean, na.rm=T)

data$length_2011_2015 = apply(data[,33:37], 1, FUN = mean, na.rm=T)

data$length_2016_2020 = apply(data[,38:42], 1, FUN = mean, na.rm=T)

data <- data[,c(1,2,43:50)]
save(data, file=paste0(path, "replication/data/heatwaves/hw_length_5y_dataframe.Rdata"))

for(t in 3:10){
  print(t)
  df <- data[,c(1,2,t)]
  df[is.na(df[,3]),3] <- -999
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  r <- reclassify(r, c(-1000,-998, NA))
  plot(r, main = colnames(df)[3])
  writeRaster(r, paste0(path, "replication/data/heatwaves/4km/year5/hw_",
                        colnames(df)[3]), format = "GTiff", overwrite = T)
}

# intensity
rm(list=setdiff(ls(), c("master_path", "code_path")))
path <- master_path 

load(paste0(path, "replication/data/heatwaves/hw_intesnity_dataframe.Rdata"))
ref <- raster(paste0(path, "replication/data/heatwaves/4km/annual/hw_count_1981.tif"))

data$intensity_1981_1985 = apply(data[,3:7], 1, FUN = mean, na.rm=T)

data$intensity_1986_1990 = apply(data[,8:12], 1, FUN = mean, na.rm=T)

data$intensity_1991_1995 = apply(data[,13:17], 1, FUN = mean, na.rm=T)

data$intensity_1996_2000 = apply(data[,18:22], 1, FUN = mean, na.rm=T)

data$intensity_2001_2005 = apply(data[,23:27], 1, FUN = mean, na.rm=T)

data$intensity_2006_2010 = apply(data[,28:32], 1, FUN = mean, na.rm=T)

data$intensity_2011_2015 = apply(data[,33:37], 1, FUN = mean, na.rm=T)

data$intensity_2016_2020 = apply(data[,38:42], 1, FUN = mean, na.rm=T)

data <- data[,c(1,2,43:50)]
save(data, file=paste0(path, "replication/data/heatwaves/hw_intensity_5y_dataframe.Rdata"))

for(t in 3:10){
  print(t)
  df <- data[,c(1,2,t)]
  df[is.na(df[,3]),3] <- -999
  r <- rasterize(df[,c("x", "y")], ref, df[,3])
  r <- reclassify(r, c(-1000,-998, NA))
  plot(r, main = colnames(df)[3])
  writeRaster(r, paste0(path, "replication/data/heatwaves/4km/year5/hw_",
                        colnames(df)[3]), format = "GTiff", overwrite = T)
}
