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

#### `initialize_database`
Initializes the Spanner database by creating all necessary tables and uploading proto descriptors.

*   This action requires no payload parameters. It automatically reads `schema.sql` and `storage.pb` from the container directory to provision the database schema and proto descriptors.
*   **Note on Protos**: The `storage.pb` file is generated during the Docker build process. The `Dockerfile` fetches `storage.proto` from the `datacommonsorg/import` GitHub repository and compiles it into `storage.pb`.

## Local Development and Testing

To run the helper service locally and test its functionality:

### Running the Server
Ensure you have installed the requirements (`uv pip install -r requirements.txt`), then start the functions framework:

```bash
uv run functions-framework --target ingestion_helper
```
By default, this will start serving on `http://localhost:8080`.

### Triggering Actions
You can test specific actions by sending a POST request with a JSON payload. For example, to trigger database initialization locally:
```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"actionType": "initialize_database"}'
```
