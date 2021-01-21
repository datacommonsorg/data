# Data Commons Scripts

These are scripts used to format data into MCF or TMCF + CSV format for ingestion into Data Commons.
This also contains scripts for automatically generating schema files associated with those data imports.

## Overview

- [biomedical](biomedical) is the subdirectory containing scripts to format data for Biomedical
  Data Commons (BMDC).

## Adding a dataset for auto-refresh to DC

Prerequisite: Make sure you have verified the generated MCF before working on auto-fresh MCF. These are documented in [Summer 2020 Intern Data Import Workflow](go/dc-summer2020#2020-intern-workflow).
- Auto script CSV & MCF 
  - Add manifest.json under the subdirectory and tag the PR following [import-automation README](../import-automation/README.md).
  - After submitting PR, check that a [Cloud Scheduler job](https://pantheon.corp.google.com/cloudscheduler?project=google.com:datcom-data&folder=&organizationId=) for the import is created. 
  - Either wait till the job gets scheduled or manually clicks [RUN NOW](https://screenshot.googleplex.com/5yDXFYh25bZ824d). Upon success,  you shall see data generated under the corresponding [directory](https://pantheon.corp.google.com/storage/browser/datcom-prod-imports/scripts?project=datcom-204919&pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&prefix=&forceOnObjectsSortingFiltering=false).
  - [Import Progress Dashboard](https://dashboard-frontend-dot-datcom-data.uc.r.appspot.com/) can be helpful. Click the down arrow at the left side for more information. 
- Add the import to side cache
  - Add import to side_cache_mcfs.textproto. 
    - Set perform_automated_mcf_generation for converting CSV & TMCF to MCF.
    - Set download_config which tells source CSV & TMCF on bigstore and destination path on CNS.
    - Set resolution_info. Specify KG_MCF option when need the StatVar nodes.
    - Table entry shall be set when resolution input is an external table. 
  - To verify side_cache_mcfs change, follow the IMPORTANT NOTE at the top of side_cache_mcfs, as well as [Import Controller README](https://g3doc.corp.google.com/datacommons/import/controller/README.md?cl=352915178).
  - Check branch cache growth with command: 
    ```
    gsutil du -s -h <BIGSTORE_DIR>
    ```
    Attach the result to cl description. 