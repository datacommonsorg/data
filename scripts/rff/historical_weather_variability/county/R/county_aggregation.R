### Aggregate PRISM to county ###
rm(list=setdiff(ls(), c("master_path", "code_path")))
path <- master_path

coords <- read.csv(paste0(path, "replication/data/monthly_dataframes/month_ppt_coordinates.csv"))

counties <- tigris::counties(cb = T)
counties <- as(counties, 'Spatial')

sp <- SpatialPoints(coords)
proj4string(sp) <- proj4string(counties)
  
counties <- crop(counties, extent(sp))
over <- over(sp, counties)

coords$fips <- over$GEOID

write.csv(coords, paste0(path, "replication/data/prism_coordinates_fips.csv"), row.names = F)


#### RANGES ####

# TMIN
load(paste0(path, "replication/data/ranges/tmin/tmin_ranges_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "InternannualRange_MonthlyMinTemperature")
data$Date <- substr(data$Date, 12,15)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- data

# tmax
load(paste0(path, "replication/data/ranges/tmax/tmax_ranges_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "InternannualRange_MonthlyMaxTemperature")
data$Date <- substr(data$Date, 12,15)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))

# precip 
load(paste0(path, "replication/data/ranges/ppt/precip_ranges_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "InternannualRange_MonthlyPrecipitation")
data$Date <- substr(data$Date, 14,17)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))

#### 1Y SPI ###
load(paste0(path, "replication/data/SPI/spi_annual_dataframe.Rdata"))
data <- cbind(coords, annual[,3:ncol(annual)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "StandardPrecipitationIndex")
data$Date <- substr(data$Date, 2,5)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))


#### 1Y HEATWAVES ###

# Count 
load(paste0(path, "replication/data/heatwaves/hw_count_dataframe.Rdata"))

data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Count")
data$Heatwave_Count <- round(data$Heatwave_Count)
data$Date <- substr(data$Date, 10,13)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))


# Length
load(paste0(path, "replication/data/heatwaves/hw_length_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Length")
data$Heatwave_Length <- round(data$Heatwave_Length)
data$Date <- substr(data$Date, 11,14)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))

# Intensity
load(paste0(path, "replication/data/heatwaves/hw_intensity_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Intensity")
data$Date <- substr(data$Date, 14,17)
data$TimeIntervalType <- "P1Y"
data <- data[,c(4,2,1,3)]

df <- merge(data, df, by=c("TimeIntervalType", "Date", "GeoId"))
any(is.na(df))

###############

# SPI Monthly
load( paste0(path, "replication/data/SPI/spi_monthly_dataframe.Rdata"))
colnames(monthly) <-c("x", "y", paste0("y", rep(1981:2021, each = 12), "m", str_pad(rep(1:12, 41), 2, pad = "0")))
data <- cbind(coords, monthly[,3:ncol(monthly)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "StandardPrecipitationIndex")
data$Date <- paste0(substr(data$Date, 2,5), "-", substr(data$Date, 7,8))
data$TimeIntervalType <- "P1M"

data$Heatwave_Intensity <- NA
data$Heatwave_Length <- NA
data$Heatwave_Count <- NA
data$InternannualRange_MonthlyPrecipitation <- NA
data$InternannualRange_MonthlyMaxTemperature <- NA
data$InternannualRange_MonthlyMinTemperature <- NA

data <- data[,c(4,2,1,5,6,7,3,8,9,10)]
any(is.na(data))

df <- rbind(df, data)



############### HW 5 years 

# Count
load(paste0(path, "replication/data/heatwaves/hw_count_5y_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Count")
data$Heatwave_Count <- round(data$Heatwave_Count)
data$Date <- substr(data$Date, 7,10)
data$TimeIntervalType <- "P5Y"

hw <- data

# Length
load(paste0(path, "replication/data/heatwaves/hw_length_5y_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Length")
data$Date <- substr(data$Date, 8,11)
data$TimeIntervalType <- "P5Y"

hw <- merge(hw, data, by = c("TimeIntervalType", "Date", "GeoId"))




# Intensity
load(paste0(path, "replication/data/heatwaves/hw_intensity_5y_dataframe.Rdata"))
data <- cbind(coords, data[,3:ncol(data)])

data <- aggregate(data[,4:ncol(data)], by = list(data$fips), FUN = mean, na.rm=T)
colnames(data)[1] <- "GeoId"

data$GeoId<- paste0("dcid:geoId/",str_pad(data$GeoId, 5, pad = "0"))
data <- melt(data, id.vars = "GeoId")
colnames(data) <- c("GeoId", "Date", "Heatwave_Intensity")
data$Date <- substr(data$Date, 11,14)
data$TimeIntervalType <- "P5Y"

hw <- merge(hw, data, by = c("TimeIntervalType", "Date", "GeoId"))
any(is.na(hw))

hw$StandardPrecipitationIndex <- NA
hw$InternannualRange_MonthlyPrecipitation <- NA
hw$InternannualRange_MonthlyMaxTemperature <- NA
hw$InternannualRange_MonthlyMinTemperature <- NA

hw <- hw[,colnames(df)]

df <- rbind(df, hw)

write.csv(df, file = paste0(path, "replication/WeatherVariability_County_2.csv"),
          row.names = F)













