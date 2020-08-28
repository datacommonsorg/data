# Cloud Build Configuration

This directory contains a Cloud Build configuration that creates asynchronous
tasks using Cloud Tasks on pull requests and pushes to master to trigger the
executor.

The tasks pass information about the commits to the executor and can optionally
pass any configurations for the executor.