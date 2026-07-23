# Production Failure RCA Runbook

# 1\. Overview

This document provides an overview of the process that can be followed for doing the Root Cause Analysis (RCA) of the errors popping up in the auto refresh pipelines of Data Commons.

# 2\. Background on Auto Refresh Pipelines

The auto refresh pipelines are configured in the Cloud Batch service of the project “datcom-import-automation-prod”. The purpose of these pipelines is to refresh the data on a regular basis for the eligible datasets that have been ingested into Data Commons already. The pipelines perform the following tasks:

1. Download the data from the source  
2. Pre-process the data as required  
3. Generate .csv and .tmcf files (via PV-MAPS or custom .py scripts)  
4. Validate data against the last execution  
5. Ingest the data to Data Commons if every step is successfully completed

# 3\. Errors in auto refresh pipelines

While these pipelines are meant to refresh the data in Data Commons, it is necessary to apply checks and perform data validation before the final ingestion. These checks ensure that the right data is ingested to Data Commons and reduce the probability of wrong data ingestion in Data Commons. Consequently, these pipelines fail in case the necessary checks and validations fail while data processing.

Apart from data checks and validation there could be other probable reasons for the pipeline failures including the compute resources exhaustion, unavailability of data at source, deletion of source, addition of new places in the source data etc.

The process to tackle each of these issues can be different. However, the steps to perform the RCA can be generalised. The next section will cover some of the important  steps that can be taken into consideration for performing RCA.

# 4\. Steps for performing RCA

This section highlights the steps that can be taken to perform RCA for the failed production pipelines. 

Step 1: Go to the looker [dashboard](https://lookerstudio.google.com/c/reporting/e88fda74-50c9-46c6-88aa-c84342ceba48/page/eaXdF) and get the latest status of all the pipelines from the dashboard. The probable different states of each pipelines could be as below:

1. VALIDATION: Data validation failure.  
2. FAILURE: Import job failed.  
3. STAGING: Import job completed, ready for ingestion.  
4. SUCCESS: Data ingestion completed  
5. SKIP: Incoming data is same as production data

Pipelines having the state as “VALIDATION” or “FAILED” are the candidates for performing RCA.

Step 2: Next, for each failed pipeline check the priority status. The same can be determined from the [Code Search](https://source.corp.google.com/)  portal. Search for the import name in the Code Search portal and determine the respective import group for each of the pipelines from the respective manifest.json files.

| Classification | Priority Ranking | import\_groups |
| :---- | :---- | :---- |
| **P0** | 1 | SearchBranch |
| **P0** | 2 | LaeLaps |
| **P0** | 3 | SearchAim |
| **P2** | 4 | Auto1W |
| **P2** | 5 | Auto2W |
| **P2** | 6 | USCensus |
| **P2** | 7 | USBLS |
| **P2** | 8 | WorldBank |
| **P2** | 8 | OECD |
| **P2** | 9 | CDC |
| **P2** | 10 | EuroStat |
| **P2** | 11 | UNSDG |
| **P2** | 12 | BRFSS |

Step 3: Next, go to the Cloud Batch service of the `datcom-import-automation-prod` project and search for the respective import name in the search bar. [Screenshot](https://screenshot.googleplex.com/Bah7SXkdpNu5r7u.png)

Step 4: Based on the type of the failure check the logs for the latest execution of the pipeline.  
**Note: For validation failures, the Cloud Batch portal might show the pipeline “Succeeded” but it is important to check the logs to verify the same**

Step 5:  Next, traverse the logs of the pipelines and search for the respective reason of the failures. A few common reasons of the failure are as mentioned below:

1. Exit code 137 : Signifies that the pipeline failed due to exhaustion of resources  
2. Validation and lint errors: Signifies that the pipeline failed because of validation and lint errors. [Screenshot](https://screenshot.googleplex.com/3nosGztEJKr2pZV)  
3.  Pre processing script failed: Signifies that the script responsible for either downloading the data or processing the data has failed. [Screenshot](https://screenshot.googleplex.com/9KjTNR3EF8644v8)

Step 6: Based on RCA, plan the error resolution. Discuss issues with the CORE TEAM on a need basis. Also, prepare a document capturing the issues and the next actions. [Template](https://docs.google.com/document/d/1PyBmcN-1C_p9y-ML93eaBFyspg1XD5zwkT7EqeTsQsI/edit?resourcekey=0-B5pj3_KBQDpdfNs6AGllXQ&tab=t.0#heading=h.ne6ee5rvmv4h)

Step 7: Change the code (if required) and raise [CL/PR](http://cl/PR) as appropriate. 

Step 8: Once the code is merged with production, force execute the production pipelines using the command below:

```
~/Desktop/DataCommons/data/import-automation/executor/run_import.sh -p <project name> -d dc-test-executor-$USER -cloud -a <docker artifact> <path to manifest file> -batch
```

 

