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
