// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package geo

import "strings"

// USNameToAlpha2 returns the two-letter US code for the given entity, or an empty
// string if there is no match. Inputs can be of any casing or spacing.  e.g.,
// "New York", "NewYork", "Newyork", "new   york" will all match to "NY".
//
// Note that the alpha-2 here is not to be confused with from ISO 3166-1 Alpha-2 or
// ISO 3166-2 codes.
func USNameToAlpha2(name string) string {
	// transform the input to ideally match the way its stored in the mapping.
	name = strings.ReplaceAll(name, " ", "")
	name = strings.ReplaceAll(name, ".", "")
	// TODO: any other pieces that would likely be seen in the wild that
	// should be dropped before the lookup?  '_', ',' ?

	// If there is a match it is returned, otherwise the empty string is returned.
	return usStateToAlpha2Map[strings.ToLower(name)]
}

// usStateToAlpha2Map holds the mapping of the lowercase location name to the
// two-letter code for the place. This include the 50 states, D.C., outlying
// territories, and the country itself.
var usStateToAlpha2Map = map[string]string{
	"alabama":            "AL",
	"alaska":             "AK",
	"arizona":            "AZ",
	"arkansas":           "AR",
	"california":         "CA",
	"colorado":           "CO",
	"connecticut":        "CT",
	"delaware":           "DE",
	"districtofcolumbia": "DC",
	"florida":            "FL",
	"georgia":            "GA",
	"hawaii":             "HI",
	"idaho":              "ID",
	"illinois":           "IL",
	"indiana":            "IN",
	"iowa":               "IA",
	"kansas":             "KS",
	"kentucky":           "KY",
	"louisiana":          "LA",
	"maine":              "ME",
	"maryland":           "MD",
	"massachusetts":      "MA",
	"michigan":           "MI",
	"minnesota":          "MN",
	"mississippi":        "MS",
	"missouri":           "MO",
	"montana":            "MT",
	"nebraska":           "NE",
	"nevada":             "NV",
	"newhampshire":       "NH",
	"newjersey":          "NJ",
	"newmexico":          "NM",
	"newyork":            "NY",
	"northcarolina":      "NC",
	"northdakota":        "ND",
	"ohio":               "OH",
	"oklahoma":           "OK",
	"oregon":             "OR",
	"pennsylvania":       "PA",
	"rhodeisland":        "RI",
	"southcarolina":      "SC",
	"southdakota":        "SD",
	"tennessee":          "TN",
	"texas":              "TX",
	"utah":               "UT",
	"vermont":            "VT",
	"virginia":           "VA",
	"washington":         "WA",
	"washingtondc":       "DC",
	"westvirginia":       "WV",
	"wisconsin":          "WI",
	"wyoming":            "WY",

	// U.S. Territories
	"guam":          "GU",
	"puertorico":    "PR",
	"americansamoa": "AS",
	// Within US look ups, virgin islands is assumed to mean US not British
	"virginislands":   "VI",
	"usvirginislands": "VI",

	"northernmarianaislands": "MP",

	"minoroutlyingterritories": "UM",

	// Also include the country name and variations.
	"UnitedStates":          "US",
	"UnitedStatesOfAmerica": "US",
}
