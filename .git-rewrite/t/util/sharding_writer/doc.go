/*
Package sharding_writer implements an io.Writer that can smartly split files
commonly used in Data Commons imports into comfortable sized pieces.

The Writer implements io.Writer, io.StringWriter, io.ByteWriter, and io.Closer.

The default instance of the writer will use 100 MB as the file size to split on, e.g.,

	w := sharding_writer.NewWriter(filename, extension)

The size of the shards can be specified when creating the writer:

	w := sharding_writer.NewWriter(filename, extension,
		sharding_writer.ShardSize(1024*1024))  // shard size is in bytes.

The writer has some smarts if the data being written to the file is text or even
MCF / TMCF files. In these cases the writer will ensure shards don't split in the
middle of a line or a node definition.

When creating the writer, there are options that can specify the type of data to
get the smarter behavior.

To ensure lines aren't broken in the middle, use TextDataType option.

	w := sharding_writer.NewWriter(filename, extension,
		sharding_writer.TextDataType(),
		sharding_writer.ShardSize(10*1024))

For files of MCF data, specify MCFDataType to ensure files don't split in the middle of a node.

	w := sharding_writer.NewWriter(filename, extension,
		sharding_writer.MCFDataType())

Note that this package does NOT attempt to balance the shard sizes, it is for
splitting the writes per the given size boundaries.

To take advantage of the io.StringWriter interface, use the io.WriteString method.
(io.WriteString takes a Writer, but calls it WriteString method if it has one).


Example Usage:

	import "github.com/datacommons/data/util/sharding_writer"

	...

	// Create the sharded writer with ~64kB files.
	sw := sharding_writer.NewWriter("my_data", "csv",
		sharding_writer.TextDataType().
		sharding_writer.ShardSize(64*1024))  // shard size is in bytes.

	// Ensure we close when we are all done.
	defer sw.Close()

	// CSV writer using our writer.
	w := csv.NewWriter(sw)

	for _, data := range inputs {
		// convert inputs into []string
		...

		if err := w.Write(record); err != nil {
			log.Fatalln("error writing record to csv:", err)
		}
	}

	// Write any buffered data to the underlying writer.
	w.Flush()

	if err := w.Error(); err != nil {
		log.Fatal(err)
	}

	// Now there will be a set of files each ~64kB give or take line length.

*/
package sharding_writer
