# Import Differ

This utility generates a diff (point and series analysis) of two versions of the same dataset for import analysis.

**Usage**

***Prerequisites***
- Java is installed for local runner mode.
- gcloud ADC is configured for cloud runner mode.

```
python import_differ.py --current_data=<path> --previous_data=<path> --output_location=<path> --file_format=<mcf/tfrecord> --runner_mode=<local/cloud> --job_name=<name>
```

***Parameters***
- current\_data: Path to the current data (wildcard on local/GCS supported).
- previous\_data: Path to the previous data (wildcard on local/GCS supported).
- output\_location: Path to the output data folder (local/GCS).
- file\_format: Format of the input data (mcf,tfrecord).
- runner\_mode: Dataflow runner mode(local/cloud)
- project\_id: GCP project Id for the bdataflow job.
- job\_name: Name of the differ dataflow job.


***Output***

Summary output generated is of the form below showing counts of differences for each variable.

| |variableMeasured|ADDED|DELETED|MODIFIED|
|---|---|---|---|---|---|---|
|0|dcid:var1|1|0|0
|1|dcid:var2|0|2|1|
|2|dcid:var3|0|0|1|
|3|dcid:var4|0|2|0|

Detailed diff output is written to files for further analysis. Sample result files can be found under folder 'test/results'.
- point\_analysis\_summary.csv: diff summry for point analysis
- point\_analysis\_results.csv: detailed results for point analysis
- series\_analysis\_summary.csv: diff summry for series analysis
- series\_analysis\_results.csv: detailed results for series analysis
