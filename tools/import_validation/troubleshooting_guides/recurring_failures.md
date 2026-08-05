# Analysis of Recurring Production Job Failures 

## 1\. Overview

This document outlines several recurring production job failures, some of these failures are caused by minor or temporary data deletions. By increasing the threshold, we can prevent these jobs from failing due to non-permanent issues. However, before adjusting these thresholds, we will implement new validation rules to ensure that crucial data is never lost, even during minor deletions.  
More details can be found here [DC - Imports Execution Learnings ](https://docs.google.com/spreadsheets/d/1lAm-EPB6o9U9btQHbdRruGhx_DFerlhQF43Ba6skI4Q/edit?gid=1651779522#gid=1651779522)

## 2\. Most Recurring Job Failures

In the previous quarter, the following production jobs experienced the highest frequency of failures:

| Import name | Occurrences | Bug IDs |
| :---- | :---- | :---- |
| BLS\_CES\_State | 4 | [b/482946661](http://b/482946661), [b/500945912](http://b/500945912), [b/502090898](http://b/502090898) |
| USCensusPEP\_Sex | 5 | [b/472605922](http://b/472605922), [b/478186511](http://b/478186511), [b/483219293](http://b/483219293) |
| WorldDevelopmentIndicators | 3 | [b/470415967](http://b/470415967), [b/482902862,](http://b/482902862) [b/489948342](http://b/489948342) |
| EurostatData\_Education\_Enrollment | 3 | [b/474326901](http://b/474326901), [b/481243356,](http://b/481243356) [b/496059688](http://b/496059688) |
| USCensusPEP\_By\_Sex\_Race | 5 | [b/485260648](http://b/485260648), [b/502079403](http://b/502079403) |
| USCensusPEP\_PopulationEstimatebyRace | 5 | [b/486801970](http://b/486801970), [b/493190090](http://b/493190090), [b/497802532](http://b/497802532) |
| EurostatData\_Education\_Attainment | 3 | [b/472606851](http://b/472606851), [b/481245546](http://b/481245546), [b/504879314](http://b/504879314) |
| WorldBankDatasets | 3 | [b/472258775](http://b/472258775), [b/506961224](http://b/506961224) |
| EurostatData\_Fertility | 3 | [b/498154643](http://b/498154643) |
| USCensusPEP\_AgeSexRace | 3 | [b/500622108](http://b/500622108) |
| USCensusPEP\_Annual\_Population | 3 | [b/479399481](http://b/479399481), [b/4935600377](http://b/4935600377) |

### 2.1 Minor Deletions imports

The following imports frequently experience minor data losses due to broken source URLs or the removal of individual data points at the origin. To address this, we recommend increasing the deletion thresholds based on historical percentages, supplemented by automated validation rules to maintain data integrity.

1. USCensusPEP\_Sex   
2. USCensusPEP\_By\_Sex\_Race  
3. USCensusPEP\_PopulationEstimatebyRace   
4. USCensusPEP\_AgeSexRace  
5. USCensusPEP\_Annual\_Population  
6. EurostatData\_Education\_Attainment  
7. EurostatData\_Fertility  
8. EurostatData\_Education\_Enrollment 

### 2.2 Major Deletions Imports

The following import jobs have experienced significant data deletions resulting from annual benchmarking conducted by the data sources, who have officially announced these changes:

1. BLS\_CES\_State  
2. WorldDevelopmentIndicators  
3. WorldBankDatasets

While these major deletions are unavoidable due to source updates, we intend to raise the threshold to accommodate and manage any minor deletions that may occur with some validation rules.

**Note:** The current baseline threshold for deletions is **0.01%** (doesn’t contain crucial data) any deletion greater than the threshold should be stored as historical.

## 3\. Imports with a Single Deletion Incident

The following imports have experienced exactly one minor deletion incident from the source. If these deletions recur, we will increase the thresholds and apply automated validation rules.

1. EurostatData\_Employment\_Per\_Sector  
2. EIA\_Electricity  
3. EIA\_NaturalGas  
4. EIA\_Petroleum  
5. EIA\_SEDS  
6. EIA\_NuclearOutages  
7. EurostatData\_GDP

