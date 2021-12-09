package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"googlemaps.github.io/maps"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

var (
	inCsvPath = flag.String("in_csv_path", "", "Input CSV file. Column names are supposed to be Place properties or "+
		"literal 'Node' to represent a local ID. containedInPlace is always assumed to be a local reference.")
	outCsvPath      = flag.String("out_csv_path", "", "Same as input with additional column for DCID.")
	mapsApiKey      = flag.String("maps_api_key", "", "Key for accessing Geocoding Maps API.")
	generatePlaceID = flag.Bool("generate_place_id", false, "If set, placeID is generated in output CSV instead of DCID.")
)

const (
	// Query limit: 50 qps
	batchSize = 50
	// TODO: Switch to prod
	dcAPI = "https://autopush.recon.datacommons.org/id/resolve"
)

//
// PlaceId2Dcid Reader.
//
type ResolveApi interface {
	Resolve(req *resolveReq) (*resolveResp, error)
}

type RealResolveApi struct{}

func (r *RealResolveApi) Resolve(req *resolveReq) (*resolveResp, error) {
	jReq, err := json.Marshal(req)
	jResp, err := http.Post(dcAPI, "application/json", bytes.NewBuffer(jReq))
	if err != nil {
		return nil, err
	}
	defer jResp.Body.Close()
	jBytes, err := ioutil.ReadAll(jResp.Body)
	if err != nil {
		return nil, err
	}

	var resp resolveResp
	err = json.Unmarshal(jBytes, &resp)
	return &resp, nil
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
	nidIdx int
	// Column index of 'containedInPlace'. -1 if missing.
	cipIdx int
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

func geocodeOneRow(idx int, tinfo *tableInfo, mapCli MapsClient, wg *sync.WaitGroup) {
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
	// TODO: Deal with place-type checks and multiple results.
	for _, result := range results[:1] {
		tinfo.rows[idx] = append(tinfo.rows[idx], result.PlaceID, "")
	}
}

type resolveReq struct {
	InProp  string   `json:"inProp"`
	OutProp string   `json:"outProp"`
	Ids     []string `json:"ids"`
}

type resolveRespEntity struct {
	InId   string   `json:"inId"`
	OutIds []string `json:"outIds"`
}

type resolveResp struct {
	Entities []resolveRespEntity `json:"entities"`
}

func geocodePlaces(mapCli MapsClient, tinfo *tableInfo) error {
	for i := 0; i < len(tinfo.rows); i += batchSize {
		var wg sync.WaitGroup
		jMax := i + batchSize
		if jMax > len(tinfo.rows) {
			jMax = len(tinfo.rows)
		}
		for j := i; j < jMax; j++ {
			wg.Add(1)
			go geocodeOneRow(j, tinfo, mapCli, &wg)
		}
		wg.Wait()
		// Make sure we are under the 50 QPS limit set by Google Maps API.
		time.Sleep(1 * time.Second)
		log.Printf("Processed %d rows, %d left.", jMax, len(tinfo.rows)-jMax)
	}
	return nil
}

func mapPlaceIDsToDCIDs(rApi ResolveApi, tinfo *tableInfo) error {
	// Collect all place IDs and build the REST API call.
	placeID2Idx := map[string]int{}
	req := &resolveReq{
		InProp:  "placeId",
		OutProp: "dcid",
	}
	for i, r := range tinfo.rows {
		if len(r) < 2 {
			continue
		}
		placeID := r[len(r)-2]
		placeID2Idx[placeID] = i
		req.Ids = append(req.Ids, placeID)
	}

	resp, err := rApi.Resolve(req)
	if err != nil {
		return err
	}

	// Replace all resolved placeIDs with DCIDs
	for _, ent := range resp.Entities {
		idx := placeID2Idx[ent.InId]
		tinfo.rows[idx][len(tinfo.rows[idx])-2] = ent.OutIds[0]
		placeID2Idx[ent.InId] = -1
	}
	for placeID, idx := range placeID2Idx {
		if idx == -1 {
			// Resolved entry
			continue
		}
		// Set error.
		l := len(tinfo.rows[idx])
		tinfo.rows[idx][l-2] = ""
		tinfo.rows[idx][l-1] = fmt.Sprintf("Missing dcid for placeId %s", placeID)
	}
	return nil
}

func writeOutput(outCsvPath string, tinfo *tableInfo) error {
	outFile, err := os.Create(outCsvPath)
	if err != nil {
		return err
	}
	w := csv.NewWriter(outFile)
	if err := w.Write(tinfo.header); err != nil {
		return err
	}
	if err := w.WriteAll(tinfo.rows); err != nil {
		return err
	}
	if err := w.Error(); err != nil {
		return err
	}
	return nil
}

func resolvePlacesByName(inCsvPath, outCsvPath string, generatePlaceID bool, rApi ResolveApi, mapCli MapsClient) error {
	tinfo, err := buildTableInfo(inCsvPath)
	if err != nil {
		return err
	}
	err = geocodePlaces(mapCli, tinfo)
	if err != nil {
		return err
	}
	if !generatePlaceID {
		err = mapPlaceIDsToDCIDs(rApi, tinfo)
		if err != nil {
			return err
		}
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

	err = resolvePlacesByName(*inCsvPath, *outCsvPath, *generatePlaceID, &RealResolveApi{}, &RealMapsClient{Client: mapCli})
	if err != nil {
		log.Fatalf("resolvePlacesByName failed: %v", err)
	}
}
