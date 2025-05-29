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
	"math"
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
type shardSize int64

// ShardSize returns an option that sets the desired shard size in bytes.
//
// If the value is non-positive, then there will be no splitting of output.
// All data will go in a single file.
func ShardSize(numBytes int64) Option { return shardSize(numBytes) }

func (x shardSize) set(opts *Options) {
	opts.shardSize = int64(x)
}

// dataType is an enum of the different types of writing behavior based
// on the data expected to be written.
type dataType int

const (
	// dataTypeBytes is for plain bytes, no smarts, just split on exact byte count.
	//
	// This is the default behavior.
	dataTypeBytes dataType = iota

	// dataTypeText is for textual values that will wrap on the next newline
	// that comes after the byte count requested.
	dataTypeText

	// dataTypeMCF is for textual types that have some structure, and the
	// shard split will only occur after the line that closes an MCF block.
	dataTypeMCF

	// TODO(rsned): If there are other formats of data being sharded for writing
	// that need more smarts, add them here. (E.g., JSON should split on the
	// close of a complete record so that all file shards can be independently
	// processed safely.
)

// BytesDataType configures the writer to treat data as plain bytes.
func BytesDataType() Option { return dataTypeBytes }

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
	basePath  string // full path and file name prefix.
	extension string // extension with leading period if set.
	opts      *Options

	currentFile  *os.File // file handle currently being written to.
	currentShard int      // current shard number.
	bytesWritten int64    // number of bytes written to current shard [0, shardSize).

	// track if we should be failing all writes going forward.
	errorTriggered bool
}

// NewWriter returns a sharding writer for the given name and file extension.
// If no options are given, the writer defaults to 100 MB shard size, and
// writing out the data as bytes with no smarts on split points.
//
// If multiple values of the same type of option are supplied, only the last
// one will be have effect. E.g., given []Option{ShardSize(1024), ShardSize(100)},
// the shard size used will be 100 bytes.
func NewWriter(basePath, extension string, opts ...Option) io.WriteCloser {
	w := &Writer{
		basePath:  basePath,
		extension: extension,

		opts: &Options{
			shardSize: DefaultShardSize,
		},
	}

	// If the user sets an extension, prepend the period if they didn't
	// so we can more simply construct the filename.
	if len(extension) > 0 && !strings.HasPrefix("extension", ".") {
		w.extension = fmt.Sprintf(".%s", extension)
	}

	// Check the opts and set any the user has chosen to set explicitly.
	for _, o := range opts {
		o.set(w.opts)
	}

	// If the user specifies an unusable size, default to 'all data'.
	if w.opts.shardSize <= 0 {
		// 2^64 bytes in a file ought to be enough for anybody.
		w.opts.shardSize = math.MaxInt64
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
	// TODO(rsned): Come to a decision on shard number width and padding
	// that will match what the Python library does.
	// E.g., %d, %05d, etc.
	return fmt.Sprintf("%s_%d%s", w.basePath, w.currentShard, w.extension)
}

// Write writes len(p) bytes from p to the underlying data stream. It returns
// the number of bytes written from p (0 <= n <= len(p)) and any error encountered
// that caused the write to stop early.
func (w *Writer) Write(data []byte) (n int, err error) {
	if w.errorTriggered {
		return 0, fmt.Errorf("error occurred during previous writes")
	}

	var bytesWritten int64
	for len(data) > 0 {
		// Check if we need to start a new shard.
		if w.shardFull() {
			if err := w.newShard(); err != nil {
				w.errorTriggered = true
				return int(bytesWritten), err
			}
		}
		// Figure out how much of the input we can use before sharding.
		splitPoint := w.opts.shardSize - w.bytesWritten

		// If we don't have enough to fill out the remainder of
		// the current shard, adjust the cut point.
		if splitPoint > int64(len(data)) {
			splitPoint = int64(len(data))
		}

		n, err = w.currentFile.Write(data[:splitPoint])
		bytesWritten += int64(n)
		w.bytesWritten += int64(n)
		if (err != nil) || int64(n) != splitPoint {
			w.errorTriggered = true
			return int(bytesWritten), fmt.Errorf("error writing: %v", err)
		}

		// Drop the portion written so far.
		data = data[splitPoint:]
	}

	return int(bytesWritten), nil
}

// WriteString writes the contents of the given string. It returns the number n of
// bytes written from from the string (0 <= n <= len(s)) and any error encountered
// that caused the write to stop early.
func (w *Writer) WriteString(s string) (n int, err error) {
	if w.errorTriggered {
		return 0, fmt.Errorf("error occurred during previous writes")
	}

	// track total bytes written in this call, which may be more than shardSize.
	var bytesWritten int64

	switch w.opts.dataType {
	case dataTypeBytes:
		return w.Write([]byte(s))
	case dataTypeText:
		// TODO(rsned): Implement
		return -1, fmt.Errorf("sharded writestring for text not implemented yet")
	case dataTypeMCF:
		// TODO(rsned): Implement
		return -1, fmt.Errorf("sharded writestring for MCF not implemented yet")
	}

	return int(bytesWritten), err
}

// WriteByte writes a single byte to the underlying data stream. It returns
// any error encountered that caused the write to fail.
func (w *Writer) WriteByte(c byte) error {
	n, err := w.Write([]byte{c})
	if n != 1 {
		// err != nil is already caught in Write.
		w.errorTriggered = true
	}
	return err
}

// Close implements io.Closer interface.
func (w *Writer) Close() error {
	return w.currentFile.Close()
}

// newShard is used to close the existing shard, start a new one, and reset
// the counters. If an error occurs closing the current file or opening the
// new file, it is returned.
func (w *Writer) newShard() error {
	var err error

	if w.currentFile != nil {
		if err = w.currentFile.Close(); err != nil {
			w.errorTriggered = true
			return err
		}
	}

	w.currentShard++
	w.bytesWritten = 0

	w.currentFile, err = os.Create(w.currentFileName())
	if err != nil {
		w.errorTriggered = true
	}
	return err
}

// shardFull reports of the current shard is full.
func (w *Writer) shardFull() bool {
	// TODO(rsned): Future enhancement: Allow a +/- 1% leeway so we don't end up
	// writing out a 100 MB shard and a 1 kB shard when it could all
	// end up in one file.
	return (w.opts.shardSize - w.bytesWritten) <= 0
}
