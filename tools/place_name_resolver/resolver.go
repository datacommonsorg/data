package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"

	"googlemaps.github.io/maps"
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
	batchSize   = 50
	dcAPI       = "https://api.datacommons.org/v1/recon/resolve/id"
	dcBatchSize = 500
)

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

// PlaceId2Dcid Reader.
type ResolveApi interface {
	Resolve(req *resolveReq) (*resolveResp, error)
}

type RealResolveApi struct{}

func (r *RealResolveApi) Resolve(req *resolveReq) (*resolveResp, error) {
	jReq, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	jResp, err := http.Post(dcAPI, "application/json", bytes.NewBuffer(jReq))
	if err != nil {
		return nil, err
	}
	defer func() {
		err := jResp.Body.Close()
		if err != nil {
			log.Printf("ERROR: failed to close response body: %v", err)
		}
	}()
	jBytes, err := io.ReadAll(jResp.Body)
	if err != nil {
		return nil, err
	}
	var resp resolveResp
	err = json.Unmarshal(jBytes, &resp)
	if err != nil {
		return nil, err
	}
	return &resp, nil
}

// Maps API Client.
type MapsClient interface {
	Geocode(r *maps.GeocodingRequest) ([]maps.GeocodingResult, error)
}

type RealMapsClient struct {
	Client *maps.Client
}

func (r *RealMapsClient) Geocode(req *maps.GeocodingRequest) ([]maps.GeocodingResult, error) {
	return r.Client.Geocode(context.Background(), req)
}

// Data Structure representing the CSV.
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

func appendContainedInPlaceNames(row []string, tinfo *tableInfo) (string, error) {
	var parts []string
	currRow := row
	visitedNodes := make(map[string]bool)

	for {
		name := currRow[tinfo.nameIdx]
		parts = append(parts, name)

		if tinfo.cipIdx < 0 {
			break
		}

		cipRef := currRow[tinfo.cipIdx]
		if cipRef == "" {
			break
		}

		nodeId := currRow[tinfo.nidIdx]
		if nodeId != "" {
			if _, ok := visitedNodes[nodeId]; ok {
				return "", fmt.Errorf("circular dependency detected for node %s", nodeId)
			}
			visitedNodes[nodeId] = true
		}

		if nodeId == cipRef {
			break
		}

		idx, ok := tinfo.node2row[cipRef]
		if !ok {
			log.Printf("ERROR: Unresolved 'containedInPlace' ref %s in Node %s, skipping.", cipRef, nodeId)
			break
		}
		if idx >= len(tinfo.rows) {
			return "", fmt.Errorf("out of range %d vs. %d", idx, len(tinfo.rows))
		}

		currRow = tinfo.rows[idx]
	}

	return strings.Join(parts, ", "), nil
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
				return nil, fmt.Errorf("csv does not have a 'name' column")
			}
			if tinfo.cipIdx >= 0 && tinfo.nidIdx < 0 {
				return nil, fmt.Errorf("when 'containedInPlace' is provided, 'Node' must be provided to allow for references")
			}
			isHeader = false
			continue
		}
		if numCols != len(row) {
			return nil, fmt.Errorf("not a rectangular CSV! Row %d has only %d columns", dataRowNum+1, len(row))
		}
		if tinfo.nidIdx >= 0 && row[tinfo.nidIdx] != "" {
			tinfo.node2row[row[tinfo.nidIdx]] = dataRowNum
		}
		tinfo.rows = append(tinfo.rows, row)
		dataRowNum += 1
	}

	for _, row := range tinfo.rows {
		extName, err := appendContainedInPlaceNames(row, tinfo)
		if err != nil {
			return nil, err
		}
		tinfo.extNames = append(tinfo.extNames, extName)
	}
	return tinfo, nil
}

func geocodePlaces(mapCli MapsClient, tinfo *tableInfo) error {
	numRows := len(tinfo.rows)
	jobs := make(chan int, numRows)
	results := make(chan error, numRows)

	// Start workers
	numWorkers := batchSize
	for w := 0; w < numWorkers; w++ {
		go func(w int, jobs <-chan int, results chan<- error) {
			for j := range jobs {
				extName := tinfo.extNames[j]
				req := &maps.GeocodingRequest{
					Address:  extName,
					Language: "en",
				}
				resp, err := mapCli.Geocode(req)
				if err != nil {
					tinfo.rows[j] = append(tinfo.rows[j], "", fmt.Sprintf("Geocoding failure for %s: %v", extName, err))
					results <- nil
					continue
				}
				if len(resp) == 0 {
					tinfo.rows[j] = append(tinfo.rows[j], "", fmt.Sprintf("Empty geocoding result for %s", extName))
					results <- nil
					continue
				}
				// TODO: Deal with place-type checks and multiple results.
				for _, result := range resp[:1] {
					tinfo.rows[j] = append(tinfo.rows[j], result.PlaceID, "")
				}
				results <- nil
			}
		}(w, jobs, results)
	}

	// Add jobs
	for j := 0; j < numRows; j++ {
		jobs <- j
	}
	close(jobs)

	// Wait for all jobs to finish
	for i := 0; i < numRows; i++ {
		err := <-results
		if err != nil {
			return err
		}
		if (i+1)%batchSize == 0 {
			log.Printf("Processed %d rows, %d left.", i+1, numRows-(i+1))
		}
	}
	log.Printf("Processed all %d rows.", numRows)
	return nil
}

func mapPlaceIDsToDCIDs(rApi ResolveApi, tinfo *tableInfo) error {
	placeID2Idx := buildPlaceIDMap(tinfo)
	batches := createResolveBatches(placeID2Idx)

	resolvedPlaceIDs := make(map[string]string)
	for _, batch := range batches {
		req := &resolveReq{
			InProp:  "placeId",
			OutProp: "dcid",
			Ids:     batch,
		}
		resp, err := rApi.Resolve(req)
		if err != nil {
			return err
		}
		for _, ent := range resp.Entities {
			if len(ent.OutIds) > 0 {
				resolvedPlaceIDs[ent.InId] = ent.OutIds[0]
			}
		}
	}

	updateTableWithDCIDs(tinfo, placeID2Idx, resolvedPlaceIDs)
	return nil
}

func buildPlaceIDMap(tinfo *tableInfo) map[string][]int {
	placeID2Idx := make(map[string][]int)
	for i, r := range tinfo.rows {
		if len(r) < 2 {
			continue
		}
		placeID := r[len(r)-2]
		if placeID != "" {
			placeID2Idx[placeID] = append(placeID2Idx[placeID], i)
		}
	}
	return placeID2Idx
}

func createResolveBatches(placeID2Idx map[string][]int) [][]string {
	var batches [][]string
	var batch []string
	for placeID := range placeID2Idx {
		batch = append(batch, placeID)
		if len(batch) == dcBatchSize {
			batches = append(batches, batch)
			batch = nil
		}
	}
	if len(batch) > 0 {
		batches = append(batches, batch)
	}
	return batches
}

func updateTableWithDCIDs(tinfo *tableInfo, placeID2Idx map[string][]int, resolvedPlaceIDs map[string]string) {
	for placeID, indices := range placeID2Idx {
		dcid, ok := resolvedPlaceIDs[placeID]
		for _, idx := range indices {
			l := len(tinfo.rows[idx])
			if !ok {
				tinfo.rows[idx][l-2] = ""
				tinfo.rows[idx][l-1] = fmt.Sprintf("Missing dcid for placeId %s", placeID)
			} else if len(indices) > 1 {
				tinfo.rows[idx][l-2] = ""
				tinfo.rows[idx][l-1] = fmt.Sprintf("Duplicate dcid %s", dcid)
			} else {
				tinfo.rows[idx][l-2] = dcid
			}
		}
	}
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
