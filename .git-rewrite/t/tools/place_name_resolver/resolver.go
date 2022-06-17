package main

import (
	"cloud.google.com/go/storage"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"googlemaps.github.io/maps"
	"io"
	"io/ioutil"
	"log"
	"os"
	"sync"
)

var (
	inCsvPath = flag.String("in_csv_path", "", "Input CSV file. Column names are supposed to be Place properties or "+
		"literal 'Node' to represent a local ID. containedInPlace is always assumed to be a local reference.")
	outCsvPath = flag.String("out_csv_path", "", "Same as input with additional column for DCID.")
	mapsApiKey = flag.String("maps_api_key", "", "Key for accessing Geocoding Maps API.")
)

const (
	batchSize          = 200
	placeId2DcidBucket = "datcom-browser-prod.appspot.com"
	placeId2DcidObject = "placeid2dcid.json"
)

//
// PlaceId2Dcid Reader.
//
type PlaceId2Dcid interface {
	Read() ([]byte, error)
}

type RealPlaceId2Dcid struct{}

func (r *RealPlaceId2Dcid) Read() ([]byte, error) {
	ctx := context.Background()
	gcsCli, err := storage.NewClient(ctx)
	if err != nil {
		return nil, err
	}
	fp, err := gcsCli.Bucket(placeId2DcidBucket).Object(placeId2DcidObject).NewReader(ctx)
	if err != nil {
		return nil, err
	}
	defer fp.Close()
	return ioutil.ReadAll(fp)
}

//
// Maps API Client.
//
type MapsClient interface {
	Geocode(r *maps.GeocodingRequest) ([]maps.GeocodingResult, error)
}

type RealMapsClient struct {
	Client *maps.Client
}

func (r *RealMapsClient) Geocode(req *maps.GeocodingRequest) ([]maps.GeocodingResult, error) {
	return r.Client.Geocode(context.Background(), req)
}

//
// Data Structure representing the CSV.
//
type tableInfo struct {
	// CSV header.
	header []string

	// Ordered rows in CSV.
	rows [][]string

	// Expanded name used for geocoding, one per row.
	extNames []string

	// Map from node-id to row index.
	node2row map[string]int

	// Column index of 'Node'. -1 if missing.
	nidIdx  int
	// Column index of 'containedInPlace'. -1 if missing.
	cipIdx  int
	// Column index of 'name'. -1 if missing.
	nameIdx int
}

func appendContainedInPlaceNames(name string, row []string, tinfo *tableInfo) (string, error) {
	if tinfo.cipIdx < 0 {
		return name, nil
	}

	cipRef := row[tinfo.cipIdx]
	if cipRef == "" {
		return name, nil
	}

	nodeId := row[tinfo.nidIdx]
	if nodeId == cipRef {
		return name, nil
	}

	idx, ok := tinfo.node2row[cipRef]
	if !ok {
		log.Printf("ERROR: Unresolved 'containedInPlace' ref %s in Node %s, skipping.", cipRef, nodeId)
		return name, nil
	}
	if idx >= len(tinfo.rows) {
		log.Fatalf("Out of range %d vs. %d", idx, len(tinfo.rows))
		return "", fmt.Errorf("Out of range %d vs. %d", idx, len(tinfo.rows))
	}

	cipRow := tinfo.rows[idx]
	cipName := cipRow[tinfo.nameIdx]
	return appendContainedInPlaceNames(name+", "+cipName, cipRow, tinfo)
}

func buildTableInfo(inCsvPath string) (*tableInfo, error) {
	csvfile, err := os.Open(inCsvPath)
	if err != nil {
		return nil, err
	}
	r := csv.NewReader(csvfile)
	isHeader := true
	numCols := 0
	tinfo := &tableInfo{
		node2row: map[string]int{},
		nidIdx:   -1,
		nameIdx:  -1,
		cipIdx:   -1,
	}
	dataRowNum := 0
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if isHeader {
			numCols = len(row)
			for i, f := range row {
				switch f {
				case "name":
					tinfo.nameIdx = i
				case "containedInPlace":
					tinfo.cipIdx = i
				case "Node":
					tinfo.nidIdx = i
				}
			}
			tinfo.header = append(row, "dcid", "errors")

			// Validate.
			if tinfo.nameIdx < 0 {
				return nil, fmt.Errorf("CSV does not have a 'name' column!")
			}
			if tinfo.cipIdx >= 0 && tinfo.nidIdx < 0 {
				return nil, fmt.Errorf("When 'containedInPLace' is provided, 'Node' must be provided to allow for references!")
			}
			isHeader = false
			continue
		}
		if numCols != len(row) {
			return nil, fmt.Errorf("Not a rectangular CSV! Row %d has only %d columns!", dataRowNum+1, len(row))
		}
		if tinfo.nidIdx >= 0 && row[tinfo.nidIdx] != "" {
			tinfo.node2row[row[tinfo.nidIdx]] = dataRowNum
		}
		tinfo.rows = append(tinfo.rows, row)
		dataRowNum += 1
	}

	for _, row := range tinfo.rows {
		extName, err := appendContainedInPlaceNames(row[tinfo.nameIdx], row, tinfo)
		if err != nil {
			return nil, err
		}
		tinfo.extNames = append(tinfo.extNames, extName)
	}
	return tinfo, nil
}

func loadPlaceIdToDcidMap(p2d PlaceId2Dcid) (*map[string]string, error) {
	bytes, err := p2d.Read()
	if err != nil {
		return nil, err
	}
	placeId2Dcid := &map[string]string{}
	err = json.Unmarshal(bytes, &placeId2Dcid)
	if err != nil {
		return nil, err
	}
	return placeId2Dcid, nil
}

func geocodeOneRow(idx int, placeId2Dcid *map[string]string, tinfo *tableInfo, mapCli MapsClient, wg *sync.WaitGroup) {
	defer wg.Done()
	extName := tinfo.extNames[idx]
	req := &maps.GeocodingRequest{
		Address:  extName,
		Language: "en",
	}
	results, err := mapCli.Geocode(req)
	if err != nil {
		tinfo.rows[idx] = append(tinfo.rows[idx], "", fmt.Sprintf("Geocoding failure for %s: %v", extName, err))
		return
	}
	if len(results) == 0 {
		tinfo.rows[idx] = append(tinfo.rows[idx], "", fmt.Sprintf("Empty geocoding result for %s", extName))
		return
	}
	for _, result := range results {
		dcid, ok := (*placeId2Dcid)[result.PlaceID]
		if !ok {
			tinfo.rows[idx] = append(tinfo.rows[idx], "", fmt.Sprintf("Missing dcid for placeId %s", result.PlaceID))
		} else {
			// TODO: Deal with place-type checks and multiple results.
			tinfo.rows[idx] = append(tinfo.rows[idx], dcid, "")
		}
		break
	}
}

func geocodePlaces(mapCli MapsClient, placeId2Dcid *map[string]string, tinfo *tableInfo) error {
	for i := 0; i < len(tinfo.rows); i += batchSize {
		var wg sync.WaitGroup
		jMax := i + batchSize
		if jMax > len(tinfo.rows) {
			jMax = len(tinfo.rows)
		}
		for j := i; j < jMax; j++ {
			wg.Add(1)
			go geocodeOneRow(j, placeId2Dcid, tinfo, mapCli, &wg)
		}
		wg.Wait()
		log.Printf("Processed %d rows, %d left.", jMax, len(tinfo.rows)-jMax)
	}
	return nil
}

func writeOutput(outCsvPath string, tinfo *tableInfo) error {
	outFile, err := os.Create(outCsvPath)
	if err != nil {
		return err
	}
	w := csv.NewWriter(outFile)
	w.Write(tinfo.header)
	w.WriteAll(tinfo.rows)
	if err := w.Error(); err != nil {
		return err
	}
	return nil
}

func resolvePlacesByName(inCsvPath, outCsvPath string, p2d PlaceId2Dcid, mapCli MapsClient) error {
	tinfo, err := buildTableInfo(inCsvPath)
	if err != nil {
		return err
	}
	placeIdToDcid, err := loadPlaceIdToDcidMap(p2d)
	if err != nil {
		return err
	}
	err = geocodePlaces(mapCli, placeIdToDcid, tinfo)
	if err != nil {
		return err
	}
	return writeOutput(outCsvPath, tinfo)
}

func main() {
	flag.Parse()
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	mapCli, err := maps.NewClient(maps.WithAPIKey(*mapsApiKey))
	if err != nil {
		log.Fatalf("Maps API init failed: %v", err)
	}

	err = resolvePlacesByName(*inCsvPath, *outCsvPath, &RealPlaceId2Dcid{}, &RealMapsClient{Client: mapCli})
	if err != nil {
		log.Fatalf("resolvePlacesByName failed: %v", err)
	}
}
