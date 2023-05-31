library(raster)
library(tidyverse)
library(tidycensus)
library(sf)
library(stringr)
library(future.apply)

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

aab <- read_csv("aab_western_counties.csv") %>% 
        mutate(forest_burned_acres = burned_cells*0.222395)


create_data <- function(geography, variable, aggregation = "sum", weight = NA, save = T) {
  
  keepvars <- c("countyfips","year", variable)
  if (!is.na(weight)) keepvars <- c(keepvars, weight)
  
  df <- aab %>% dplyr::select(keepvars)

  if (geography == "state") {
    
      df <- df %>% mutate(st_fips = substr(countyfips,1,2)) 
      
      if (aggregation == "mean") {
        df <- df %>% 
            group_by(st_fips,year) %>% 
            summarize(variable = weighted.mean(get(variable), get(weight))) 
      } else if (aggregation == "sum") {
        df <- df %>% 
          group_by(st_fips,year) %>% 
          summarize(variable = sum(get(variable), na.rm = T))
      }
      
  }
  
  if (geography == "west") {
    
    if (aggregation == "mean") {
        df <- df %>% 
              group_by(year) %>% 
              summarize(variable = weighted.mean(get(variable), get(weight)))
    } else if (aggregation == "sum") {
      df <- df %>% 
        group_by(year) %>% 
        summarize(variable = sum(get(variable), na.rm = T))
    }
  } 
   
  if (save == TRUE) {
  
    dst <- sprintf("%s/", variable)
    dir.create(dst, recursive = T, showWarnings = F)
    write.csv(df, sprintf("%s/%s_%s", variable, variable, geography))
  
    }
  
  return(df)
    
  }

create_decadal_data <- function(geography, variable, aggregation, weight, save = T) {
  
  df <- create_data(geography = geography,
                                variable = variable,
                                aggregation = aggregation, 
                                weight = weight) %>% 
          mutate(decade = ifelse(year <= 1994, "1985-1994", 
                            ifelse(year >= 1995 & year <= 2004, "1995-2004", 
				ifelse(year >= 2005 & year <= 2014, "2005-2014", "2014-2017"))))
  
  if (geography == "county") {
    df <- df %>% group_by(countyfips, decade) %>% 
            summarize(variable = mean(get(variable), na.rm = T)) 
  } else if (geography == "state") {
    df <- df %>% group_by(st_fips, decade) %>% 
      summarize(variable = mean(variable, na.rm = T)) 
  } else {
    df <- df %>% group_by(decade) %>% 
      summarize(variable = mean(variable, na.rm = T)) 
  }
  
  
  if (save == TRUE) {
    
    dst <- sprintf("%s/", variable)
    dir.create(dst, recursive = T, showWarnings = F)
    write.csv(df, sprintf("%s/%s_%s_decadal", variable, variable, geography))
    
  }
  
  return(df)
    
  }

   
data_dictionary <- data.frame(geography = rep(c("county","state","west"),3),
                              variables = lapply(c("forest_burned_acres", 
                                                   "pct_forest_burned",
                                                   "pct_high_severity"), function(x) rep(x,3)) %>% unlist(),
                              aggregation = lapply(c("sum", 
                                                   "mean",
                                                   "mean"), function(x) rep(x,3)) %>% unlist(),
                              weight = lapply(c(NA, 
                                                     "forest_cells",
                                                     "burned_cells"), function(x) rep(x,3)) %>% unlist()) %>% 
                    mutate(weight = ifelse(geography == "county", NA, weight))


lapply(seq(1, dim(data_dictionary)[1]), function(i)
       create_data(data_dictionary$geography[i],
                   data_dictionary$variables[i],
                   data_dictionary$aggregation[i],
                   data_dictionary$weight[i]))

lapply(seq(1, 6), function(i)
    create_decadal_data(data_dictionary$geography[i],
              data_dictionary$variables[i],
              data_dictionary$aggregation[i],
              data_dictionary$weight[i]))


