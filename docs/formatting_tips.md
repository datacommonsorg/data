# Tips for formatting/cleaning CSV

These are tips for cleaning a CSV that, coupled with a corresponding TMCF,
represents graph data suitable for import into Data Commons.

## Options to use when writing CSV

When you open the CSV file for writing, it is convenient to escape the double-quote
character occurring within a field. You can do that by using the following args
to CSV writer
([example](https://github.com/datacommonsorg/data/blob/master/scripts/us_epa/facility/process_facility.py#L190-L191)).

  ```
  doublequote=False, escapechar='\\'
  ```

## Emitting DC string values

DC strings use double quotes, as does the default CSV quoting. So CSV fields
that store DC String values need to be escaped.

For example, to represent `name: "Foo Bar"`, the CSV field value should be
`"\"Foo Bar\""`.

You can achieve that by opening the output CSV to auto-escape quotes (as noted
above), and then in python code use double-quotes without escaping, like `'"Foo
Bar"'`.

## Emitting DC repeated values

DC repeated values use comma as the delimiter, as does the default CSV field
delimiter.  So CSV fields that store repeated DC values should be quoted.

For example, to represent `typeOf: dcs:County, dcs:State` in MCF, the cell value
will have `"dcs:County, dcs:State"`.

Just use the CSV writer to write the field value, and it will introduce the
double quotes.

You can have combinations of repeated strings with some containing commas. For
example, to represent `name: "Google, Inc.", "Alphabet, Inc."`, the CSV field
value would be `"\"Google, Inc.\", \"Alphabet, Inc.\""`.

You can achieve that by opening the output CSV to auto-escape quotes (as noted
above), and then in python code use double-quotes without escaping, like
`'"Google. Inc.", "Alphabet, Inc."'`.
