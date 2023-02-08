# US: Pregnancy Risk Assessment Monitoring System 

## About the Dataset
This dataset has Population Estimates for Pregnancy Risk Assessment Monitoring System in USA for the years 2016,2017,2018,2019,2020.

The population is categorized by various set of combinations as below:
        
        1. Nutrition.
        2. Pre-Pregnancy Weight.
        3. Substance Use.
        4. Intimate Partner Violence.
        5. Depression.
        6. Health Care Services.
        7. Pregnancy Intention.
        8. Postpartum Family Planning.
        9. Oral Health.
        10. Health Insurance Status One Month Before Pregnancy.
        11. Health Insurance Status for Prenatal Care.
        12. Health Insurance Status Postpartum.
        13. Infant Sleep Practices.
        14. Breastfeeding Practices.
        

### Download URL
The data in .pdf formats are downloadable from https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/ -> 	State Name.
The actual URLs are listed in input_files.py.
Example: "https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/Alabama-PRAMS-MCH-Indicators-508.pdf"


#### API Output
These are the attributes that will be used
| Attribute      		                        | Description                                                   |
|-------------------------------------------------------|---------------------------------------------------------------|
| Year       					| The Year of the population estimates provided. 	                |
| Geo       					| The Area of the population estimates provided. 			|
| Nutrition  				| Multivitamin Use. 					|
| Pre-Pregnancy Weight   	| The level of weight before pregnancy.  |
| Substance Used in Smoking and Drinking 		|Substances like Cigarettes, ECigarettes and Hookah being used				|
| Intimate Partner Violence 				| Violence by Husband or Partner.					|
| Depression   			| Self Reported Depression.      |
| Health Care Services   				| Services like Flu shot, prenatal care and maternal checkup.					|
| Pregnancy Intention   				| Intentions like unwanted, mistimed and Intended Pregnancy.				|
| Postpartum Family Planning   				| Use of contaceptive methods or postpartum contaception.				|
| Oral Health   				| Teeth cleaned during pregnancy				|
| Health Insurance Status One Month Before Pregnancy   			| Type of Insurance- Private, Medicaid, No Insurance.			|
| Health Insurance Status for Prenatal Care   				| Type of Insurance- Private, Medicaid, No Insurance.				|
| Health Insurance Status Postpartum   				| Type of Insurance- Private, Medicaid, No Insurance.				|
| Infant Sleep Practices   				| Baby often laid on back to sleep.				|
| Breastfeeding Practices   				| Ever Breastfed or breastfeeding at 8 weeks.				|



#### Cleaned Data
Cleaned data will be inside [output/PRAMS.csv] as a CSV file with the following columns.

- Geo
- SV
- Year
- Observation



#### MCFs and Template MCFs
- [output/PRAMS.mcf]
- [output/PRAMS.tmcf]

### Running Tests

Run the test cases

`python3 -m unittest scripts/cdc_prams/process_test.py`
`sh ./run_tests.sh -p scripts/cdc_prams`




### Import Procedure

The below script will download the data and extract it.

`/bin/python scripts/cdc_prams/input_files.py`

The below script will clean the data, Also generate final csv, mcf and tmcf files.

`/bin/python scripts/cdc_prams/process.py`