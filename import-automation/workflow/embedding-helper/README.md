# Embedding Helper

This module helps generate embeddings for nodes in a Google Cloud Spanner database. It fetches nodes of specific types (e.g., `StatisticalVariable`, `Topic`) that have been updated, generates embeddings using a remote ML model in Spanner, and stores the results in the `NodeEmbeddings` table.

## Files

-   `main.py`: The entry point script that orchestrates the workflow.
-   `embedding_utils.py`: Utility functions for interacting with Spanner and processing nodes.
-   `requirements.txt`: Python dependencies.
-   `test/`: Unit tests.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script expects the following environment variables to be set:

-   `SPANNER_INSTANCE`: The ID of the Spanner instance.
-   `SPANNER_DATABASE`: The ID of the Spanner database.
-   `SPANNER_PROJECT`: The ID of the Google Cloud project.

Run the script:

```bash
export SPANNER_INSTANCE="your-instance-id"
export SPANNER_DATABASE="your-database-id"
export SPANNER_PROJECT="your-project-id"

python main.py
```

## Running Tests

To run the tests, you can use the standard `unittest` module.

From the `embedding-helper` directory:

```bash
python -m unittest discover -s test -p "*_test.py"
```
