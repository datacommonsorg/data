
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# For data upload 
data <- read.csv(paste0(path, "smokePM25_annual_county_stats.csv"))
data$daysAbove12 <- data$days12 + data$days35 + data$days55 +data$days150 + data$days250
data$daysAbove35 <- data$days35 + data$days55 +data$days150 + data$days250
data$daysAbove55 <- data$days55 +data$days150 + data$days250
data$daysAbove150 <- data$days150 + data$days250
data$daysAbove250 <- data$days250

data <- data[,c("GEOID", "year", "ann_mean_smokePM", "ann_max_smokePM", 
                "daysAbove12", "daysAbove35", "daysAbove55",
                "daysAbove150", "daysAbove250")]
write.csv(data, paste0(path, "smokePM25_annual_county_stats_revised.csv"), row.names = F)
