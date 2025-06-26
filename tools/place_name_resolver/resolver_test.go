package main

import (
	"googlemaps.github.io/maps"
	"io/ioutil"
	"log"
	"strings"
	"testing"
)

type MockResolveApi struct{}

func (m *MockResolveApi) Resolve(req *resolveReq) (*resolveResp, error) {
	mockResp := &resolveResp{
		Entities: []resolveRespEntity{
			resolveRespEntity{
				InId:   "ChIJwe1EZjDG5zsRaYxkjY_tpF0",
				OutIds: []string{"wikidataId/Q1156"},
			},
			resolveRespEntity{
				InId:   "ChIJkbeSa_BfYzARphNChaFPjNc",
				OutIds: []string{"country/IND"},
			},
			resolveRespEntity{
				InId:   "ChIJg0f4wxyUmjkRUlulOJtaCxE",
				OutIds: []string{"wikidataId/Q1473962"},
			},
		},
	}
	return mockResp, nil
}

type MockMapsClient struct {
	result_map map[string][]maps.GeocodingResult
}

func (m *MockMapsClient) Geocode(req *maps.GeocodingRequest) ([]maps.GeocodingResult, error) {
	res, ok := m.result_map[req.Address]
	if !ok {
		log.Fatalf("Unexpected Geocode call: %s", req.Address)
		return nil, nil
	}
	return res, nil
}

func getMockGeocodesBasic() *MockMapsClient {
	return &MockMapsClient{
		result_map: map[string][]maps.GeocodingResult{
			"India": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJkbeSa_BfYzARphNChaFPjNc"},
			},
			"Maharashtra": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJ-dacnB7EzzsRtk_gS5IiLxs"},
			},
			"Mumbai": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJwe1EZjDG5zsRaYxkjY_tpF0"},
			},
			// Return the same placeId for both Pratapgarhs.
			"Pratapgarh UP": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJg0f4wxyUmjkRUlulOJtaCxE"},
			},
			"Pratapgarh Rajasthan": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJg0f4wxyUmjkRUlulOJtaCxE"},
			},
		},
	}
}

func getMockGeocodesContainment() *MockMapsClient {
	return &MockMapsClient{
		result_map: map[string][]maps.GeocodingResult{
			"India": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJkbeSa_BfYzARphNChaFPjNc"},
			},
			"Maharashtra, India": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJ-dacnB7EzzsRtk_gS5IiLxs"},
			},
			"Mumbai, Maharashtra, India": []maps.GeocodingResult{
				maps.GeocodingResult{PlaceID: "ChIJwe1EZjDG5zsRaYxkjY_tpF0"},
			},
		},
	}
}

func TestAppendContainedInPlaceNames(t *testing.T) {
	table := []struct {
		name      string
		row       []string
		tinfo     *tableInfo
		expected  string
		shouldErr bool
	}{
		{
			"Simple containment",
			[]string{"n1", "Mumbai", "n2"},
			&tableInfo{
				rows: [][]string{
					{"n1", "Mumbai", "n2"},
					{"n2", "Maharashtra", "n3"},
					{"n3", "India", ""},
				},
				node2row: map[string]int{"n1": 0, "n2": 1, "n3": 2},
				nidIdx:   0,
				nameIdx:  1,
				cipIdx:   2,
			},
			"Mumbai, Maharashtra, India",
			false,
		},
		{
			"No containment",
			[]string{"n1", "India", ""},
			&tableInfo{
				rows:     [][]string{{"n1", "India", ""}},
				node2row: map[string]int{"n1": 0},
				nidIdx:   0,
				nameIdx:  1,
				cipIdx:   2,
			},
			"India",
			false,
		},
		{
			"Unresolved containment ref",
			[]string{"n1", "Mumbai", "n4"}, // n4 does not exist
			&tableInfo{
				rows: [][]string{
					{"n1", "Mumbai", "n4"},
					{"n2", "Maharashtra", "n3"},
				},
				node2row: map[string]int{"n1": 0, "n2": 1},
				nidIdx:   0,
				nameIdx:  1,
				cipIdx:   2,
			},
			"Mumbai", // Should just return the name, and log an error.
			false,
		},
		{
			"Self containment ref",
			[]string{"n1", "Mumbai", "n1"},
			&tableInfo{
				rows:     [][]string{{"n1", "Mumbai", "n1"}},
				node2row: map[string]int{"n1": 0},
				nidIdx:   0,
				nameIdx:  1,
				cipIdx:   2,
			},
			"Mumbai",
			false,
		},
		{
			"Circular dependency",
			[]string{"n1", "A", "n2"},
			&tableInfo{
				rows: [][]string{
					{"n1", "A", "n2"},
					{"n2", "B", "n1"},
				},
				node2row: map[string]int{"n1": 0, "n2": 1},
				nidIdx:   0,
				nameIdx:  1,
				cipIdx:   2,
			},
			"",
			true,
		},
	}

	for _, test := range table {
		t.Run(test.name, func(t *testing.T) {
			// The function under test can call log.Fatalf which will exit the test runner.
			// This is not ideal, but for now we will live with it.
			// A proper fix would be to refactor the code to not call log.Fatalf.
			defer func() {
				if r := recover(); r != nil {
					if !test.shouldErr {
						t.Errorf("appendContainedInPlaceNames() panicked unexpectedly: %v", r)
					}
				}
			}()
			got, err := appendContainedInPlaceNames(test.row, test.tinfo)
			if (err != nil) != test.shouldErr {
				t.Errorf("appendContainedInPlaceNames() error = %v, wantErr %v", err, test.shouldErr)
				return
			}
			if got != test.expected {
				t.Errorf("appendContainedInPlaceNames() = %v, want %v", got, test.expected)
			}
		})
	}
}

func TestGeocodePlaces(t *testing.T) {
	tinfo := &tableInfo{
		rows: [][]string{
			{"n1", "Mumbai", "n2"},
			{"n2", "Maharashtra", "n3"},
			{"n3", "India", ""},
		},
		extNames: []string{
			"Mumbai, Maharashtra, India",
			"Maharashtra, India",
			"India",
		},
		node2row: map[string]int{"n1": 0, "n2": 1, "n3": 2},
		nidIdx:   0,
		nameIdx:  1,
		cipIdx:   2,
	}
	mapCli := getMockGeocodesContainment()
	err := geocodePlaces(mapCli, tinfo)
	if err != nil {
		t.Errorf("geocodePlaces() failed with error %v", err)
	}
	expectedRows := [][]string{
		{"n1", "Mumbai", "n2", "ChIJwe1EZjDG5zsRaYxkjY_tpF0", ""},
		{"n2", "Maharashtra", "n3", "ChIJ-dacnB7EzzsRtk_gS5IiLxs", ""},
		{"n3", "India", "", "ChIJkbeSa_BfYzARphNChaFPjNc", ""},
	}
	for i, row := range tinfo.rows {
		if strings.Join(row, ",") != strings.Join(expectedRows[i], ",") {
			t.Errorf("row %d differs: got %v, want %v", i, row, expectedRows[i])
		}
	}
}

func TestMapPlaceIDsToDCIDs(t *testing.T) {
	tinfo := &tableInfo{
		rows: [][]string{
			{"n1", "Mumbai", "n2", "ChIJwe1EZjDG5zsRaYxkjY_tpF0", ""},
			{"n2", "Maharashtra", "n3", "ChIJ-dacnB7EzzsRtk_gS5IiLxs", ""},
			{"n3", "India", "", "ChIJkbeSa_BfYzARphNChaFPjNc", ""},
		},
	}
	rApi := &MockResolveApi{}
	err := mapPlaceIDsToDCIDs(rApi, tinfo)
	if err != nil {
		t.Errorf("mapPlaceIDsToDCIDs() failed with error %v", err)
	}
	expectedRows := [][]string{
		{"n1", "Mumbai", "n2", "wikidataId/Q1156", ""},
		{"n2", "Maharashtra", "n3", "", "Missing dcid for placeId ChIJ-dacnB7EzzsRtk_gS5IiLxs"},
		{"n3", "India", "", "country/IND", ""},
	}
	for i, row := range tinfo.rows {
		if strings.Join(row, ",") != strings.Join(expectedRows[i], ",") {
			t.Errorf("row %d differs: got %v, want %v", i, row, expectedRows[i])
		}
	}
}

func TestMain(t *testing.T) {
	table := []struct {
		in     string
		want   string
		got    string
		mapCli MapsClient
	}{
		{"input_basic.csv", "expected_output_basic.csv", "actual_output_basic.csv", getMockGeocodesBasic()},
		{"input_containment.csv", "expected_output_containment.csv", "actual_output_containment.csv", getMockGeocodesContainment()},
	}
	for _, t := range table {
		err := resolvePlacesByName("testdata/"+t.in, "testdata/"+t.got, false, &MockResolveApi{}, t.mapCli)
		if err != nil {
			log.Fatal(err)
		}
		want, err := ioutil.ReadFile("testdata/" + t.want)
		if err != nil {
			log.Fatal(err)
		}
		got, err := ioutil.ReadFile("testdata/" + t.got)
		if err != nil {
			log.Fatal(err)
		}
		if string(want) != string(got) {
			log.Fatalf("For input %s:: got: %s, want: %s", t.in, string(got), string(want))
		}
	}
}
