package sharding_writer

import (
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"path"
	"testing"
)

var (
	// tmpDir is picked at start time for tests done during this session.
	tmpDir string
)

func init() {
	var err error
	tmpDir, err = ioutil.TempDir("", "sharding_writer_test")
	if err != nil {
		log.Fatalf("unable to create temporary directory for tests")
	}
}

// makeFilename constructs a filename relative to the tmpDir for these tests.
func makeFilename(pieces ...string) string {
	return path.Join(append([]string{tmpDir}, pieces...)...)
}

const (
	// baseString is ranged over to get the desired length of data.
	// The string is 73 characters long so it should lead to non-identical
	// rows when repeated line after line.
	baseString = `abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWXYZ.`

	// TODO(roberts): Add in a test string that includes varying byte width
	// UTF-8 characters such as:
	//
	// 2 byte utf-8
	// U+00A2       ¢   // currency symbol
	//
	// 3 byte utf-8
	// U+20AC       €   // the Euro
	//
	// 4 byte utf-8
	// U+2070E	𠜎
	// U+20731	𠜱

	// sampleMCF is a simple string that will have the x replaced with a
	// counter when being generated as filler.
	// TODO(rsned): Uncomment when generateMCF is implemented.
	/*
			sampleMCF = `
		Node: dcid:UnitTest_Generated_Node_{x}_Entry
		name: "UnitTest_Generated_Node_{x}_Entry"
		typeOf: dcs:StatisticalVariable
		populationType: dcs:TotalPopulation
		measuredProperty: dcs:measuredProperty
		statType: dcs:measuredValue
		measurementMethod: dcs:UnitTestingGenerated
		unit: dcs:Percent
		`
	*/
)

// generateRawString generates a regular set of characters up to the given
// number, without newlines, whitespace, or punctuation.
func generateRawString(count int64) string {
	// short circuit requests for negative or 0.
	if count < 1 {
		return ""
	}

	var buf bytes.Buffer

	// If the num bytes is more than the length of the src string, range
	// until we have written enough whole strings.
	for i := int64(0); i < (count / int64(len(baseString))); i++ {
		n, err := buf.WriteString(baseString)
		if n != len(baseString) || err != nil {
			fmt.Printf("error writing to buffer, had %d, wrote %d, err: %v",
				len(baseString), n, err)
		}
	}

	// Write out the bytes less than a full line to get to the full amount.
	buf.WriteString(baseString[:count%int64(len(baseString))])

	return buf.String()
}

func TestGenerateRawString(t *testing.T) {
	tests := []struct {
		count int64
		want  string
	}{
		{count: -3, want: ""},
		{count: 0, want: ""},
		{count: 1, want: "a"},
		{count: 2, want: "ab"},
		{count: 73, want: baseString},
		{count: 74, want: baseString + baseString[0:1]},
		{count: 75, want: baseString + baseString[0:2]},
		{count: 80, want: baseString + baseString[0:7]},
		{count: 100, want: baseString + baseString[0:27]},
		{count: 150, want: baseString + baseString + baseString[0:4]},
	}

	for _, test := range tests {
		if got := generateRawString(test.count); got != test.want {
			t.Errorf("generateRawString(%d) = %q, want %q", test.count, got, test.want)
		}
	}
}

// generateLines generates the given number of lines of text as 61 or 47 character
// long lines in a regular fashion.
func generateLines(count int64) string {
	// short circuit requests for negative or 0.
	if count < 1 {
		return ""
	}

	var buf bytes.Buffer
	var start, end int64
	var lenBase = int64(len(baseString))

	for i := int64(0); i < count; i++ {
		// 61 char long
		if i%2 == 0 {
			end = start + 61
			// if we dont have to wrap, write it out and move on.
			if end < lenBase {

				buf.WriteString(baseString[start:end])
				buf.WriteString("\n")
				start = end
				continue
			}
			// We need to wrap. Write to the end of the string.
			buf.WriteString(baseString[start:])
			// Jump back to the start.
			start = 0
			// The end is the remainder from dividing by length.
			end = end % lenBase
			buf.WriteString(baseString[start:end])
			buf.WriteString("\n")
			start = end
			continue
		}

		// else 47 char long
		end = start + 47
		// if we dont have to wrap, write it out and move on.
		if end < lenBase {
			buf.WriteString(baseString[start:end])
			buf.WriteString("\n")
			start = end
			continue
		}
		// We need to wrap. Write to the end of the string.
		buf.WriteString(baseString[start:])
		// Jump back to the start.
		start = 0
		// The end is the remainder from dividing by length.
		end = end % lenBase
		buf.WriteString(baseString[start:end])
		buf.WriteString("\n")
		start = end
		continue

	}
	return buf.String()
}

func TestGenerateLines(t *testing.T) {
	tests := []struct {
		count int64
		want  string
	}{
		{count: -7, want: ""},
		{count: 0, want: ""},
		{
			count: 1,
			want:  "abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOP\n",
		},
		{
			count: 2,
			want: `abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOP
Q;RSTUVWXYZ.abcdef_ghijkl,mnopqr?stuvwx+yz0123-
`,
		},
		{
			count: 3,
			want: `abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOP
Q;RSTUVWXYZ.abcdef_ghijkl,mnopqr?stuvwx+yz0123-
456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWXYZ.abcdef_ghijkl,mnopqr?st
`,
		},
		{
			count: 4,
			want: `abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOP
Q;RSTUVWXYZ.abcdef_ghijkl,mnopqr?stuvwx+yz0123-
456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWXYZ.abcdef_ghijkl,mnopqr?st
uvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWX
`,
		},
		{
			count: 5,
			want: `abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOP
Q;RSTUVWXYZ.abcdef_ghijkl,mnopqr?stuvwx+yz0123-
456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWXYZ.abcdef_ghijkl,mnopqr?st
uvwx+yz0123-456789*0ABCDE/FGHIJK:LMNOPQ;RSTUVWX
YZ.abcdef_ghijkl,mnopqr?stuvwx+yz0123-456789*0ABCDE/FGHIJK:LM
`,
		},
	}

	for _, test := range tests {
		if got := generateLines(test.count); got != test.want {
			t.Errorf("generateLines(%d) = %q, want %q", test.count, got, test.want)
		}
	}
}

// generateMCF generates a series of MCF definitions with a blank line separator
// between each entry.
func generateMCF(count int64) string {
	// short circuit requests for negative or 0.
	if count < 1 {
		return ""
	}

	var buf bytes.Buffer

	// TODO: generate the MCF

	return buf.String()
}

func TestGenerateMCF(t *testing.T) {
	tests := []struct {
		count int64
		want  string
	}{
		{count: -1, want: ""},
		{count: 0, want: ""},
	}

	for _, test := range tests {
		if got := generateMCF(test.count); got != test.want {
			t.Errorf("generateMCF(%d) = %q, want %q", test.count, got, test.want)
		}
	}
}

// setup does the creation work for a given test, creating the path it
// will use for its tests.
func setup(testPath string) {
	if err := os.Mkdir(makeFilename(testPath), os.ModeDir|0750); err != nil {
		log.Fatalf("unable to create working dir for test %q: %v", testPath, err)
	}
}

// tearDown cleans up the generated files for the given test.
func tearDown(testPath string) {
	if err := os.RemoveAll(makeFilename(testPath)); err != nil {
		fmt.Printf("unable to clean up for test path %q", testPath)
	}
}

func checkExpectedNumShards(t *testing.T, testPath string, numExpected int) {
	dir, err := os.Open(makeFilename(testPath))
	if err != nil {
		t.Errorf("unable to open directory to check shards: %v", err)
		return
	}

	fileInfos, err := dir.Readdir(-1)
	if err != nil {
		t.Errorf("unable to read directory: %v", err)
		return
	}

	if len(fileInfos) != numExpected {
		t.Errorf("num shards = %v, want %v", len(fileInfos), numExpected)
	}
}

func checkFilesSumToInputSize(t *testing.T, testPath string, wantSize int64) {
	dir, err := os.Open(makeFilename(testPath))
	if err != nil {
		t.Errorf("unable to open directory to check shards: %v", err)
		return
	}

	fileInfos, err := dir.Readdir(-1)
	if err != nil {
		t.Errorf("unable to read directory: %v", err)
		return
	}

	var sumSize int64
	for _, fi := range fileInfos {
		sumSize += fi.Size()
	}

	if sumSize != wantSize {
		t.Errorf("sum of file sizes = %d, want %d", sumSize, wantSize)
	}
}

func cmpBytes(t *testing.T, label string, a, b []byte) {
	if len(a) != len(b) {
		t.Errorf("bytes not the same length: %v != %v", len(a), len(b))
	}

	for i, val := range a {
		if b[i] != val {
			t.Errorf("%s: slices differ starting at element %d: 0x%x (%s) vs 0x%x (%s)",
				label, i, val, string(val), b[i], string(b[i]))
			return
		}
	}
}

// checkFileBeginEndContents checks that a file begins and ends with the expected values.
func checkFileBeginEndContents(t *testing.T, testPath, filename string, begins, ends []byte) {
	fn := makeFilename(testPath, filename)
	contents, err := ioutil.ReadFile(fn)
	if err != nil {
		t.Errorf("error reading %q for content checks: %v", fn, err)
	}

	if len(contents) < len(begins) {
		t.Errorf("file %q to short to compare with starting bytes %v", fn, begins)
	}
	if len(contents) < len(ends) {
		t.Errorf("file %q to short to compare with ending bytes %v", fn, begins)
	}

	cmpBytes(t, fn, contents[0:len(begins)], begins)
	cmpBytes(t, fn, contents[len(contents)-len(ends):], ends)
}

func TestWriter(t *testing.T) {
	tests := []struct {
		label string   // descriptive label of this case
		path  string   // directory name piece to distinguish test data
		opts  []Option // selection of opts to set.
		count int64    // how many we want to generate

		// what generator to use. Note this can be different
		// than what the writer is configured to use to test poor choices.
		dataType dataType

		wantNumShards int

		// Check the first and last bytes/chars of the first shard.
		wantFirstShardBegin string
		wantFirstShardEnd   string

		// Check the first and last bytes/chars of the last shard.
		// Note that these are only checked if there is more than one shard.
		wantLastShardBegin string
		wantLastShardEnd   string
	}{
		{
			label:               "Write 1 byte to default shard, default opts, raw data",
			path:                "1_byte_to_default_shard_all_defaults",
			count:               1,
			dataType:            dataTypeRaw,
			wantNumShards:       1,
			wantFirstShardBegin: "a",
			wantFirstShardEnd:   "a",
		},
		{
			label: "Write 1 byte to 1 shard, raw data",
			path:  "1_byte_to_1_byte_shard_raw",
			opts: []Option{
				RawDataType(),
				ShardSize(1),
			},
			dataType:          dataTypeRaw,
			count:             1,
			wantNumShards:     1,
			wantFirstShardEnd: "a",
		},
		{
			label: "Write 256 bytes to 1 shard, raw data",
			path:  "256_bytes_to_100mb_shard_raw",
			opts: []Option{
				RawDataType(),
			},
			count:               256,
			dataType:            dataTypeRaw,
			wantNumShards:       1,
			wantFirstShardBegin: "abcdef_g",
			wantFirstShardEnd:   "z0123-45",
		},
		{
			label: "Write 256 bytes to 32-byte shards, raw data",
			path:  "256_bytes_to_32_byte_shards_raw",
			opts: []Option{
				RawDataType(),
				ShardSize(32),
			},
			count:               256,
			dataType:            dataTypeRaw,
			wantNumShards:       8,
			wantFirstShardBegin: "abcdef_g",
			wantFirstShardEnd:   "vwx+yz01",
			wantLastShardBegin:  "f_ghijkl",
			wantLastShardEnd:    "z0123-45",
		},
		{
			label: "Write 257 bytes to 11-byte shards, raw data",
			path:  "257_bytes_to_11_byte_shards_raw",
			opts: []Option{
				RawDataType(),
				ShardSize(11),
			},
			count:               257,
			dataType:            dataTypeRaw,
			wantNumShards:       24,
			wantFirstShardBegin: "abcdef_g",
			wantFirstShardEnd:   "def_ghij",
			wantLastShardBegin:  "-456",
			wantLastShardEnd:    "-456",
		},

		// TODO(rsned): Add tests for text based and MCF based data
		// as those methods get implemented.
	}

	for _, test := range tests {
		setup(test.path)
		// Create a sharded writer with the options in the test case.
		w := NewWriter(makeFilename(test.path, "sharded_data"), "dat",
			test.opts...)

		// Generate data to be written out.
		var data string
		switch test.dataType {
		case dataTypeRaw:
			data = generateRawString(test.count)
		case dataTypeText:
			data = generateLines(test.count)
		case dataTypeMCF:
			data = generateMCF(test.count)
		}

		// io.WriterString calls an io.Writer's WriteString if the Writer
		// also implements StringWriter, which we do.
		n, err := io.WriteString(w, data)
		if err != nil {
			t.Errorf("error writing to the sharding writer: %v", err)
			// move on to next case since the remaining checks wont work
			continue
		}
		if n != len(data) {
			t.Errorf("num bytes written doesn't match the input. wrote %d, had %d",
				n, len(data))
			// move on to next case since the remaining checks wont work
			continue
		}

		// Close the writer to ensure it's all saved.
		w.Close()

		// Now perform the various checks of the outputs.
		checkExpectedNumShards(t, test.path, test.wantNumShards)

		checkFilesSumToInputSize(t, test.path, int64(len(data)))

		firstFile := "sharded_data_0.dat"
		checkFileBeginEndContents(t, test.path, firstFile,
			[]byte(test.wantFirstShardBegin),
			[]byte(test.wantFirstShardEnd))

		if test.wantNumShards > 1 {
			lastFile := fmt.Sprintf("sharded_data_%d.dat", test.wantNumShards-1)
			checkFileBeginEndContents(t, test.path, lastFile,
				[]byte(test.wantLastShardBegin),
				[]byte(test.wantLastShardEnd))

		}
		// If you want to debug output or leave the results on disk,
		// comment out the tearDown call which removes this tests data.
		tearDown(test.path)
	}
}
