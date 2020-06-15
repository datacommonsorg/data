package geo

import (
	"testing"
)

func TestUSNameToAlpha2(t *testing.T) {
	tests := []struct {
		have string
		want string
	}{
		// Non matching values.
		{have: "", want: ""},
		{have: "Ontario", want: ""},
		{have: "Nueva York", want: ""},
		{have: "USA", want: ""},
		{have: "pizZa", want: ""},
		{have: "8675309", want: ""},
		{have: "O1h3i5o9", want: ""},

		// Matching values.
		{have: "            New Y or k      ", want: "NY"},
		{have: "New York", want: "NY"},
		{have: "NewYork", want: "NY"},
		{have: "UTAH", want: "UT"},
		{have: "aLaSKa", want: "AK"},
		{have: "New.....York", want: "NY"},
		{have: "U.S. Virgin Islands", want: "VI"},
		{have: "virgin Islands", want: "VI"},
	}

	for _, test := range tests {
		if got := USNameToAlpha2(test.have); got != test.want {
			t.Errorf("USNameToAlpha2(%s) = %v, want %v", test.have, got, test.want)
		}
	}
}
