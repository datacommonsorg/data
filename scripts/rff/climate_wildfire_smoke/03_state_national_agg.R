# NATIONAL and STATE aggregates

rm(list=ls())
path <- dirname(rstudioapi::getActiveDocumentContext()$path)

library(stringr)

# SMOKE DATA 
smoke <- read.csv(paste0(path, "smokePM25_annual_county_stats.csv"))
smoke$GEOID <- str_pad(smoke$GEOID, 5, pad = "0")

pop <- read.csv(paste0(path, "co-est2021-alldata.csv"))
pop$COUNTYFP <- str_pad(pop$COUNTY, 3, pad = "0")
pop$STATEFP <- str_pad(pop$STATE, 2, pad = "0")
pop$GEOID <- paste0(pop$STATEFP, pop$COUNTYFP)
pop <- subset(pop, !(STATEFP %in% c("02", "15")))
pop <- subset(pop, !(COUNTY==0))

smoke <- merge(smoke, pop[,c("GEOID", "STATEFP", "POPESTIMATE2020")])

state_totals <- aggregate(pop$POPESTIMATE2020, by=list(pop$STATEFP), FUN = "sum")
colnames(state_totals) <- c("STATEFP", "state_pop")

national_total <- sum(pop$POPESTIMATE2020)

smoke <- merge(smoke, state_totals, by = "STATEFP")
smoke$national_pop <- national_total

smoke$ann_mean_smokePM_popw <- smoke$ann_mean_smokePM*(smoke$POPESTIMATE2020/smoke$state_pop)
smoke$ann_max_smokePM_popw <- smoke$ann_max_smokePM*(smoke$POPESTIMATE2020/smoke$state_pop)

state_smoke <- aggregate(smoke[,c("ann_mean_smokePM_popw", "ann_max_smokePM_popw")], by = list(smoke$STATEFP, smoke$year), FUN = "sum")
colnames(state_smoke)[1:2] <- c("STATEFP", "YEAR")
write.csv(state_smoke, file = paste0(path, "state_smokePM.csv"))

smoke$ann_mean_smokePM_popw <- smoke$ann_mean_smokePM*(smoke$POPESTIMATE2020/smoke$national_pop)
smoke$ann_max_smokePM_popw <- smoke$ann_max_smokePM*(smoke$POPESTIMATE2020/smoke$national_pop)

national_smoke <- aggregate(smoke[,c("ann_mean_smokePM_popw", "ann_max_smokePM_popw")], by = list(smoke$year), FUN = "sum")
colnames(national_smoke)[1] <- c("YEAR")
write.csv(national_smoke, file = paste0(path, "national_smokePM.csv"))


# HEATWAVE DATA 
data <- read.csv(paste0(path, "WeatherVariability_Counties.csv"))
data$GEOID <- substr(data$GeoId, 12, 16)
data <- subset(data, TimeIntervalType=="P1Y")
data <- data[,c("Date", "GEOID", "Heatwave_Intensity", "Heatwave_Length", "Heatwave_Count")]
colnames(data)[1] <- "year"

data <- merge(data, pop[,c("GEOID", "STATEFP", "POPESTIMATE2020")])
data <- merge(data, state_totals, by = "STATEFP")
data$national_pop <- national_total

data$Heatwave_Intensity_popw <- data$Heatwave_Intensity*(data$POPESTIMATE2020/data$state_pop)
data$Heatwave_Length_popw <- data$Heatwave_Length*(data$POPESTIMATE2020/data$state_pop)
data$Heatwave_Count_popw <- data$Heatwave_Count*(data$POPESTIMATE2020/data$state_pop)

state_data <- aggregate(data[,c("Heatwave_Intensity_popw", "Heatwave_Length_popw", "Heatwave_Count_popw")], 
                        by = list(data$STATEFP, data$year), FUN = "sum", na.rm = T)
colnames(state_data)[1:2] <- c("STATEFP", "YEAR")
write.csv(state_data, file = paste0(path, "state_heatwave.csv"))

data$Heatwave_Intensity_popw <- data$Heatwave_Intensity*(data$POPESTIMATE2020/data$national_pop)
data$Heatwave_Length_popw <- data$Heatwave_Length*(data$POPESTIMATE2020/data$national_pop)
data$Heatwave_Count_popw <- data$Heatwave_Count*(data$POPESTIMATE2020/data$national_pop)

national_data <- aggregate(data[,c("Heatwave_Intensity_popw", "Heatwave_Length_popw", "Heatwave_Count_popw")], 
                           by = list(data$year), FUN = "sum", na.rm = T)
colnames(national_data)[1] <- c("YEAR")
write.csv(national_data, file = paste0(path,"national_heatwave.csv"))


