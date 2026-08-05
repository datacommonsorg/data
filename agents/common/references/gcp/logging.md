# Read Cloud Logging entries

Use this shared reference when a product recipe needs `gcloud logging read`.
The product recipe supplies the concrete filter, defaults, bounds, output
fields, and interpretation.

```bash
gcloud logging read '<FILTER>' \
  --project='<PROJECT>' \
  --order='<ORDER>' \
  --limit='<LIMIT>' \
  --format='<FORMAT>'
```

- `FILTER` selects matching log entries.
- `PROJECT` identifies the project containing the logs.
- `ORDER` is `asc` or `desc` by timestamp; the CLI defaults to `desc`.
- `LIMIT` caps the number of entries requested; omitting it is unbounded.
- `FORMAT` selects the returned representation or fields.

These parameters are available building blocks, not universal requirements.
The product recipe states which values and filters apply.

## Time selection

A timestamp is not required by the CLI. For an exact or historical window, add
a half-open UTC filter:

```text
timestamp >= "<START>" AND timestamp < "<END>"
```

Without a timestamp filter, `gcloud logging read` applies a default freshness
of one day. A product recipe can choose another relative window by adding:

```text
--freshness='<FRESHNESS>'
```

`--freshness` works only with descending order and a filter without a
timestamp. Use either explicit timestamps or freshness, not both.

## Common filters

Use only the clauses relevant to the product:

```text
logName = "projects/<PROJECT>/logs/<LOG_ID>"
resource.type = "<RESOURCE_TYPE>"
resource.labels.<KEY> = "<VALUE>"
labels.<KEY> = "<VALUE>"
severity >= "<SEVERITY>"
jsonPayload.<FIELD> = "<VALUE>"
textPayload : "<TERM>"
```

Severity values, from lowest to highest, are `DEFAULT`, `DEBUG`, `INFO`,
`NOTICE`, `WARNING`, `ERROR`, `CRITICAL`, `ALERT`, and `EMERGENCY`.
`severity >= "ERROR"` therefore includes `ERROR` and every higher severity.

For string fields, `:` matches a substring while `=` matches the whole field.
Use `textPayload : "<TERM>"` for a contains search and
`textPayload = "<VALUE>"` only when the complete payload text is known.

Combine clauses with uppercase `AND` or `OR`, and group `OR` clauses with
parentheses. Prefer a finite limit, narrow by time or a known identifier when
practical, and select only the fields needed for the answer.

## Example

Wrap the complete filter in single shell quotes and keep Logging string values
in double quotes:

```bash
gcloud logging read \
  'timestamp >= "<START>" AND timestamp < "<END>" AND severity >= "ERROR" AND (textPayload : "<TERM_1>" OR textPayload : "<TERM_2>")' \
  --project='<PROJECT>' \
  --order='desc' \
  --limit='<LIMIT>' \
  --format='json(timestamp,severity,textPayload)'
```

For less common options, see the official
[`gcloud logging read` reference](https://docs.cloud.google.com/sdk/gcloud/reference/logging/read)
and [Logging query language](https://docs.cloud.google.com/logging/docs/view/logging-query-language).
