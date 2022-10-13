# Property-Value map for India census data
{
    # File level Properties.
    "EC1200A1-2022-09-15": {
        # "observationDate": "",
        # "measurementMethod": "",
    },
    # Column: "Geographic Area Name (NAME)",
    # values
    "United States": {
        "observationAbout": "dcs:country/USA",
    },

    # Column: 2012 NAICS code (NAICS2012)",
    "2012 NAICS code (NAICS2012)": {
        "naics": "dcs:NAICS/{NaicsCode}",
        "#Regex": "(?P<NaicsCode>^[0-9]+)",
    },
    "Year (YEAR)": {
        "observationDate": "{@Number}",
        "Year": "{@Number}",  # Reference used in other PVs below
    },

    # Column: "Meaning of Tax status code (TAXSTAT_LABEL)",
    "Meaning of Tax status code (TAXSTAT_LABEL):All establishments": {
        "taxStatus": "",
    },
    "Establishments subject to federal income tax": {
        "taxStatus": "dcs:SubjectToFederalIncomeTax",
    },
    "Establishments exempt from federal income tax": {
        "taxStatus": "dcs:ExemptFromFederalIncomeTax",
    },

    # Column: "Meaning of Type of operation code (TYPOP_LABEL)",
    "Manufacturers' sales branches and offices:All establishments": {
        "businessOperationType": "",
    },
    "Manufacturers' sales branches and offices": {
        "businessOperationType": "dcs:ManufacturerSalesBranchesAndOffices",
    },
    "Merchant wholesalers, except manufacturers' sales branches and offices": {
        "businessOperationType":
            "dcs:MerchantWholesalersExcludingManufacturerSalesBranchesAndOffices",
    },

    # Column: Number of establishments (ESTAB)
    # SVObs
    "Number of establishments (ESTAB)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:count",
        "measurementQualifier": "",
        "value": "{Number}",
        "MultiplyFactor": 1,
        "unit": "",
        "observationDate": "{Year}",
        "statType": "dcs:measuredValue",
    },

    # Column: "Sales, value of shipments, or revenue ($1,000) (RCPTOT)"
    "Sales, value of shipments, or revenue ($1,000) (RCPTOT)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:receiptsOrRevenue",
        "measurementQualifier": "dcs:Annual",
        "value": "{Number}",
        "MultiplyFactor": 1000,
        "unit": "dcs:USDollar",
        "observationDate": "{Year}",
        "statType": "dcs:measuredValue",
    },

    # Column: Annual payroll ($1,000) (PAYANN)
    # SVObs
    "Annual payroll ($1,000) (PAYANN)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:payroll",
        "measurementQualifier": "dcs:Annual",
        "value": "{Number}",
        "MultiplyFactor": 1000,
        "unit": "dcs:USDollar",
        "observationDate": "{Year}",
        "statType": "dcs:measuredValue",
    },

    # Column: "First-quarter payroll ($1,000) (PAYQTR1)",
    # SVObs:
    "First-quarter payroll ($1,000) (PAYQTR1)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:payroll",
        "measurementQualifier": "dcs:Quarterly",
        "value": "{Number}",
        "MultiplyFactor": 1000,
        "unit": "dcs:USDollar",
        "observationDate": "{Year}-03",
        "statType": "dcs:measuredValue",
    },

    # Column: "Number of employees (EMP)",
    "Number of employees (EMP)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:numberOfEmployees",
        "measurementQualifier": "",
        "value": "{Number}",
        "MultiplyFactor": 1,
        "unit": "",
        "observationDate": "{Year}",
        "statType": "dcs:measuredValue",
    },

    # Column: "Relative standard error of estimate of the value of business done
    # (RCPTOT_S)"
    "Relative standard error of estimate of the value of business done (RCPTOT_S)":
        {
            "populationType": "dcs:USCEstablishment",
            "measuredProperty": "dcs:receiptsOrRevenue",
            "value": "{Number}",
            "statType": "dcs:marginOfError",
            "MultiplyFactor": 1,
            "unit": "",
            "observationDate": "{Year}",
            "statType": "dcs:measuredValue",
        },

    # Column: "Relative standard error of annual payroll (%) (PAYANN_S)",
    "Relative standard error of annual payroll (%) (PAYANN_S)": {
        "populationType": "dcs:USCEstablishment",
        "measuredProperty": "dcs:payroll",
        "measurementQualifier": "dcs:Annual",
        "value": "{Number}",
        "MultiplyFactor": 1,
        "unit": "",
        "observationDate": "{Year}",
        "statType": "dcs:marginOfError",
    },

    # Column: "Relative standard error of estimate of first-quarter payroll, employees wages (%) (PAYQTR1_S)",
    "Relative standard error of estimate of first-quarter payroll, employees wages (%) (PAYQTR1_S)":
        {
            "populationType": "dcs:USCEstablishment",
            "measuredProperty": "dcs:payroll",
            "measurementQualifier": "dcs:Quarterly",
            "observationDate": "{Year}-03",
            "value": "{Number}",
            "MultiplyFactor": 1,
            "unit": "",
            "statType": "dcs:marginOfError",
        },
}
