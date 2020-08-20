# Import Progress Dashboard API

This directory contains code of a REST API that manages information
about import progress and logs.

# Data Model

TODO(intrepiditee): Add descriptions, fields.

There are three types of resources:
1. System Run
2. Import Attempt
3. Progress Log

# Endpoints

TODO(intrepiditee): Add arguments.

1. /system_runs
2. /system_runs/{run_id}
3. /system_runs/{run_id}/logs
4. /import_attempts/{attempt_id}
5. /import_attempts/{attempt_id}/logs
6. /logs
7. /logs/{log_id}


# Deploying to App Engine

```
gcloud app deploy
```

# Running Tests

```
. run_test.sh
```

The Datastore emulator must be installed for the tests to run.
See https://cloud.google.com/datastore/docs/tools/datastore-emulator.
Running run_test.sh will attempt to install the emulator.
