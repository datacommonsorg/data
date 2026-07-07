# Import Differ

This utility generates a diff of two versions of a dataset for import analysis.

**Usage**

***Prerequisites***
- Python/Pandas is installed for native runner mode.
- Java JRE/JDK is installed for direct runner mode.
- gcloud ADC is configured for cloud runner mode.

```bash
python3 import_differ.py \
  --current_data=<path> \
  --previous_data=<path> \
  --output_location=<path> \
  --file_format=<mcf/tfrecord> \
  --runner_mode=<native/direct/cloud> \
  --project_id=<id> \
  --job_name=<name>
```

***Parameters***
- current\_data: Path to the current data (wildcard on local/GCS supported).
- previous\_data: Path to the previous data (wildcard on local/GCS supported).
- output\_location: Path to the output data folder (local/GCS).
- file\_format: Format of the input data (mcf,tfrecord).
- runner\_mode: Runner mode: native (Python) / direct (Java runner) /cloud (Dataflow in Cloud).
- project\_id: GCP project Id for the dataflow job.
- job\_name: Name of the differ dataflow job.


***Output***

The utility generates a summary of the differences and detailed MCF files.

**Summary Output**
A summary is printed to the logs and also written to `differ_summary.json` in the output directory:
```json
{
    "current_version": "path/to/current",
    "previous_version": "path/to/previous",
    "current_obs_count": 1000,
    "previous_obs_count": 950,
    "current_schema_count": 100,
    "previous_schema_count": 95,
    "added_obs_count": 50,
    "deleted_obs_count": 0,
    "modified_obs_count": 10,
    "added_schema_count": 5,
    "deleted_schema_count": 0,
    "modified_schema_count": 0,
    "obs_diff_count": 60,
    "schema_diff_count": 5
}
```

**Detailed Diff Files**
Detailed diff output is written to MCF files in the output directory:
- nodes-added.mcf: MCF nodes added in the current version
- nodes-deleted.mcf: MCF nodes deleted in the current version
- nodes-modified.mcf: MCF nodes modified in the current version
