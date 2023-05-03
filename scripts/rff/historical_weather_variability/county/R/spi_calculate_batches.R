rm(list=setdiff(ls(), c("master_path", "code_path")))




# TMAX 
path <- master_path

load(paste0(path, "replication/data/monthly_dataframes/monthly_ppt.Rdata"))

data <- data[-which(substr(rownames(data),2,5)=="2022"),]
data <- ts(data, end=c(2021,12), frequency=12)

df <- data[,1:500]

low <- seq(1,481631, 500)
high <- c(seq(500, 481500, 500),481631)

doParallel::registerDoParallel(4)

foreach(b = 1:length(low)) %dopar% {
  print(b)
  df <- data[,low[b]:high[b]]
  spi_monthly <- SPEI::spi(df, 1, ref.start=c(1981,1), ref.end=c(1999,12))
  spi_annual <- SPEI::spi(df, 12) #, ref.start=c(1981,1), ref.end=c(1999,12))
  save(spi_monthly, file = paste0(path, "replication/data/SPI/monthly_batches/monthly_batch_", b, ".Rdata"))
  save(spi_annual, file = paste0(path, "replication/data/SPI/annual_batches/annual_batch_", b, ".Rdata"))
}

rm(list=setdiff(ls(), c("master_path", "code_path")))
path <- master_path
low <- seq(1,481631, 500)

for(b in 1:length(low)){
  print(b)
  load(paste0(path, "replication/data/SPI/monthly_batches/monthly_batch_", b, ".Rdata"))
  if(b==1){monthly <- spi_monthly$fitted}else{monthly <- cbind(monthly, spi_monthly$fitted)}
}

monthly <- t(monthly)
monthly <- as.data.frame(monthly)
rownames(monthly) <- 1:nrow(monthly)
colnames(monthly) <- paste0("y", rep(c(1981:2021), each = 12), "m", rep(str_pad(c(0:12), 2, pad = "0")))
monthly <- as.integer(monthly*1000)

coords <- read.csv(paste0(path, "replication/data/monthly_dataframes/month_ppt_coordinates.csv"))

monthly <- cbind(coords, monthly)

save(monthly, file = paste0(path, "replication/data/SPI/spi_monthly_dataframe.Rdata"))


rm(monthly)

for(b in 1:length(low)){
  print(b)
  load(paste0(path, "replication/data/SPI/annual_batches/annual_batch_", b, ".Rdata"))
  spi_annual <- spi_annual$fitted
  spi_annual <- spi_annual[seq(12,492,12),]
  if(b==1){annual <- spi_annual}else{annual <- cbind(annual, spi_annual)}
}

annual <- t(annual)
annual <- as.data.frame(annual)
rownames(annual) <- 1:nrow(annual)
colnames(annual) <- paste0("y", c(1981:2021))

annual <- cbind(coords, annual)

save(annual, file = paste0(path, "replication/data/SPI/spi_annual_dataframe.Rdata"))
