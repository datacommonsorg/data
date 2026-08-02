#!/bin/bash
source undata/run_batch_import.sh
while read -r f; do
    process_dataset "$f"
done < undata/logs/file_list.txt
