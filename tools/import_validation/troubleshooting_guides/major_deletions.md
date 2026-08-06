# **Validating Deletions for the Import**

 The validation process involves : examining the cloud job logs, replicating the import run on a local machine, and identifying the cause of record deletions to implement a permanent fix.

## **Check the Cloud Logs to See What Failed**

First, we need to find out why the job failed by looking at the cloud logs and the error messages.

1. **Check the Cloud Batch Job:**  
   Go to the Cloud Batch Jobs console and find the latest run for the import.  
   * Here is the job I looked at for this import: Cloud Batch Job: `worlddevelopmentindicators-1781002802` (Project: `[<AUTO_REFRESH_PROJECT>](gcp_variables.md#auto_refresh_project)`, Region: `us-central1`)  
2. **Look for Errors in the Logs:**  
   Even if the job status says "Succeeded," it might still have errors. Look through the logs (you can use the errors filter to jump straight to them). In my case, the job failed some validation checks because of deletions.  
   * **Error Message:** Found 0.87% deleted records, which is over the threshold of 0%.  
3. **Check the Production Bucket:**  
   Next, head over to the production cloud bucket to find the specific files for this job run. Navigate down the correct path for the import:  
   Project: `[<PROD_PROJECT>](gcp_variables.md#prod_project)`, Bucket: `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)`, Path: `scripts/world_bank/wdi/WorldDevelopmentIndicators`
   * Go to the folder with the latest timestamp as the job you just looked at: 2026\_06\_09T04\_07\_31\_200635\_07\_00  
4. **Review the Validation Files:**  
   Go into the input0/validation/ folder. Here, you want to look at two specific files:  
   * **validation\_output.csv:** This tells you the exact reason the checks failed. In my case, 3 checks passed, but the check\_deleted\_records\_percent failed because 3,908 records were deleted. (See table below)  
      * Location: Project: `[<PROD_PROJECT>](gcp_variables.md#prod_project)`, Bucket: `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)`, Path: `scripts/world_bank/wdi/WorldDevelopmentIndicators/2026_06_09T04_07_31_200635_07_00/input0/validation/validation_output.csv`
   * **Nodes\_deleted.mcf:** This file shows you the actual list of records that were deleted.  
      * Location: Project: `[<PROD_PROJECT>](gcp_variables.md#prod_project)`, Bucket: `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)`, Path: `scripts/world_bank/wdi/WorldDevelopmentIndicators/2026_06_09T04_07_31_200635_07_00/input0/validation/obs_diff_log.csv`

## **Run the Import Locally**

Now, we need to run the import process on our own computer. This helps us confirm if the deletions are really happening, or if it was just a transient failure in the cloud job.

### **Automated Run using `run_import.sh` (Recommended)**
Instead of executing every step manually (running parser scripts, executing the Java import-tool to build/lint MCFs, downloading previous baselines, and running the differ tool), you can use the unified **`run_import.sh`** utility script. It automates the entire local execution and validation flow.

   #### **Theory of Operation:**
   * **Parses the Manifest:** It reads `manifest.json` for the import's resource constraints and import specifications.
   * **Prepares the Environment:** It downloads the required `import-tool.jar` and configures execution defaults.
   * **Runs User Scripts:** It executes the downloader and generator scripts defined in the manifest.
   * **Validates & Runs Diff Checks:** It automatically generates output MCFs, runs lint validations, pulls the previous successful version from GCS to compare, and generates the final validation report (`validation_output.csv` and `obs_diff_log.csv`).

   #### **Execution Commands:**
   Navigate to the root directory of your repository and run one of the following commands:

   * **Using Docker (Highly Recommended):** Runs the pipeline in a clean container, avoiding local dependency issues.
     ```bash
     ./import-automation/executor/run_import.sh -docker scripts/world_bank/wdi/manifest.json
     ```
     *If you want to build and use a Docker image with your latest local code changes:*
     ```bash
     ./import-automation/executor/run_import.sh -d dc-test-executor -docker scripts/world_bank/wdi/manifest.json
     ```

   * **Using your Local Python Host Environment:**
     ```bash
     ./import-automation/executor/run_import.sh scripts/world_bank/wdi/manifest.json
     ```
   The execution outputs, logs, and final validation reports will be stored in `/tmp/WorldDevelopmentIndicators/` (or the folder path specified by `-o <output_dir>`).

---

### **Manual Run (Alternative)**
If you prefer to run the individual steps of the pipeline manually:

1. **Clone the GitHub Repository:**  
   Clone the Datacommons data repository to your machine: [https://github.com/datacommonsorg/data.git](https://github.com/datacommonsorg/data.git). Once cloned, navigate to the exact same import path we looked at in the bucket.  
2. **Run the Scripts:**  
   Check the [manifest.json](https://github.com/datacommonsorg/data/blob/master/scripts/world_bank/wdi/manifest.json) file in that folder to understand how the job runs, and manually run the scripts and processes it outlines.

3. **Generate the MCF File:**  
   Run the lint and genmcf tests to generate the table.mcf file, which we will need for the differ tool. Run these commands:  
   * java \-jar java-jar.jar lint output.csv output.tmcf  
   * java \-jar java-jar.jar genmcf output.csv output.tmcf  
4. **Get the Previous Data:**  
   To run the differ tool, we need to compare the table.mcf file we just created (the current data) with the table.mcf file from the previous successful run.  
   * Find the timestamp of the last successful run by checking the `latest_version.txt` file in the cloud bucket. GCS Location: Project: `[<PROD_PROJECT>](gcp_variables.md#prod_project)`, Bucket: `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)`, Path: `scripts/world_bank/wdi/WorldDevelopmentIndicators/latest_version.txt`
   * Go to that timestamp's folder in the bucket and download its table.mcf file.  
5. **Run the Differ Tool:**  
   Now, run this command to compare the two files:  
   python3 import\_differ.py \--current\_data= \--previous\_data= \--output\_location= \--file\_format=mcf \--runner\_mode=local  
6. **Confirm the Results:**  
   Open the dc\_generated/nodes\_deleted.mcf folder and the validation\_output.csv on your local machine. If they match the results we saw in the cloud bucket during Phase 1, we know the results are accurate\!

## **Validate Deletions from the Source**

Now that we know the deletions are real, we need to validate them against the original data source to confirm the source actually removed the data.

1. **Locate the Textproto File:** To find out exactly where the data came from, check the `textproto` file for this import. For WorldDevelopmentIndicators, the file path is: `google3/datacommons/import/mcf/manifest/international_stats/WorldDevelopmentIndicators.textproto`  
   * You can search for this file using Google Code Search: [WorldDevelopmentIndicators.textproto Link](screens/wdi_textproto_source.png)
2. **Find the Source URL:** Open the `textproto` file and look for the line that says: `provenance_url: "https://datatopics.worldbank.org/world-development-indicators/"` This URL tells us exactly where the data is downloaded from.  
3. **Navigate the Source Website:** Open that source URL. On the World Bank website, click on the **Explore Data** option, and then click on **Access Data**. This will allow you to see their entire dataset.  
4. **Manually Verify Deleted Records:** check at your `nodes_deleted.mcf` file and pick out 5 to 6 specific deleted records. Go back to the World Bank website and manually filter the data by entering the parameters for those specific records.  
   * *If you do not get any data for them (or the data is missing), this confirms that the data was accurately deleted from the source.*

   *Example :* The job failed because some specific data points present in the previous production version are missing in the current version.

* **Source Deletion:** The record  has been removed from the source.  
1) [Source Screenshot](screens/3oK73RXvox3xeTM.png) | [Differ Screenshot](screens/BWYDfWvTNZoixSE.png)   
2) [Source Screenshot](screens/8znJ3XadmGGRmdL.png) | [Differ Screenshot](screens/4JKbhAxnJz6SGbJ.png)  
3) [Source Screenshot](screens/5Nw3dA9a3iH7GAM.png) | [Differ Screenshot](screens/7ovdMycUe7tiADw.png)   
* These deletions are confirmed as intentional source-side changes from the World Bank’s April 2026 update.

  WDI April 8, 2026 Changelog [Screenshot](screens/497zku465XJzsJt.png) | [Link](https://datatopics.worldbank.org/world-development-indicators/release-note/apr-2026.html)

5. In my case, the amount of data getting deleted from the source was very huge. When this happens, we cannot just ignore it. We need to:  
   * **Create a validation error document:** Document the massive deletion properly so there is a clear record of why the job threshold failed and what was removed. [BLS\_CES\_State\_20\_04\_2026](docs_summary/bls_ces_state_deletion_resolution.md)
   * **Store the data historically:** Keep a record of the deleted data. (need approval from core team)  
6. Check for the affected SVs deleted that we find out by taking unique deleted SVs  from the differ & check in BigQuery (Table: `[<BQ_PROJECT>](gcp_variables.md#bq_project).dc_kg_latest.NLStatVars`) if these Svs are present in the NL SVs table.  
7. Because the deletions are minor & from the source the next would be store Historical data & because it had recurring failure  golden checks \+ threshold increase as per history deletions will also be implemented ( All these steps must be mentioned in the validation error document because we need core team approval to store historical & update the latest\_version.txt)

   ## **How to implement golden checks?**

   Consult the following resource for instructions on incorporating goldens into your import process: [Implementation Guide: Golden Set Validations](docs_summary/golden_set_validations_implementation_guide.md)

   ## **How to store historical data ?**

1.  resolve **validation errors**  
   Preserve the deleted data by storing it in a historical file, which should then be copied to the CNS. Below are the steps:   
   1. Verify the production version of the import via [Data Commons/Version](https://datacommons.org/version).  
      2. Locate and download the production CSV from the storage bucket, matching the date specified in the Data Commons version.  
      3. Run the script in your local environment, then utilize Python code to perform a difference comparison between the latest and production output CSVs.  
      4. Run the differ on output & historical data table\_mcf\_nodes.mcf files together & ensure no deletion flags are there.  
      5. Once the deleted rows are identified & no deletions with this historical file through the comparison, save them to a file and upload it to CNS as a historical record, path shown below.

```
mcf_proto_url: "/cns/jv-d/home/[<BASE_PROJECT>](gcp_variables.md#base_project)/v3_resolved_mcf/us_bls/ces/state/latest/historical_data/graph.tfrecord@1.gz"
 table {
   mapping_path: "/cns/jv-d/home/[<BASE_PROJECT>](gcp_variables.md#base_project)/v3_mcf/wdi/WorldDevelopmentIndicators/historical_data/worldbank.tmcf"
   csv_path: "/cns/jv-d/home/[<BASE_PROJECT>](gcp_variables.md#base_project)/v3_mcf/wdi/WorldDevelopmentIndicators/historical_data/*.csv"
 }
```

   b. To stop these “Deleted” flags from appearing as errors, **the latest\_version.txt file must be updated only after the core team approves.**  This ensures the differ recognizes the change as deliberate to the dataset rather than a data loss error. 

```
experimental/users/ajaits/[<BASE_PROJECT>](gcp_variables.md#base_project)/scripts/import_info.sh -i WorldDevelopmentIndicator-set_latest 2026_04_20_02_42_50_536488_08_00 -note 'details of deletion analysis in b/500945912 reviewed by: <ldap of the approver>'
```

   C. Rerun the pipeline to verify it finishes without issues and check that all tests in *validation\_output.csv* have passed.

      

   

