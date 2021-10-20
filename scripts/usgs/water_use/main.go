package main

import (
	"bufio"
	"encoding/csv"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

var (
	inputDir = flag.String(
		"input_dir",
		"/usr/local/google/home/wsws/Data/water",
		"Directory that contains input data files.")
	outputDir = flag.String(
		"output_dir",
		"/usr/local/google/home/wsws/Data/output",
		"Output directory.")
)

type varInfo struct {
	name string
	// If -1, it means that the column doesn't exist, we treat it as missing value.
	colIdx int
}

var (
	waterUseCategories = []string{
		"PublicSupply",
		"Domestic",
		"Industrial",
		"Irrigation",
		"Thermoelectric",
		"Mining",
		"Livestock",
		"Aquaculture",
	}
	waterTypes = []string{
		"FreshWater",
		"SalineWater",
	}
	waterSourceTypes = []string{
		"GroundWater",
		"SurfaceWater",
	}
	totalWithdrawalRateComponents = map[string]struct{}{
		"WithdrawalRate_Water_PublicSupply":   {},
		"WithdrawalRate_Water_Domestic":       {},
		"WithdrawalRate_Water_Industrial":     {},
		"WithdrawalRate_Water_Irrigation":     {},
		"WithdrawalRate_Water_Thermoelectric": {},
		"WithdrawalRate_Water_Mining":         {},
		"WithdrawalRate_Water_Livestock":      {},
		"WithdrawalRate_Water_Aquaculture":    {},
	}
	// The last one will be the total (WithdrawalRate_Water), and is handled in the processing code.
	varInfoList = []*varInfo{
		// Take WithdrawalRate_Water_PublicSupply_FreshWater, for data completeness.
		{"WithdrawalRate_Water_PublicSupply", 15},
		{"WithdrawalRate_Water_PublicSupply_GroundWater", 11},
		{"WithdrawalRate_Water_PublicSupply_SurfaceWater", 14},
		{"WithdrawalRate_Water_PublicSupply_FreshWater", 15},
		{"WithdrawalRate_Water_PublicSupply_FreshWater_GroundWater", 9},
		{"WithdrawalRate_Water_PublicSupply_FreshWater_SurfaceWater", 12},
		{"WithdrawalRate_Water_PublicSupply_SalineWater", 16},
		{"WithdrawalRate_Water_PublicSupply_SalineWater_GroundWater", 10},
		{"WithdrawalRate_Water_PublicSupply_SalineWater_SurfaceWater", 13},
		// Take WithdrawalRate_Water_Domestic_FreshWater, for data completeness.
		{"WithdrawalRate_Water_Domestic", 33},
		{"WithdrawalRate_Water_Domestic_GroundWater", 29},
		{"WithdrawalRate_Water_Domestic_SurfaceWater", 32},
		{"WithdrawalRate_Water_Domestic_FreshWater", 33},
		{"WithdrawalRate_Water_Domestic_FreshWater_GroundWater", 27},
		{"WithdrawalRate_Water_Domestic_FreshWater_SurfaceWater", 30},
		{"WithdrawalRate_Water_Domestic_SalineWater", 36},
		{"WithdrawalRate_Water_Domestic_SalineWater_GroundWater", 28},
		{"WithdrawalRate_Water_Domestic_SalineWater_SurfaceWater", 31},
		{"WithdrawalRate_Water_Industrial", 68},
		{"WithdrawalRate_Water_Industrial_GroundWater", 62},
		{"WithdrawalRate_Water_Industrial_SurfaceWater", 65},
		{"WithdrawalRate_Water_Industrial_FreshWater", 66},
		{"WithdrawalRate_Water_Industrial_FreshWater_GroundWater", 60},
		{"WithdrawalRate_Water_Industrial_FreshWater_SurfaceWater", 63},
		{"WithdrawalRate_Water_Industrial_SalineWater", 67},
		{"WithdrawalRate_Water_Industrial_SalineWater_GroundWater", 61},
		{"WithdrawalRate_Water_Industrial_SalineWater_SurfaceWater", 64},
		// Take WithdrawalRate_Water_Irrigation_FreshWater, for data completeness.
		{"WithdrawalRate_Water_Irrigation", 237},
		{"WithdrawalRate_Water_Irrigation_GroundWater", 232},
		{"WithdrawalRate_Water_Irrigation_SurfaceWater", 236},
		{"WithdrawalRate_Water_Irrigation_FreshWater", 237},
		{"WithdrawalRate_Water_Irrigation_FreshWater_GroundWater", 230},
		{"WithdrawalRate_Water_Irrigation_FreshWater_SurfaceWater", 233},
		{"WithdrawalRate_Water_Irrigation_SalineWater", 238},
		{"WithdrawalRate_Water_Irrigation_SalineWater_GroundWater", 231},
		{"WithdrawalRate_Water_Irrigation_SalineWater_SurfaceWater", 235},
		{"WithdrawalRate_Water_Thermoelectric", 84},
		{"WithdrawalRate_Water_Thermoelectric_GroundWater", 78},
		{"WithdrawalRate_Water_Thermoelectric_SurfaceWater", 81},
		{"WithdrawalRate_Water_Thermoelectric_FreshWater", 82},
		{"WithdrawalRate_Water_Thermoelectric_FreshWater_GroundWater", 76},
		{"WithdrawalRate_Water_Thermoelectric_FreshWater_SurfaceWater", 79},
		{"WithdrawalRate_Water_Thermoelectric_SalineWater", 83},
		{"WithdrawalRate_Water_Thermoelectric_SalineWater_GroundWater", 77},
		{"WithdrawalRate_Water_Thermoelectric_SalineWater_SurfaceWater", 80},
		{"WithdrawalRate_Water_Mining", 185},
		{"WithdrawalRate_Water_Mining_GroundWater", 179},
		{"WithdrawalRate_Water_Mining_SurfaceWater", 182},
		{"WithdrawalRate_Water_Mining_FreshWater", 183},
		{"WithdrawalRate_Water_Mining_FreshWater_GroundWater", 177},
		{"WithdrawalRate_Water_Mining_FreshWater_SurfaceWater", 180},
		{"WithdrawalRate_Water_Mining_SalineWater", 184},
		{"WithdrawalRate_Water_Mining_SalineWater_GroundWater", 178},
		{"WithdrawalRate_Water_Mining_SalineWater_SurfaceWater", 181},
		// Take WithdrawalRate_Water_Livestock_FreshWater, for data completeness.
		{"WithdrawalRate_Water_Livestock", 192},
		// Take WithdrawalRate_Water_Livestock_FreshWater_GroundWater, for data completeness.
		{"WithdrawalRate_Water_Livestock_GroundWater", 190},
		// Take WithdrawalRate_Water_Livestock_FreshWater_SurfaceWater, for data completeness.
		{"WithdrawalRate_Water_Livestock_SurfaceWater", 191},
		{"WithdrawalRate_Water_Livestock_FreshWater", 192},
		{"WithdrawalRate_Water_Livestock_FreshWater_GroundWater", 190},
		{"WithdrawalRate_Water_Livestock_FreshWater_SurfaceWater", 191},
		{"WithdrawalRate_Water_Livestock_SalineWater", -1},
		{"WithdrawalRate_Water_Livestock_SalineWater_GroundWater", -1},
		{"WithdrawalRate_Water_Livestock_SalineWater_SurfaceWater", -1},
		// Use WithdrawalRate_Water_Aquaculture_FreshWater, for data completeness.
		{"WithdrawalRate_Water_Aquaculture", 224},
		{"WithdrawalRate_Water_Aquaculture_GroundWater", 220},
		{"WithdrawalRate_Water_Aquaculture_SurfaceWater", 223},
		{"WithdrawalRate_Water_Aquaculture_FreshWater", 224},
		{"WithdrawalRate_Water_Aquaculture_FreshWater_GroundWater", 218},
		{"WithdrawalRate_Water_Aquaculture_FreshWater_SurfaceWater", 221},
		{"WithdrawalRate_Water_Aquaculture_SalineWater", 225},
		{"WithdrawalRate_Water_Aquaculture_SalineWater_GroundWater", 219},
		{"WithdrawalRate_Water_Aquaculture_SalineWater_SurfaceWater", 222},
	}
)

// In addition to the comment lines starting with "#", we need to skip 4 additional lines:
// 1. "Content-type: text/plain"
// 2. Empty row.
// 3. The header.
// 4. Cell length info.
func formatFile(filePath string) (*strings.Reader, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var content strings.Builder
	numSkippedLines := 0

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()

		// Skip comment lines.
		if strings.HasPrefix(line, "#") {
			continue
		}

		// Skip 4 non-data lines.
		if numSkippedLines < 4 {
			numSkippedLines++
			continue
		}

		content.WriteString(line + "\n")
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return strings.NewReader(content.String()), nil
}

// Format: geoId/XX.
func formatState(stateCode string) (string, error) {
	l := len(stateCode)
	if l == 2 {
		return "geoId/" + stateCode, nil
	}
	if l == 1 {
		return "geoId/0" + stateCode, nil
	}
	return "", fmt.Errorf("wrong stateCode: %s", stateCode)
}

// Format: geoId/XXYYY, where XX is the formatted stateCode.
func formatCounty(stateDCID, countyCode string) (string, error) {
	if len(stateDCID) != 8 {
		return "", fmt.Errorf("wrong stateDCID: %s", stateDCID)
	}
	l := len(countyCode)
	if l == 3 {
		return stateDCID + countyCode, nil
	}
	if l == 2 {
		return stateDCID + "0" + countyCode, nil
	}
	if l == 1 {
		return stateDCID + "00" + countyCode, nil
	}
	return "", fmt.Errorf("wrong countyCode: %s", countyCode)
}

func totalWithdrawalRateComponentIndices() map[int]struct{} {
	res := map[int]struct{}{}
	for _, varInfo := range varInfoList {
		if _, ok := totalWithdrawalRateComponents[varInfo.name]; ok {
			res[varInfo.colIdx] = struct{}{}
		}
	}
	return res
}

func csvHeader() []string {
	header := []string{"year", "dcid"}
	for _, varInfo := range varInfoList {
		header = append(header, varInfo.name)
	}
	header = append(header, "WithdrawalRate_Water")
	return header
}

func float64ListToStrList(list []float64) []string {
	res := []string{}
	for _, v := range list {
		if v == -1 {
			res = append(res, "")
		} else {
			res = append(res, strconv.FormatFloat(v, 'f', -1, 64))
		}
	}
	return res
}

func writeCSV(outputDir string, store map[string]map[string][]float64) error {
	fCSV, err := os.Create(filepath.Join(outputDir, "water.csv"))
	if err != nil {
		return err
	}
	defer fCSV.Close()

	csvWriter := csv.NewWriter(fCSV)
	defer csvWriter.Flush()

	if err := csvWriter.Write(csvHeader()); err != nil {
		return err
	}

	// Sort map keys to make the output more readable
	years := []string{}
	for year := range store {
		years = append(years, year)
	}
	sort.Strings(years)

	for _, year := range years {
		// Sort map keys to make the output more readable
		dcids := []string{}
		for dcid := range store[year] {
			dcids = append(dcids, dcid)
		}
		sort.Strings(dcids)

		for _, dcid := range dcids {
			row := []string{year, dcid}
			row = append(row, float64ListToStrList(store[year][dcid])...)
			if err := csvWriter.Write(row); err != nil {
				return err
			}
		}
	}

	return nil
}

func processData(inputDir, outputDir string) error {
	// Map: year => place DCID => [varValues].
	store := map[string]map[string][]float64{}

	totalWithdrawalIndices := totalWithdrawalRateComponentIndices()

	files, err := ioutil.ReadDir(inputDir)
	if err != nil {
		return fmt.Errorf("ioutil.ReadDir() = %s", err)
	}
	for _, f := range files {
		fmt.Printf("Reading %s\n", f.Name())

		fileReader, err := formatFile(filepath.Join(inputDir, f.Name()))
		if err != nil {
			return fmt.Errorf("formatFile(%s) = %s", f.Name(), err)
		}

		reader := csv.NewReader(fileReader)
		reader.Comma = '\t'
		rows, err := reader.ReadAll()
		for _, row := range rows {
			// Basic check for the row size.
			if len(row) != 283 {
				return fmt.Errorf("Wrong row size:\n%v\n", row)
			}

			// Location & time.
			state, err := formatState(row[0])
			if err != nil {
				return err
			}
			county, err := formatCounty(state, row[2])
			if err != nil {
				return err
			}
			year := row[4]
			if len(year) != 4 {
				return fmt.Errorf("wrong year: %s", year)
			}

			// Set up the store map for county.
			if _, ok := store[year]; !ok {
				store[year] = map[string][]float64{}
			}
			store[year][county] = []float64{}

			// Fill the store for county data.
			totalValue := 0.0
			for _, varInfo := range varInfoList {
				value := -1.0 // -1 means missing value.
				idx := varInfo.colIdx

				if idx != -1 { // Not missing column.
					if strValue := row[idx]; strValue != "-" { // Not missing value.
						value, err = strconv.ParseFloat(strValue, 64 /* bit */)
						if err != nil {
							return err
						}

						// For total withdrawal.
						if _, ok := totalWithdrawalIndices[idx]; ok {
							totalValue += value
						}
					}
				}

				store[year][county] = append(store[year][county], value)
			}
			store[year][county] = append(store[year][county], totalValue)
		}
	}

	// Map: year => place DCID => [varValues].
	aggStore := map[string]map[string][]float64{}

	// Aggregate for state and country data.
	usa := "country/USA"
	for year, yearStore := range store {
		aggStore[year] = map[string][]float64{}
		aggStore[year][usa] = make([]float64, len(varInfoList)+1)

		for county, values := range yearStore {
			if len(county) <= 8 {
				return fmt.Errorf("wrong county: %s", county)
			}

			state := county[:8]
			if _, ok := aggStore[year][state]; !ok {
				aggStore[year][state] = make([]float64, len(varInfoList)+1)
			}
			for idx, value := range values {
				if value == -1 { // Missing value.
					continue
				}
				aggStore[year][usa][idx] += value
				aggStore[year][state][idx] += value
			}
		}
	}
	for year, yearAggStore := range aggStore {
		for dcid, values := range yearAggStore {
			store[year][dcid] = values
		}
	}

	// Write to CSV.
	if err := writeCSV(outputDir, store); err != nil {
		return err
	}

	return nil
}

func generateStatVars(outputDir string) error {
	var res strings.Builder

	// Water Withdraw.
	idBase := "Node: dcid:WithdrawalRate_Water"
	nodeBase := "typeOf: dcs:StatisticalVariable\n"
	nodeBase += "populationType: dcs:Water\n"
	nodeBase += "measuredProperty: dcs:withdrawalRate\n"
	nodeBase += "statType: dcs:measuredValue\n"
	res.WriteString(fmt.Sprintf("%s\n%s\n", idBase, nodeBase))
	for _, c := range waterUseCategories {
		node1 := nodeBase + fmt.Sprintf("usedFor: dcs:%s\n", c)
		id1 := fmt.Sprintf("%s_%s", idBase, c)
		res.WriteString(fmt.Sprintf("%s\n%s\n", id1, node1))
		for _, s := range waterSourceTypes {
			node2 := node1 + fmt.Sprintf("waterSource: dcs:%s\n", s)
			id2 := fmt.Sprintf("%s_%s", id1, s)
			res.WriteString(fmt.Sprintf("%s\n%s\n", id2, node2))
		}
		for _, t := range waterTypes {
			node2 := node1 + fmt.Sprintf("waterType: dcs:%s\n", t)
			id2 := fmt.Sprintf("%s_%s", id1, t)
			res.WriteString(fmt.Sprintf("%s\n%s\n", id2, node2))

			for _, s := range waterSourceTypes {
				node3 := node2 + fmt.Sprintf("waterSource: dcs:%s\n", s)
				id3 := fmt.Sprintf("%s_%s", id2, s)
				res.WriteString(fmt.Sprintf("%s\n%s\n", id3, node3))
			}
		}
	}

	// Water Use.
	// TODO(spaceenter): It seems like categories other than 'domestic' also need water use.
	// However, the data is very incomplete, so we need to decide what to do for water use.

	// Output.
	f, err := os.Create(filepath.Join(outputDir, "water.mcf"))
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(res.String())
	return err
}

func generateTMCF(outputDir string) error {
	var res strings.Builder

	idBase := "Node: E:water->E"
	nodeBase := "typeOf: dcs:StatVarObservation\n"
	nodeBase += "observationDate: C:water->year\n"
	nodeBase += "observationAbout: C:water->dcid\n"
	nodeBase += "observationPeriod: \"P1Y\"\n"

	writeNode := func(entityIndex int, statVarName string) {
		id := idBase + strconv.Itoa(entityIndex)
		node := nodeBase + fmt.Sprintf("variableMeasured: dcid:%s\n", statVarName)
		node += fmt.Sprintf("value: C:water->%s\n", statVarName)
		res.WriteString(fmt.Sprintf("%s\n%s\n", id, node))
	}

	entityIndex := 0
	writeNode(entityIndex, "WithdrawalRate_Water")
	for _, varInfo := range varInfoList {
		entityIndex++
		writeNode(entityIndex, varInfo.name)
	}

	// Output.
	f, err := os.Create(filepath.Join(outputDir, "water.tmcf"))
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(res.String())
	return err
}

func main() {
	if err := generateStatVars(*outputDir); err != nil {
		log.Fatalf("generateStatVars() = %s", err)
	}
	if err := generateTMCF(*outputDir); err != nil {
		log.Fatalf("generateTMCF() = %s", err)
	}
	if err := processData(*inputDir, *outputDir); err != nil {
		log.Fatalf("processData() = %s", err)
	}
}
