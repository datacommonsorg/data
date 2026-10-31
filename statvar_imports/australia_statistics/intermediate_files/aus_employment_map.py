{
    "observationAbout": {
        "observationAbout": "dcs:{@Data}",
        "populationType": "dcs:Person",
        "statType":	"measuredValue",
    },
    "Employed total ;  Persons ;" : {
		"employment": "dsc:Employed",
        "value": "{Number}",
    },
	"Employed total ;  > Males ;": {
		"employment": "dsc:Employed",
		"gender": "dcs:Male",
        "measuredProperty": "dcs:count",
        "value": "{Number}",
	},
	"Employed total ;  > Females ;": {
		"employment": "dsc:Employed",
		"gender": "dcs:Female",
        "measuredProperty": "dcs:count",
        "value": "{Number}",
	},
	"observationDate": {
		"observationDate": "{@Data}",
	},
    "Unemployed total ;  Persons ;": {
		"employment": "dsc:Unemployed",
        "measuredProperty": "dcs:count",
        "value": "{Number}",
    },
    "Unemployed total ;  > Males ;": {
		"employment": "dsc:Unemployed",
        "gender": "dcs:Male",
        "measuredProperty": "dcs:count",
        "value": "{Number}",
    },
    "Unemployed total ;  > Females ;": {
		"employment": "dsc:Unemployed",
        "gender": "dcs:Female",
        "measuredProperty": "dcs:count",
        "value": "{Number}",
    },
    "Unemployment rate ;  Persons ;" : {
        "measuredProperty" : "dcs:unemploymentRate",
        "value": "{Number}",
    },
    "Unemployment rate ;  > Males ;": {
        "measuredProperty" : "dcs:unemploymentRate",
        "gender": "dcs:Male",
        "value": "{Number}",
    },
    "Unemployment rate ;  > Females ;": {
        "measuredProperty" : "dcs:unemploymentRate",
        "gender": "dcs:Female",
        "value": "{Number}",
    },
}
