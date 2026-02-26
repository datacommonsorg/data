# Ingestion Helper Cloud Function

This Cloud Function provides helper routines for the Data Commons Spanner ingestion workflow. It handles tasks such as locking, status updates, and import list retrieval.

## Usage

The function expects a JSON payload with a required `actionType` parameter, which determines the operation to perform.

### Common Parameters

*   `actionType` (Required): A string specifying the action to execute.

### Supported Actions and Parameters

#### `get_import_info`
Gets the details of imports that are ready for ingestion.

*   `importList` (Optional): list of imports to ingest.

#### `acquire_ingestion_lock`
Attempts to acquire the global lock for ingestion to prevent concurrent modifications.

*   `workflowId` (Required): The ID of the workflow attempting to acquire the lock.
*   `timeout` (Required): The duration (in seconds) for which the lock should be held.

#### `release_ingestion_lock`
Releases the global ingestion lock.

*   `workflowId` (Required): The ID of the workflow releasing the lock.

#### `update_ingestion_status`
Updates the status of imports after an ingestion job completes.

*   `importList` (Required): A list of import names involved in the ingestion.
*   `workflowId` (Required): The ID of the workflow.
*   `status` (Required): Import status.
*   `jobId` (Required): The Dataflow job ID associated with the ingestion.

#### `update_import_status`
Updates the status of a specific import job.

*   `importName` (Required): The name of the import.
*   `status` (Required): The new status to set.
*   `jobId` (Optional): The Dataflow job ID.
*   `executionTime` (Optional): Execution time in seconds.
*   `dataVolume` (Optional): Data volume in bytes.
*   `latestVersion` (Optional): Latest version string.
*   `graphPath` (Optional): Graph path regex.
*   `nextRefresh` (Optional): Next refresh timestamp.


#### `update_import_version`
Updates the version of an import, records version history, and updates the status.

*   `importName` (Required): The name of the import.
*   `version` (Required): The version string. If set to `'STAGING'`, it resolves to the current staging version.
*   `comment` (Required): A comment for the audit log explaining the version update.
*   `override` (Optional): Override version without checking import status (boolean)
