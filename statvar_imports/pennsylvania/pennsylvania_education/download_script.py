import os
import requests

def download_file(url, output_path):
    print(f'Downloading {url} to {output_path}...')
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print('Download complete.')

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    input_files_dir = os.path.join(base_path, 'input_files')

    datasets = {
        'educational_attainment_by_age_range_and_gender': 'xwn6-8rmw',
        'post_secondary_completions_total_awards_degrees': 'jqcu-bcsg',
        'public_school_enrollment_by_county_grade_and_race': 'wb8u-h3s8',
        'undergraduate_stem_enrollment': 'r75w-4bue'
    }

    for folder, data_id in datasets.items():
        url = f'https://data.pa.gov/api/views/{data_id}/rows.csv?accessType=DOWNLOAD'
        output_path = os.path.join(input_files_dir, f'{folder}.csv')
        download_file(url, output_path)

if __name__ == '__main__':
    main()
