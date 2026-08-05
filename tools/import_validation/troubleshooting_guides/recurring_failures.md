# Analysis of Recurring Production Job Failures 

## 1\. Overview

This document outlines several recurring production job failures, some of these failures are caused by minor or temporary data deletions. By increasing the threshold, we can prevent these jobs from failing due to non-permanent issues. However, before adjusting these thresholds, we will implement new validation rules to ensure that crucial data is never lost, even during minor deletions.  
More details can be found here [DC - Imports Execution Learnings ](docs_summary/dc_imports_execution_learnings.md

## 2\. Most Recurring Job Failures

In the previous quarter, the following production jobs experienced the highest frequency of failures:

| Import name | Occurrences | Bug IDs |
| :---- | :---- | :---- |
| BLS\_CES\_State | 4 | [b/482946661](bugs_summary/482946661.md), [b/500945912](bugs_summary/500945912.md), [b/502090898](bugs_summary/502090898.md) |
| USCensusPEP\_Sex | 5 | [b/472605922](bugs_summary/472605922.md), [b/478186511](bugs_summary/478186511.md), [b/483219293](bugs_summary/483219293.md) |
| WorldDevelopmentIndicators | 3 | [b/470415967](bugs_summary/470415967.md), [b/482902862,](bugs_summary/482902862.md) [b/489948342](bugs_summary/489948342.md) |
| EurostatData\_Education\_Enrollment | 3 | [b/474326901](bugs_summary/474326901.md), [b/481243356,](bugs_summary/481243356.md) [b/496059688](bugs_summary/496059688.md) |
| USCensusPEP\_By\_Sex\_Race | 5 | [b/485260648](bugs_summary/485260648.md), [b/502079403](bugs_summary/502079403.md) |
| USCensusPEP\_PopulationEstimatebyRace | 5 | [b/486801970](bugs_summary/486801970.md), [b/493190090](bugs_summary/493190090.md), [b/497802532](bugs_summary/497802532.md) |
| EurostatData\_Education\_Attainment | 3 | [b/472606851](bugs_summary/472606851.md), [b/481245546](bugs_summary/481245546.md), [b/504879314](bugs_summary/504879314.md) |
| WorldBankDatasets | 3 | [b/472258775](bugs_summary/472258775.md), [b/506961224](bugs_summary/506961224.md) |
| EurostatData\_Fertility | 3 | [b/498154643](bugs_summary/498154643.md) |
| USCensusPEP\_AgeSexRace | 3 | [b/500622108](bugs_summary/500622108.md) |
| USCensusPEP\_Annual\_Population | 3 | [b/479399481](bugs_summary/479399481.md), [b/4935600377](bugs_summary/4935600377.md) |

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

