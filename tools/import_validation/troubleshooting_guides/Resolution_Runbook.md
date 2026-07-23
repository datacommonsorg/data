**PRODUCTION INCIDENT**

**RESOLUTION RUNBOOK**

**Organization / Product: DATA COMMONS**

*\[\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\]*

| Version | *\[e.g1. 1.0\]* |
| :---- | :---- |
| **Last Reviewed** | *\[Date\]* |
| **Runbook Owner** | *\[Name / Team\]* |
| **On-call Rotation** | *\[Link or name\]* |
| **Status Page URL** | *\[URL\]* |
| **Incident Channel** | *\[e.g. \#incidents\]* |

## **Overview:**

This runbook outlines resolutions for production failures, serving as a continuous guide for troubleshooting and support.

## **Types of Production Failure** 

| TYPE | ERROR NAME | MEANING |
| :---- | :---- | :---- |
| **VALIDATION ERROR** | Found 0.01% deleted records | Production environment data deletion detected |
| **LINT ERROR** | Existence\_MissingReference\_observationAbout | Data Commons does not contain the specified mapping/place DCID. |
| **MISSING REFERENCE**  | Existence\_MissingReference\_variableMeasured | The Data Commons repository is currently missing the required SV/dcid reference.  |
| **Command Failed ExitCode 1** | Subprocess Failed  | Failed due to code/development issue |
| **FALSE NEGATIVE** | Could be any failure out of above 4 | Failed once because of an issue with the cloud, server, or source.  |

1. ##  **Validation Failure**

| If a job fails due to data deletions, first identify the source of the deletion. Data deletions can occur in two scenarios: |
| :---- |

   **Case 1: Source-Level Deletion**  
    The data has been officially removed from the source system. In this case, the standard deletion handling rules apply:

   * If the deleted data is less than **0.01%** and does not contain critical data, the import threshold can be increased.  
   * If the deleted data is greater than **0.01%**, the deleted records must be stored as historical data.

   **Case 2: Pipeline/Code Issue**  
     The data deletion is caused unintentionally due to a pipeline, transformation, or code issue. In this scenario, investigate and fix the underlying issue before proceeding further.

**Resolution Steps**

1. Review the latest run of the job in the `datcom-prod-imports` bucket under the `datcom` project using the import name.  
2. If the job folder timestamp is older than one week, re-trigger the job to generate the latest output.  
3. Examine `input0/validation/nodes_deleted.mcf` to review deletion details.  
4. Validate whether the deletions originated from the source or were caused by a pipeline/code issue.  
5. Apply the appropriate resolution based on the identified deletion scenario.

**How to store Historical data**

1. Verify the production version of the import via [Data Commons/Version](https://datacommons.org/version).  
2. Locate and download the production CSV from the storage bucket, matching the date specified in the Data Commons version.  
3. Run the script in your local environment, then utilize Python code to perform a difference comparison between the latest and production output CSVs.  
4. Run the differ on output & historical data table\_mcf\_nodes.mcf files together & ensure no deletion flags are there.  
5. Once the deleted rows are identified & no deletions with this historical file through the comparison,   
6. Upload this historical data (along with its tmcf file) to the 'unresolved' path for that import, and use the importer to write it to the Knowledge Graph (KG).  
7. Once the data is saved to the Knowledge Graph, use the COPY Service to move the file to CNS.  
8. Add the historical path where you have added the file in the CNS as a historical record

**Note:** If a folder for historical data already exists for this import, place the new file inside it. If not, create a new folder.

 

## 

## 

## **LINT ERROR**

| When dcid/mapping is missing in Data Commons |
| :---- |

1. Review the latest run of the job in the `datcom-prod-imports` bucket under the `datcom` project using the import name.  
2. If the job folder timestamp is older than one week, re-trigger the job to generate the latest output.  
3. Check for **Existence\_MissingReference\_observationAbout** in the report.json inside the input0/genmcf/report.json  
4. Look for the observationAbouts’s that are throwing the error  
5.  Run the import locally an update or create the MCF file with the necessary mappings, keep adding mappings until the error is gone from report.json.  
6. Add these mappings to the current CNS file or create a new one by creating a CL.

| When the Data Commons API fails to locate the dcid or mapping |
| :---- |

 1\.	Existence\_FailedDcCall\_observationAbout  
Existence\_FailedDcCall\_observationAbout

## **MISSING REFERENCE**

## 

| When SV or schema is missing in Data Commons |
| :---- |

1. Review the latest run of the job in the `datcom-prod-imports` bucket under the `datcom` project using the import name.  
2. If the job folder timestamp is older than one week, re-trigger the job to generate the latest output.  
3. Check for **Existence\_MissingReference\_variableMeasured** in the report.json inside the input0/genmcf/report.json  
4. Look for the Variable measured (value-ref) that are throwing the warnings  
5.  Run the import locally and update or create the MCF file with the necessary mappings,keep adding mappings until the error is gone from report.json  
6. Add these mappings to the current CNS file or create a new one by creating a CL.

## **Command Failed ExitCode 1**

| When the code fails due to any issue |
| :---- |

1. Restart the job in the cloud environment; if it succeeds, the previous failure likely resulted from a transient environmental problem.  
2. If the issue persists after re-triggering the job, execute the process in a local environment to identify and resolve code defects.

## **FALSE NEGATIVE**

| When the code fails due to any  random temporary issue |
| :---- |

1. 

