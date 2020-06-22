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

package sharding_writer

import (
	"fmt"
	"io"
	"log"
	"os"
	"strings"
)

const (
	// DefaultShardSize is 100 MB.
	DefaultShardSize = 100 * 1024 * 1024
)

// option is an interface for any type of behavior we want to configure on the
// Writer. The interface methods are private because we do not support options
// implemented outside this package.
type Option interface {
	set(*Options)
}

// Options is the set of options for the writer. The type is opaque to allow
// for future additions and subtractions of supported features.
type Options struct {
	shardSize int64

	dataType dataType
}

// shardSize is a byte count to split on.
// TODO(rsned): What do we do is someone wants shard larger the 4GB?
type shardSize int64

// ShardSize returns an option that sets the desired shard size in bytes.
func ShardSize(numBytes int64) Option { return shardSize(numBytes) }

func (x shardSize) set(opts *Options) {
	opts.shardSize = int64(x)
}

// dataType is an enum of the different types of writing behavior based
// on the data expected to be writen.
type dataType int

const (
	// dataTypeRaw is for plain bytes, no smarts, just split on exact byte count.
	//
	// TODO(rsned): Is raw the clearest name for this? Maybe dataTypeBytes?
	// This is just the basic write whatever comes in as-is. dataTypePlain?
	dataTypeRaw dataType = iota

	// dataTypeText is for textual values that will wrap on the next newline
	// that comes after the byte count requested.
	dataTypeText

	// dataTypeMCF is for textual types that have some structure, and the
	// shard split will only occur after the line that closes an MCF block.
	dataTypeMCF

	// TODO: If there are other formats of data being sharded for writing
	// that need more smarts, add them here. (e.g. JSON should split on the
	// close of a complete record so that all file shards can be independently
	// processed safely.
)

// RawDataType configures the writer to treat data as plain bytes.
func RawDataType() Option { return dataTypeRaw }

// TextDataType configures the writer to treat data as text, so data
// shards are split on line breaks and not mid-line.
func TextDataType() Option { return dataTypeText }

// MCFDataType configures the writer to treat data as MCF/TMCF so record are
// not split between file shards.
func MCFDataType() Option { return dataTypeMCF }

func (d dataType) set(opts *Options) {
	opts.dataType = d
}

// Writer implements sharded writing, spliting files to be as close to the given
// byte size as possible. This type implements io.WriterCloser and io.StringWriter.
//
// If an error occurs writing to the Writer, no more data will be accepted and all
// subsequent writes will return the error.
type Writer struct {
	basePath  string
	extension string // extension with out any leading period.
	opts      *Options

	currentFile  *os.File // file handle currently being written to.
	currentShard int      // current shard number.
	bytesWritten int64    // number of bytes written to current shard.

	// track if we should be failing all writes going forward.
	errorTriggered bool
}

// NewWriter returns a sharding writer for the given name and file extension.
// If no options are given, the writer defaults to 100 MB shard size, and
// writing out the data as bytes with no smarts on split points.
//
// If multiple of the same option are supplied, only the last will be used.
// e.g. ShardSize(1024), ShardSize(100), the shard size will be 100 bytes.
func NewWriter(basePath, extension string, opts ...Option) io.WriteCloser {
	w := &Writer{
		basePath:  basePath,
		extension: extension,

		opts: &Options{
			shardSize: DefaultShardSize,
		},
	}

	// If the user accidentally includes the dot before the extension,
	// chop it off since we insert it when making the filenames.
	strings.TrimPrefix(w.extension, ".")

	// Check opts and set any the user has chosen to set explicitly.
	for _, o := range opts {
		o.set(w.opts)
	}

	var err error
	w.currentFile, err = os.Create(w.currentFileName())
	if err != nil {
		log.Fatalf("unable to create sharded file %q", w.currentFileName())
	}
	return w
}

// currentFileName is a helper to format the current filename.
func (w *Writer) currentFileName() string {
	if w.extension == "" {
		return fmt.Sprintf("%s_%d", w.basePath, w.currentShard)
	}
	return fmt.Sprintf("%s_%d.%s", w.basePath, w.currentShard, w.extension)
}

// Write writes len(p) bytes from p to the underlying data stream. It returns
// the number of bytes written from p (0 <= n <= len(p)) and any error encountered
// that caused the write to stop early.
func (w *Writer) Write(p []byte) (n int, err error) {
	if w.errorTriggered {
		return 0, fmt.Errorf("error occurred during previous writes")
	}

	// Will this fit without needing to start a new shard.
	if w.opts.shardSize-w.bytesWritten-int64(len(p)) > 0 {
		n, err := w.currentFile.Write(p)
		w.bytesWritten += int64(n)
		if err != nil || n != len(p) {
			w.errorTriggered = true
		}
		return n, err
	}

	// TODO(rsned): Implment the sharded writing of bytes.
	return -1, fmt.Errorf("sharded write not implemented")
}

// WriteString writes the contents of the given string. It returns the number of
// bytes written from from the string (0 <= n <= len(s)) and any error encountered
// that caused the write to stop early.
func (w *Writer) WriteString(s string) (n int, err error) {
	if w.errorTriggered {
		return 0, fmt.Errorf("error occurred during previous writes")
	}

	// TODO(rsned): Maybe allow a +/- 5% leeway so we don't end up
	// writing out a 100 MB shard and a 1 kB shard when it could all
	// end up in one file.

	// Check if we can write this without triggering a new shard.
	if w.opts.shardSize-w.bytesWritten-int64(len(s)) > 0 {
		n, err := w.currentFile.WriteString(s)
		w.bytesWritten += int64(n)
		if err != nil || n != len(s) {
			w.errorTriggered = true
		}
		return n, err
	}

	var bytesWritten int64

	switch w.opts.dataType {
	case dataTypeRaw:
		// We will need more than the current shard to complete the write.
		for {
			// Figure out how much of the input we can use before sharding.
			splitPoint := w.opts.shardSize - w.bytesWritten
			// If we don't have enough to fill out a shard, adjust the cut point.
			if splitPoint > int64(len(s)) {
				splitPoint = int64(len(s))
			}

			n, err = w.currentFile.WriteString(s[:splitPoint])
			if (err != nil) || int64(n) != splitPoint {
				w.errorTriggered = true
			}
			bytesWritten += int64(n)

			// drop the portion written so far from the string.
			s = s[splitPoint:]

			// If there is no more to write, we are done with the loop.
			if len(s) == 0 {
				break
			}
			// Else, there is still more to write, create a new
			// shard and keep going.
			w.newShard()
		}
	case dataTypeText:
		// TODO(rsned): implement
		return -1, fmt.Errorf("sharded writestring for text not implemented yet.")
	case dataTypeMCF:
		// TODO(rsned): implement
		return -1, fmt.Errorf("sharded writestring for MCF not implemented yet.")
	}

	return int(bytesWritten), err
}

// WriteByte writes a single byte to the underlying data stream. It returns
// any error encountered that caused the write to fail.
func (w *Writer) WriteByte(c byte) error {
	if w.errorTriggered {
		return fmt.Errorf("error occurred during previous writes")
	}

	// Will this byte fit, or do we need to start a new shard.
	if w.opts.shardSize-w.bytesWritten-1 <= 0 {
		w.newShard()
	}

	n, err := w.currentFile.Write([]byte{c})
	w.bytesWritten += 1
	if err != nil || n != 1 {
		w.errorTriggered = true
	}
	return err
}

// Close implements io.Closer interface.
func (w *Writer) Close() error {
	return w.currentFile.Close()
}

// newShard is used to close the existing shard, start a new one, and reset the counters.
func (w *Writer) newShard() {
	if w.currentFile != nil {
		// Do we need to do something if there was an error closing
		// the current file?
		w.currentFile.Close()
	}

	w.currentShard++
	w.bytesWritten = 0

	var err error
	w.currentFile, err = os.Create(w.currentFileName())
	if err != nil {
		w.errorTriggered = true
	}
}
