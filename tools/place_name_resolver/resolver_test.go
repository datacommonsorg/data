package main

import (
	"googlemaps.github.io/maps"
	"io/ioutil"
	"log"
	"testing"
)

type MockPlaceId2Dcid struct{}

func (m *MockPlaceId2Dcid) Read() ([]byte, error) {
	return ioutil.ReadFile("testdata/placeid2dcid.json")
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
		err := resolvePlacesByName("testdata/"+t.in, "testdata/"+t.got, &MockPlaceId2Dcid{}, t.mapCli)
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
