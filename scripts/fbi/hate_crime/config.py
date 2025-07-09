hate_crime_api_url = "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime.zip"
hate_crime_publication_api_url = [
        {
            "api_url": "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime_2023.zip",
            "output_folder": "hate_crime_publication_data/hate_crime_publication_2023_data_xlsx", 
            "target_extension": ".xlsx" 
        },
        {
            "api_url": "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime_2022.zip", 
            "output_folder": "hate_crime_publication_data/hate_crime_publication_2022_data_xlsx",
            "target_extension": ".xlsx"
        },
        {
            "api_url": "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime_2021.zip", 
            "output_folder": "hate_crime_publication_data/hate_crime_publication_2021_data_xlsx",
            "target_extension": ".xls" 
        },
         {
            "api_url": "https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime_2020.zip",
            "output_folder": "hate_crime_publication_data/hate_crime_publication_2020_data_xlsx",
            "target_extension": ".xlsx" 
        }
    ]