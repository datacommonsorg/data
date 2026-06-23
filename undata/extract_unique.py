import csv
import sys

def get_unique_values(file_path, num_rows=2000):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        unique_values = {field: set() for field in fieldnames}
        for i, row in enumerate(reader):
            if i >= num_rows:
                break
            for field in fieldnames:
                unique_values[field].add(row[field])
    
    for field in fieldnames:
        print(f"{field}: {sorted(list(unique_values[field]))}")

if __name__ == "__main__":
    get_unique_values(sys.argv[1])
