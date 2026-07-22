## **Production Challenges: Source-Side Complications**

### 1\. Structural and Schema Modifications

Pipeline disruptions frequently arise from unexpected modifications to source data structures. These breaking changes—including altered formats, deleted records, or revised schema definitions—interfere with established ingestion and processing workflows.

Information regarding the most frequent types of import failures can be found [DC - Imports Execution Learnings ](https://docs.google.com/spreadsheets/d/1lAm-EPB6o9U9btQHbdRruGhx_DFerlhQF43Ba6skI4Q/edit?gid=1651779522#gid=1651779522).

*Historical instances requiring code adjustments:*

1. WorldBankDatasets: [Reference Documentation](https://docs.google.com/document/d/1ExMv5_J4vSEY1OVwWLoXbvnH1ltjRsfcBjUqSyw6uXo/edit?tab=t.0)  
2. EurostatData\_lifeexpectency: [Reference Documentation](https://docs.google.com/document/d/1h4ETCMddDTWPCCZnE8OaHNYKFAH2WHtUX9tGCxV5caY/edit?resourcekey=0-h6BHDUjBSyHS2v-mCfCKUw&tab=t.0#heading=h.by7ahuiow2gz)  
3. UsMontlyRetailSales: [Reference Documentation](https://docs.google.com/document/d/1mVoeHRkdlnPvTpu-IMee-6d2GQ-htlLDRP2ZYdGW04w/edit?tab=t.0#heading=h.by7ahuiow2gz)

**Standard Remediation Protocol**

1. Verify the failure by searching for the specific import name within *validation\_output.csv* located in the `datcom-prod-imports` bucket.  
2. In cases involving data loss, investigate whether the records were intentionally removed at the source or if a mismatch has occurred, then establish the necessary correction.

### 1\. Data structure changes (Schema changes)

Modifications to source data are causing pipeline failures. When a data source alters its format, removes records, or changes schema definitions without notice, it introduces breaking changes that disrupt our ingestion and processing workflows.  
For example, code fixes were required after changes occurred in the following datasets:

1. WorldBankDatasets: [WorldBankDatasets ](https://docs.google.com/document/d/1ExMv5_J4vSEY1OVwWLoXbvnH1ltjRsfcBjUqSyw6uXo/edit?tab=t.0)  
2. EurostatData\_lifeexpectency: [EurostatData\_LifeExpectancy](https://docs.google.com/document/d/1h4ETCMddDTWPCCZnE8OaHNYKFAH2WHtUX9tGCxV5caY/edit?resourcekey=0-h6BHDUjBSyHS2v-mCfCKUw&tab=t.0#heading=h.by7ahuiow2gz)  
3. UsMontlyRetailSales : [ USMontlyRetailsales](https://docs.google.com/document/d/1mVoeHRkdlnPvTpu-IMee-6d2GQ-htlLDRP2ZYdGW04w/edit?tab=t.0#heading=h.by7ahuiow2gz)

   

**Standard procedures for addressing the problem**

1. Analyze *validation\_output.csv* in the `datcom-prod-imports` bucket to confirm the import failure using the import name.  
2. If the error is due to deletions, verify if data was removed at the source or if there is a data mismatch. Determine the appropriate fix.  
3. If a 'missing reference' error occurs, identify the missing entity or mapping (e.g., place DCID or statistical variable). Update the relevant MCF file in Cider and submit a CL.

 

### 2\. Data deletion at source

The data has been officially removed from the source system. In this case, the standard deletion handling rules apply:

* For minor data deletions, implement golden checks to protect critical information and do a subsequent increase in the import threshold.  
  * In instances of large data removal, ensure that all deleted records are preserved as historical data.

1. In case of deletions, we check for generated o/p CSV \-\> in o/p folder of an import/timestamp folder  
2. 

   For example, Historical has been stored in  [EurostatData\_Employment\_Per\_Sector](https://docs.google.com/document/d/1CPyqi9DBjv0t4eWanNYMRfJTIGjhubN6Op2Sao5S-9Y/edit?resourcekey=0-lNpBO1oS4JQOJaGE2uj2Rg&tab=t.0#heading=h.by7ahuiow2gz)   & latest\_version.txt has been updated in [EIA\_NuclearOutages](https://docs.google.com/document/d/1GfF_sdUCg4d3fmkJoRCarQpFoGtLIPfezoKwoEXXL84/edit?tab=t.0#heading=h.10kuxd1t3o0u) 

**Standard procedures for addressing the problem**

1. Review the latest run of the job in the `datcom-prod-imports` bucket under the `datcom` project using the import name.  
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
  The `UsCensusPep_xxx` data import pipeline has experienced frequent failures (28 occurrences to date) due to issues with the source URLs. eg: [USCensusPEP\_AgeSexRace](https://docs.google.com/document/d/10_kFWkpkon9xhVOlOXjIFF0fSyO2IGFKWq6H1pcAcVE/edit?tab=t.0#heading=h.by7ahuiow2gz)

**Standard procedures for addressing the problem**

1. Restart the pipeline; if the issue persists, monitor the URL performance over the next several hours/days.  
2. In cases where the source URLs have been fully replaced or relocated, modify the codebase or the relevant configuration settings accordingly.  
3. If the URL is completely deleted and there is no new link:  
* Use **historical data** if a large amount of data is missing. (only if core teams approves)  
* Update the **`latest_version.txt`** file to keep the pipeline running.(only if core team approves)

### 4\. API Issues (Limits & Failures)

The pipeline can fail if we hit the API rate limit (too many requests) or if the API stops working entirely. 

The BLS\_CES import process utilizes an API for data retrieval; however, executing the import twice can occasionally trigger API rate limits:  [BLS Imports Issues](https://docs.google.com/document/d/1bQbwKMVPtcehUZ3zI3r2kGlidMiE6UjEN9faKlJgtUs/edit?resourcekey=0-wJrxn96bZK7RUR196cSNfA&tab=t.0#heading=h.8rkahuqo26x9)

**Standard procedures for addressing the problem**

1. **Wait it Out:** If we hit a temporary rate limit or timeout issue, wait for the lockout period to end and try again later.  
2. **Switch the API:** If the API is completely broken, no longer supported, or constantly failing, change the code to use an alternative API with a fallback logic.

### 5.Missing reference errors due to additional source data

The pipeline fails with a `missingReferenceObservationAbout` or `missingReferencesVariableMeasured` error when the source website adds new data (like new locations or new variables) that do not exist in our system yet. Because Data Commons doesn't recognize these new entities, the import fails.

The EIA\_SEDS  & US\_SAT\_ACT\_Participation imports  has some data additions [EIA\_SEDS-2026-](https://docs.google.com/document/d/1Kvhz-7AaWpaxSvSN1wHDP75-3CVXTfZT7dffBgZNTaY/edit?resourcekey=0-YG8JZHFyO_xnEdqmg_4NMQ&tab=t.0#heading=h.by7ahuiow2gz) [Support P2 - Auto Refresh Failed Imports: US\_SAT\_ACT\_Participation](https://b.corp.google.com/issues/507394518)

**Standard procedures for addressing the problem**

1. Identify the missing place DCID or Statistical Variable from the error log. Add it to the existing `.mcf` file if the additions are valid.  
2. Raise a CL to merge the updates and fix the pipeline.

