# Property-Value map for India census data
{
    # File level Properties.
    "us_census_B01001_input.csv": {
        "observationDate": "2020",
        "measurementMethod": "dcs:CensusACS5yrSurvey",
        "populationType": "dcs:Person",
    },
    # Row: "Total"
    "Total:": {
        "populationType": "dcs:Person",
        "value": "{Number}",
    },
    "Male:": {
        "gender": "dcs:Male",
    },
    "Female:": {
        "gender": "dcs:Female",
    },

    # Ages
    "Under 5 years": {
        "age": "[- 5 Years]"
    },
    "20 years": {
        "age": "dcs:20Years"
    },
    "21 years": {
        "age": "dcs:21Years"
    },
    "85 years and over": {
        "age": "[85 - Years]"
    },
    "10 to 14 years": {
        "age": "[10 14 Years]"
    },
    "15 to 17 years": {
        "age": "[15 17 Years]"
    },
    "18 and 19 years": {
        "age": "[18 19 Years]"
    },
    "22 to 24 years": {
        "age": "[22 24 Years]"
    },
    "25 to 29 years": {
        "age": "[25 29 Years]"
    },
    "30 to 34 years": {
        "age": "[30 34 Years]"
    },
    "35 to 39 years": {
        "age": "[35 39 Years]"
    },
    "40 to 44 years": {
        "age": "[40 44 Years]"
    },
    "45 to 49 years": {
        "age": "[45 49 Years]"
    },
    "50 to 54 years": {
        "age": "[50 54 Years]"
    },
    "55 to 59 years": {
        "age": "[55 59 Years]"
    },
    "5 to 9 years": {
        "age": "[5 9 Years]"
    },
    "60 and 61 years": {
        "age": "[60 61 Years]"
    },
    "62 to 64 years": {
        "age": "[62 64 Years]"
    },
    "65 and 66 years": {
        "age": "[65 66 Years]"
    },
    "67 to 69 years": {
        "age": "[67 69 Years]"
    },
    "70 to 74 years": {
        "age": "[70 74 Years]"
    },
    "75 to 79 years": {
        "age": "[75 79 Years]"
    },
    "80 to 84 years": {
        "age": "[80 84 Years]"
    },
    #"years": {
    #    "age": "[{StartAge} {EndAge} Years]",
    #        "#Regex": "(?P<StartAge>[0-9]+) (to|and) (?P<EndAge>[0-9]+) years",
    #    },
    "Estimate": {
        "observationDate": "2020",
        "measurementMethod": "dcs:CensusACS5yrSurvey",
        "populationType": "dcs:Person",
        "value": "{Number}",
    },

    # US States
    "Alabama": {
        "observationAbout": "dcid:geoId/01"
    },  # AL
    "Alaska": {
        "observationAbout": "dcid:geoId/02"
    },  # AK
    "Arizona": {
        "observationAbout": "dcid:geoId/04"
    },  # AZ
    "Arkansas": {
        "observationAbout": "dcid:geoId/05"
    },  # AR
    "California": {
        "observationAbout": "dcid:geoId/06"
    },  # CA
    "Colorado": {
        "observationAbout": "dcid:geoId/08"
    },  # CO
    "Connecticut": {
        "observationAbout": "dcid:geoId/09"
    },  # CT
    "Delaware": {
        "observationAbout": "dcid:geoId/10"
    },  # DE
    "District of Columbia": {
        "observationAbout": "dcid:geoId/11"
    },  # DC
    "Florida": {
        "observationAbout": "dcid:geoId/12"
    },  # FL
    "Georgia": {
        "observationAbout": "dcid:geoId/13"
    },  # GA
    "Hawaii": {
        "observationAbout": "dcid:geoId/15"
    },  # HI
    "Idaho": {
        "observationAbout": "dcid:geoId/16"
    },  # ID
    "Illinois": {
        "observationAbout": "dcid:geoId/17"
    },  # IL
    "Indiana": {
        "observationAbout": "dcid:geoId/18"
    },  # IN
    "Iowa": {
        "observationAbout": "dcid:geoId/19"
    },  # IA
    "Kansas": {
        "observationAbout": "dcid:geoId/20"
    },  # KS
    "Kentucky": {
        "observationAbout": "dcid:geoId/21"
    },  # KY
    "Louisiana": {
        "observationAbout": "dcid:geoId/22"
    },  # LA
    "Maine": {
        "observationAbout": "dcid:geoId/23"
    },  # ME
    "Maryland": {
        "observationAbout": "dcid:geoId/24"
    },  # MD
    "Massachusetts": {
        "observationAbout": "dcid:geoId/25"
    },  # MA
    "Michigan": {
        "observationAbout": "dcid:geoId/26"
    },  # MI
    "Minnesota": {
        "observationAbout": "dcid:geoId/27"
    },  # MN
    "Mississippi": {
        "observationAbout": "dcid:geoId/28"
    },  # MS
    "Missouri": {
        "observationAbout": "dcid:geoId/29"
    },  # MO
    "Montana": {
        "observationAbout": "dcid:geoId/30"
    },  # MT
    "Nebraska": {
        "observationAbout": "dcid:geoId/31"
    },  # NE
    "Nevada": {
        "observationAbout": "dcid:geoId/32"
    },  # NV
    "New Hampshire": {
        "observationAbout": "dcid:geoId/33"
    },  # NH
    "New Jersey": {
        "observationAbout": "dcid:geoId/34"
    },  # NJ
    "New Mexico": {
        "observationAbout": "dcid:geoId/35"
    },  # NM
    "New York": {
        "observationAbout": "dcid:geoId/36"
    },  # NY
    "North Carolina": {
        "observationAbout": "dcid:geoId/37"
    },  # NC
    "North Dakota": {
        "observationAbout": "dcid:geoId/38"
    },  # ND
    "Ohio": {
        "observationAbout": "dcid:geoId/39"
    },  # OH
    "Oklahoma": {
        "observationAbout": "dcid:geoId/40"
    },  # OK
    "Oregon": {
        "observationAbout": "dcid:geoId/41"
    },  # OR
    "Pennsylvania": {
        "observationAbout": "dcid:geoId/42"
    },  # PA
    "Rhode Island": {
        "observationAbout": "dcid:geoId/44"
    },  # RI
    "South Carolina": {
        "observationAbout": "dcid:geoId/45"
    },  # SC
    "South Dakota": {
        "observationAbout": "dcid:geoId/46"
    },  # SD
    "Tennessee": {
        "observationAbout": "dcid:geoId/47"
    },  # TN
    "Texas": {
        "observationAbout": "dcid:geoId/48"
    },  # TX
    "Utah": {
        "observationAbout": "dcid:geoId/49"
    },  # UT
    "Vermont": {
        "observationAbout": "dcid:geoId/50"
    },  # VT
    "Virginia": {
        "observationAbout": "dcid:geoId/51"
    },  # VA
    "Washington": {
        "observationAbout": "dcid:geoId/53"
    },  # WA
    "West Virginia": {
        "observationAbout": "dcid:geoId/54"
    },  # WV
    "Wisconsin": {
        "observationAbout": "dcid:geoId/55"
    },  # WI
    "Wyoming": {
        "observationAbout": "dcid:geoId/56"
    },  # WY
    "Guam": {
        "observationAbout": "dcid:geoId/66"
    },  # GU
    "Puerto Rico": {
        "observationAbout": "dcid:geoId/72"
    },  # PR
    "American Samoa": {
        "observationAbout": "dcid:geoId/60"
    },  # AS
    "US Virgin Islands": {
        "observationAbout": "dcid:geoId/78"
    },  # VI
    "Northern Mariana Islands": {
        "observationAbout": "dcid:geoId/69"
    },  # MP
    "Minor Outlying Territories": {
        "observationAbout": "dcid:geoId/74"
    },  # UM
}
