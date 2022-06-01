## Prevalence of Asthma in adults and children at a county-level

This import adds the prevalence of Asthma among children and adults at a county-level. 

The statistics for prevalence of asthma among adults is for counties in 50 states and prevalence of asthma among children is for counties in 27 participating states. The data source is the 2016–2018 Behavioral Risk Factor Surveillance System (BRFSS) which is merged with the 2013 National Center for Health Statistics (NCHS) Urban-Rural Classification Scheme for Counties. 

The dataset is extracted from [this public PDF report](https://www.cdc.gov/asthma/national-surveillance-data/pdfs/State-maps-for-asthma-prevalence-by-six-level-urban-rural-classification-2016-2018-p.pdf).

To generate the import artefacts, use the following command,

```bash
python3 brfss_asthma_import.py
```

### Notes
1. The tabular data was extracted from the PDF using [tabula-online](http://tabula.ondata.it/). Since, the tables in the PDF are present in different regions of the pages, we need to draw separate bounding boxes around the tables in each page. This step is made easy in [tabula-online](http://tabula.ondata.it/).
2. Once the tabular data was extracted we compared it with the source PDF file to ensure that there were no missing data points
3. Some county names were incomplete, to resolve their names we find the names used in the [Power BI app](https://app.powerbigov.us/view?r=eyJrIjoiZmZmOWU2N2ItYzllZi00N2I4LWE1NGItYWMxNmU3MTJmYmY4IiwidCI6IjljZTcwODY5LTYwZGItNDRmZC1hYmU4LWQyNzY3MDc3ZmM4ZiJ9) from which the PDF was exported
4. The statistical variables for this import are constant and are defined as a static string.