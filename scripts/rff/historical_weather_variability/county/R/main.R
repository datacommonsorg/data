## Generate weather variability metrics v2 ###

if(!("pacman" %in% installed.packages())){install.packages("pacman")}
require(pacman)
p_load(rstudioapi, raster, terra, foreach, parallel, doParallel,
       stringr, Rfast,SPEI,rgdal, tigris, reshape2)

master_path <- str_split(getSourceEditorContext()$path, "replication/code")[[1]][1]
code_path <- paste0(master_path, "replication/code/")

# Make monthly data frames for ppt, tmin, tmax 
source(paste0(code_path, "monthly_dataframes.R"))

# Heatwave metrics 
source(paste0(code_path, "heatwave_annual_rasters.R"))
source(paste0(code_path, "heatwave_5year_rasters.R"))
source(paste0(code_path, "heatwave_rasters_to_df.R"))

# Interannual ranges 
source(paste0(code_path, "interannual_ranges.R"))
source(paste0(code_path, "ranges_rasters_to_df.R"))

# SPI 
source(paste0(code_path, "spi_calculate_batches.R"))

# County aggregation
source(paste0(code_path, "county_aggreation.R"))


