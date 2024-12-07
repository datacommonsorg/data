- import_name: "Indonesia_Census"

- source: https://www.bps.go.id/en/statistics-table?subject=522

- how to download data: Manual download from source 
  `To download the data` visit the website and select the desired year. Then, click on the download button to save the file to your computer."
  
   `https://www.bps.go.id/en/statistics-table/2/NDIjMg==/number-of-disease-cases--cases-.html`
   `https://www.bps.go.id/en/statistics-table/2/MjMyIzI=/number-of-general-hospitals--special-hospitals--and-public-health-centers--unit-.html`   
   `https://www.bps.go.id/en/statistics-table/1/MTU2OSMx/aids-cummulative-cases--death-cases--cases-rate--and-new-number-cases-by-province-in-       	    indonesia--2008-2012.html`
   `https://www.bps.go.id/en/statistics-table/2/MjE4IzI=/percentage-of-married-women-aged-15-49-years-old-currently-using-contraception-method--percent-.html`
   `https://www.bps.go.id/en/statistics-table/2/MTQzNSMy/percentage-of-population-aged-15-years-and-older-who-smoked-tobacco-by-province--percent-.html`
   `https://www.bps.go.id/en/statistics-table/2/MTQwMiMy/unmet-need-of-health-services-by-province--percent-.html`
   `https://www.bps.go.id/en/statistics-table/1/MTYxNyMx/percentage-of-population-having-health-complaint-by-province--urban-rural-classification--and-sex--2009-2023.html`
   `https://www.bps.go.id/en/statistics-table/1/MTYyMCMx/percentage-of-population-with-outpatient-treatment-during-the-previous-month-by-province--2009-2023.html`
   `https://www.bps.go.id/en/statistics-table/3/YTA1Q1ptRmhUMEpXWTBsQmQyZzBjVzgwUzB4aVp6MDkjMw==/disease-by-province-and-type-of-disease.html?year=2018`


- type of place: life expectancy sheet having AA2 & AA3 while all other sheets contain place at the country level AA1. 

- statvars: Health

- years: 2000 to 2023

- place_resolution:  places are resolved based on name.

### How to run:
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_health/test_data/sample_input/<filename>.xlsx --pv_map=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_health/pvmap/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_place_resolved.csv --config=statvar_imports/indonesia_bps_statistics/indonesia_census/indonesia_health/metadata/<filename>_metadata.csv  --output_path=output_path=<filepath/filename>

### Licence:
license : "https://prabumulihkota.beta.bps.go.id/en/term-of-use"

