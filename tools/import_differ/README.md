# Import Differ

This utility generates a diff of two versions of a dataset for import analysis.

**Usage**

***Prerequisites***
- Python/Pandas is installed for native runner mode.
- gcloud ADC is configured for cloud runner mode.

```bash
python import_differ.py \
  --current_data=<path> \
  --previous_data=<path> \
  --output_location=<path> \
  --file_format=<mcf/tfrecord> \
  --runner_mode=<local/cloud> \
  --job_name=<name>
```

***Parameters***
- current\_data: Path to the current data (wildcard on local/GCS supported).
- previous\_data: Path to the previous data (wildcard on local/GCS supported).
- output\_location: Path to the output data folder (local/GCS).
- file\_format: Format of the input data (mcf,tfrecord).
- runner\_mode: Runner mode: local (Python) / cloud (Dataflow in Cloud).
- project\_id: GCP project Id for the dataflow job.
- job\_name: Name of the differ dataflow job.


***Output***

Summary output generated is of the form below showing counts of differences for each variable.

| variableMeasured | ADDED | DELETED | MODIFIED |
| :--- | :--- | :--- | :--- |
| dcid:var1 | 1 | 0 | 0 |
| dcid:var2 | 0 | 2 | 1 |
| dcid:var3 | 0 | 0 | 1 |
| dcid:var4 | 0 | 2 | 0 |

Detailed diff output is written to files for further analysis. Sample result files can be found under folder 'test/results'.
- obs\_diff\_summary.csv: diff summary for observation analysis
- obs\_diff\_samples.csv: sample diff for observation analysis
- obs\_diff\_log.csv: diff log for observations
- schema\_diff\_summary.csv: diff summary for schema analysis
- schema\_diff\_log.csv: diff log for schema nodes 
