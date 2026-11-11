{
    # PV mappings for BEA GDP
    
    #Map Fips as observationAbout - maintain separate maping to dcid
    'GeoFIPS': {
        'observationAbout': '{@Data}',
        'populationType': 'EconomicActivity',
        'measuredProperty': 'amount',
        'activitySource': 'GrossDomesticProduction',
        'observationPeriod': 'P1Y',
        'measurementQualifier': 'RealValue',
    },
    
    #Map Year columns
    
    '2001': {
        'observationDate': '2001',
        'value': '{@Number}',
    },
    '2002': {
        'observationDate': '2002',
        'value': '{@Number}',
    },
    '2003': {
        'observationDate': '2003',
        'value': '{@Number}',
    },
    '2004': {
        'observationDate': '2004',
        'value': '{@Number}',
    },
    '2005': {
        'observationDate': '2005',
        'value': '{@Number}',
    },
    '2006': {
        'observationDate': '2006',
        'value': '{@Number}',
    },
    '2007': {
        'observationDate': '2007',
        'value': '{@Number}',
    },
    '2008': {
        'observationDate': '2008',
        'value': '{@Number}',
    },
    '2009': {
        'observationDate': '2009',
        'value': '{@Number}',
    },
    '2010': {
        'observationDate': '2010',
        'value': '{@Number}',
    },
    '2011': {
        'observationDate': '2011',
        'value': '{@Number}',
    },
    '2012': {
        'observationDate': '2012',
        'value': '{@Number}',
    },
    '2013': {
        'observationDate': '2013',
        'value': '{@Number}',
    },
    '2014': {
        'observationDate': '2014',
        'value': '{@Number}',
    },
    '2015': {
        'observationDate': '2015',
        'value': '{@Number}',
    },
    '2016': {
        'observationDate': '2016',
        'value': '{@Number}',
    },
    '2017': {
        'observationDate': '2017',
        'value': '{@Number}',
    },
    '2018': {
        'observationDate': '2018',
        'value': '{@Number}',
    },
    '2019': {
        'observationDate': '2019',
        'value': '{@Number}',
    },
    '2020': {
        'observationDate': '2020',
        'value': '{@Number}',
    },
    '2021': {
        'observationDate': '2021',
        'value': '{@Number}',
    },
    '2022': {
        'observationDate': '2022',
        'value': '{@Number}',
    },
    '2023': {
        'observationDate': '2023',
        'value': '{@Number}',
    },	
    #Map Unit
    'Thousands of chained 2017 dollars':{
        '#Multiply': 1000,
        'unit': 'ChainedUSDollarBaseYr2017',
    },
    # Map industries : 
    'Accommodation and food services': {
        'naics': 'dcs:NAICS/72',
    },
    'Agriculture, forestry, fishing and hunting':{
        'naics': 'dcs:NAICS/11',
    },
    'Mining, quarrying, and oil and gas extraction':{
        'naics': 'dcs:NAICS/21',
    },
    'Utilities':{
        'naics': 'dcs:NAICS/22',
    },
    'Construction':{
        'naics': 'dcs:NAICS/23',
    },
    'Manufacturing':{
        'naics': 'dcs:NAICS/1013',
    },
    'Durable goods manufacturing':{
        'naics': 'dcs:NAICS/JOLTS_320000',
    },
    'Nondurable goods manufacturing':{
        'naics': 'dcs:NAICS/JOLTS_340000',
    },
    'Wholesale trade':{
        'naics': 'dcs:NAICS/42',
    },
    'Retail trade':{
        'naics': 'dcs:NAICS/44-45',
    },
    'Transportation and warehousing':{
        'naics': 'dcs:NAICS/48-49',
    },
    'Information':{
        'naics': 'dcs:NAICS/51',
    },
    'Finance, insurance, real estate, rental, and leasing':{
        'naics': 'dcs:NAICS/52-53',
    },
    'Finance and insurance':{
        'naics': 'dcs:NAICS/52',
    },
    'Real estate and rental and leasing':{
        'naics': 'dcs:NAICS/53',
    },
    'Professional and business services':{
        'naics': 'dcs:NAICS/JOLTS_540099',
    },
    'Professional, scientific, and technical services':{
        'naics': 'dcs:NAICS/54',
    },
    'Management of companies and enterprises':{
        'naics': 'dcs:NAICS/55',
    },
    'Administrative and support and waste management and remediation services':{
        'naics': 'dcs:NAICS/56',
    },
    'Educational services, health care, and social assistance':{
        'naics': 'dcs:NAICS/61-62',
    },
    'Educational services':{
        'naics': 'dcs:NAICS/61',
    },
    'Health care and social assistance':{
        'naics': 'dcs:NAICS/62',
    },
    'Arts, entertainment, recreation, accommodation, and food services':{
        'naics': 'dcs:NAICS/71-72',
    },
    'Arts, entertainment, and recreation':{
        'naics': 'dcs:NAICS/71',
    },
    'Other services (except government and government enterprises)':{
        'naics': 'dcs:NAICS/81',		#check mapping - otherservices except public administration
    },
    'Government and government enterprises':{
        "#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    },
    'Natural resources and mining':{
        'naics': 'dcs:NAICS/1011',
    },
    'Trade':{
    	"#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    },
    'Transportation and utilities':{
        "#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/4849',	**** Not mapped
    },
    'Manufacturing and information':{
        "#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    },
    'Private goods-producing industries':{
        "#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    },
    'Private services-providing industries':{
        "#ignore": "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    },
    'Private industries':{
        "#ignore" : "Ignore missing NAICS",
        #'naics': 'dcs:NAICS/',		**** Not mapped
    }

}

