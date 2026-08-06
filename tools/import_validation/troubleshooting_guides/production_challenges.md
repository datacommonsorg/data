## **Production Challenges: Source-Side Complications**

### 1\. Structural and Schema Modifications

Pipeline disruptions frequently arise from unexpected modifications to source data structures. These breaking changes—including altered formats, deleted records, or revised schema definitions—interfere with established ingestion and processing workflows.

Information regarding the most frequent types of import failures can be found [DC - Imports Execution Learnings ](docs_summary/dc_imports_execution_learnings.md)

*Historical instances requiring code adjustments:*

1. WorldBankDatasets: [Reference Documentation](docs_summary/world_bank_datasets_summary.md)  
2. EurostatData\_lifeexpectency: [Reference Documentation](docs_summary/eurostat_life_expectancy_summary.md)  
3. UsMontlyRetailSales: [Reference Documentation](docs_summary/us_monthly_retail_sales_summary.md)

**Standard Remediation Protocol**

1. Verify the failure by searching for the specific import name within *validation\_output.csv* located in the `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)` bucket.  
2. In cases involving data loss, investigate whether the records were intentionally removed at the source or if a mismatch has occurred, then establish the necessary correction.

### 1\. Data structure changes (Schema changes)

Modifications to source data are causing pipeline failures. When a data source alters its format, removes records, or changes schema definitions without notice, it introduces breaking changes that disrupt our ingestion and processing workflows.  
For example, code fixes were required after changes occurred in the following datasets:

1. WorldBankDatasets: [WorldBankDatasets ](docs_summary/world_bank_datasets_summary.md)  
2. EurostatData\_lifeexpectency: [EurostatData\_LifeExpectancy](docs_summary/eurostat_life_expectancy_summary.md)  
3. UsMontlyRetailSales : [ USMontlyRetailsales](docs_summary/us_monthly_retail_sales_summary.md)

   

**Standard procedures for addressing the problem**

1. Analyze *validation\_output.csv* in the `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)` bucket to confirm the import failure using the import name.  
2. If the error is due to deletions, verify if data was removed at the source or if there is a data mismatch. Determine the appropriate fix.  
3. If a 'missing reference' error occurs, identify the missing entity or mapping (e.g., place DCID or statistical variable). Update the relevant MCF file in Cider and submit a CL.

 

### 2\. Data deletion at source

The data has been officially removed from the source system. In this case, the standard deletion handling rules apply:

* For minor data deletions, implement golden checks to protect critical information and do a subsequent increase in the import threshold.  
  * In instances of large data removal, ensure that all deleted records are preserved as historical data.

1. In case of deletions, we check for generated o/p CSV \-\> in o/p folder of an import/timestamp folder  

   For example, Historical has been stored in [EurostatData\_Employment\_Per\_Sector](docs_summary/eurostat_employment_per_sector_summary.md) & latest\_version.txt has been updated in [EIA\_NuclearOutages](docs_summary/eia_nuclear_outages_summary.md)

**Standard procedures for addressing the problem**

1. Review the latest run of the job in the `[<PROD_BUCKET>](gcp_variables.md#prod_bucket)` bucket under the `[<BASE_PROJECT>](gcp_variables.md#base_project)` project using the import name.  
2. If the job folder timestamp is older than one week, re-trigger the job to generate the latest output.  
3. Examine `input0/validation/nodes_deleted.mcf` to review deletion details.  
4. Validate whether the deletions originated from the source or were caused by a pipeline/code issue.  
5. Apply the appropriate resolution based on the identified deletion scenario.

### 3\. Downtime or modifications to source URLs

These failures are typically caused by one of the following reasons:

* The source URL is completely broken or no longer active.  
* The external source changed the URL structure or moved the data to a new location.  
* The external source's server is temporarily unresponsive.  
* A firewall is blocking our connection to the source URL.  
  The `UsCensusPep_xxx` data import pipeline has experienced frequent failures (28 occurrences to date) due to issues with the source URLs. eg: [USCensusPEP\_AgeSexRace](docs_summary/uscensuspep_agesexrace_summary.md)

**Standard procedures for addressing the problem**

1. Restart the pipeline; if the issue persists, monitor the URL performance over the next several hours/days.  
2. In cases where the source URLs have been fully replaced or relocated, modify the codebase or the relevant configuration settings accordingly.  
3. If the URL is completely deleted and there is no new link:  
* Use **historical data** if a large amount of data is missing. (only if core teams approves)  
* Update the **`latest_version.txt`** file to keep the pipeline running.(only if core team approves)

### 4\. API Issues (Limits & Failures)

The pipeline can fail if we hit the API rate limit (too many requests) or if the API stops working entirely. 

The BLS\_CES import process utilizes an API for data retrieval; however, executing the import twice can occasionally trigger API rate limits:  [BLS Imports Issues](docs_summary/bls_imports_issues_summary.md)

**Standard procedures for addressing the problem**

1. **Wait it Out:** If we hit a temporary rate limit or timeout issue, wait for the lockout period to end and try again later.  
2. **Switch the API:** If the API is completely broken, no longer supported, or constantly failing, change the code to use an alternative API with a fallback logic.

### 5.Missing reference errors due to additional source data

The pipeline fails with a `missingReferenceObservationAbout` or `missingReferencesVariableMeasured` error when the source website adds new data (like new locations or new variables) that do not exist in our system yet. Because Data Commons doesn't recognize these new entities, the import fails.

The EIA\_SEDS  & US\_SAT\_ACT\_Participation imports  has some data additions [EIA\_SEDS-2026-](docs_summary/eia_seds_summary.md) & [Support P2 - Auto Refresh Failed Imports: US\_SAT\_ACT\_Participation](bugs_summary/507394518.md)

**Standard procedures for addressing the problem**

1. Identify the missing place DCID or Statistical Variable from the error log. Add it to the existing `.mcf` file if the additions are valid.  
2. Raise a CL to merge the updates and fix the pipeline.

