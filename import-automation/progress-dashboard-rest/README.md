# Import Progress Dashboard REST API

This directory contains code of a REST API that manages information
about import attempts.

The Datastore emulator must be running for these tests to run.
In a different terminal, run
'gcloud beta emulators datastore start --no-store-on-disk'.
In the terminal where the tests will be run, run
'$(gcloud beta emulators datastore env-init)' and proceed to run the tests.

See https://cloud.google.com/datastore/docs/tools/datastore-emulator.
