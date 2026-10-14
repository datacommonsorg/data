# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""ET-layer StatVar aggregation runner (DuckDB and BigQuery).

Implements parity with google3/datacommons/prophet/derived_graph/stat_var_aggregation/processor.cc:
1. Chained/hierarchical rules (where a rule's source_sv_ids reference another rule's
   ancestor_sv_id in the same import) are expanded in memory at runtime.
2. Input observations are deduplicated by (variableMeasured, observationAbout,
   observationDate, observationPeriod, unit, measurementMethod, scalingFactor)
   keeping the last observation in input order (matching C++ input_ts_map_).
3. Grouping by facet happens on the ORIGINAL measurementMethod BEFORE prefixing
   with 'dcAggregate/' (or setting 'DataCommonsAggregate').
4. Supports SUM (default), MIN, MAX, and AVG aggregation methods.
"""

import copy
import csv
import glob
import hashlib
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import uuid

import duckdb
import fastavro
from omegaconf import OmegaConf
import pyarrow as pa

ALLOWED_AGG_METHODS = frozenset({"SUM", "MIN", "MAX", "AVG"})

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "configs",
    "statvar_aggregation.yaml",
)

STAT_VAR_AGG_MCF_FILENAME = "stat_var_agg_nodes.mcf"
STAT_VAR_AGG_AVRO_FILENAME = "stat_var_agg.avro"
FALLBACK_OBS_AVRO_FILENAME = "table_observations_fallback.avro"

OBSERVATION_AVRO_SCHEMA: Dict[str, Any] = {
    "namespace": "org.datacommons.avro",
    "type": "record",
    "name": "StatVarObservationRecord",
    "fields": [
        {"name": "dcid", "type": "string", "default": ""},
        {"name": "variableMeasured", "type": "string", "default": ""},
        {"name": "observationAbout", "type": "string", "default": ""},
        {"name": "observationDate", "type": "string", "default": ""},
        {"name": "value", "type": ["null", "double"], "default": None},
        {"name": "valueStr", "type": "string", "default": ""},
        {"name": "unit", "type": "string", "default": ""},
        {"name": "measurementMethod", "type": "string", "default": ""},
        {"name": "observationPeriod", "type": "string", "default": ""},
        {"name": "scalingFactor", "type": "string", "default": ""},
    ],
}

PARSED_AVRO_SCHEMA = fastavro.parse_schema(OBSERVATION_AVRO_SCHEMA)


def format_numeric_value(val: float) -> str:
    """Formats a float observation value cleanly without scientific-notation truncation."""
    if val is None or math.isnan(val) or math.isinf(val):
        return ""
    if float(val).is_integer() and abs(val) < 1e16:
        return str(int(round(val)))
    formatted = f"{val:.10f}".rstrip("0").rstrip(".")
    return formatted if formatted and formatted != "-0" else "0"


def compute_observation_dcid(
    variable_measured: str,
    observation_about: str,
    observation_date: str,
    value_str: str,
    observation_period: str = "",
    measurement_method: str = "",
    unit: str = "",
    scaling_factor: str = "",
) -> str:
    """Computes a deterministic observation dcid matching genmcf conventions."""
    key_parts = [
        f"observationAbout={observation_about}",
        f"variableMeasured={variable_measured}",
        f"observationDate={observation_date}",
        f"value={value_str}",
    ]
    if observation_period:
        key_parts.append(f"observationPeriod={observation_period}")
    if measurement_method:
        key_parts.append(f"measurementMethod={measurement_method}")
    if unit:
        key_parts.append(f"unit={unit}")
    if scaling_factor:
        key_parts.append(f"scalingFactor={scaling_factor}")
    digest = hashlib.sha256("".join(key_parts).encode("utf-8")).hexdigest()[:13]
    return f"dc/o/{digest}"


def load_stat_var_aggregation_config(
    import_name: str,
    config_path: Optional[str] = None,
    import_spec: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Loads StatVar aggregation rules for an import_name."""
    if import_spec and import_spec.get("stat_var_aggregation"):
        raw_rules = import_spec["stat_var_aggregation"]
        if isinstance(raw_rules, dict) and "aggregations" in raw_rules:
            return list(raw_rules["aggregations"])
        if isinstance(raw_rules, list):
            return list(raw_rules)

    resolved_path = config_path or DEFAULT_CONFIG_PATH
    if not resolved_path or not os.path.exists(resolved_path):
        logging.debug("StatVar aggregation config file not found at %s", resolved_path)
        return []

    cfg = OmegaConf.load(resolved_path)
    cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    if not isinstance(cfg_dict, dict):
        return []

    imports_map = cfg_dict.get("imports", {})
    import_entry = imports_map.get(import_name)
    if not import_entry:
        return []

    rules = import_entry.get("stat_var_aggregation", [])
    return list(rules) if isinstance(rules, list) else []


def expand_stat_var_aggregation_config(
    aggregations: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Expands chained/hierarchical StatVar aggregation rules in memory.

    When a rule's source_sv_ids contain another rule's ancestor_sv_id in the same
    import (e.g. CensusACS5YearSurvey_SubjectTables_S0504 and S1251), recursively
    expands those intermediate StatVars into leaf source_sv_ids and propagates
    skip_all_sources_present_check.
    """
    rule_map: Dict[str, Dict[str, Any]] = {}
    for rule in aggregations:
        anc = rule.get("ancestor_sv_id")
        if anc:
            rule_map[str(anc)] = rule

    def _expand_sources(sv_id: str, visited: set[str]) -> tuple[List[str], bool]:
        if sv_id not in rule_map or sv_id in visited:
            return [sv_id], False
        visited = visited | {sv_id}
        child_rule = rule_map[sv_id]
        leaf_sources: List[str] = []
        any_skip = bool(child_rule.get("skip_all_sources_present_check", False))
        for child_src in child_rule.get("source_sv_ids", []):
            sub_leaves, sub_skip = _expand_sources(str(child_src), visited)
            leaf_sources.extend(sub_leaves)
            any_skip = any_skip or sub_skip
        return leaf_sources, any_skip

    expanded_rules: List[Dict[str, Any]] = []
    for rule in aggregations:
        anc = str(rule.get("ancestor_sv_id", "")).strip()
        if not anc:
            continue
        raw_sources = rule.get("source_sv_ids", [])
        if not raw_sources:
            continue

        all_leaves: List[str] = []
        inherited_skip = bool(rule.get("skip_all_sources_present_check", False))
        has_derived = False
        for src in raw_sources:
            src_str = str(src).strip()
            if not src_str:
                continue
            if src_str in rule_map and src_str != anc:
                has_derived = True
            leaves, child_skip = _expand_sources(src_str, {anc})
            all_leaves.extend(leaves)
            inherited_skip = inherited_skip or child_skip

        deduped_leaves = list(dict.fromkeys(all_leaves))
        agg_method = str(rule.get("aggregation_method", "SUM")).strip().upper()
        if agg_method not in ALLOWED_AGG_METHODS:
            raise ValueError(
                f"Unsupported aggregation_method '{agg_method}' for {anc}. "
                f"Allowed methods: {sorted(ALLOWED_AGG_METHODS)}"
            )

        new_rule = copy.deepcopy(dict(rule))
        new_rule["ancestor_sv_id"] = anc
        new_rule["source_sv_ids"] = deduped_leaves
        new_rule["skip_all_sources_present_check"] = inherited_skip
        new_rule["aggregation_method"] = agg_method
        if has_derived:
            new_rule["has_derived_sources"] = True
        expanded_rules.append(new_rule)

    return expanded_rules


def _strip_mcf_value(raw_val: str) -> str:
    """Strips dcid:/dcs:/schema: prefixes and surrounding quotes from an MCF value."""
    val = raw_val.strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        val = val[1:-1]
    for prefix in ("dcid:", "dcs:", "schema:"):
        if val.startswith(prefix):
            val = val[len(prefix) :]
            break
    return val.strip()


def parse_mcf_observations(mcf_paths: Iterable[str]) -> List[Dict[str, Any]]:
    """Parses StatVarObservation nodes from MCF files into Avro record dicts."""
    records: List[Dict[str, Any]] = []

    def _flush_node(node: Dict[str, str]) -> None:
        if node.get("typeOf") != "StatVarObservation":
            return
        var_measured = node.get("variableMeasured", "")
        obs_about = node.get("observationAbout", "")
        obs_date = node.get("observationDate", "")
        val_str = node.get("value", "")
        if not (var_measured and obs_about and obs_date and val_str):
            return
        try:
            numeric_val: Optional[float] = float(val_str)
        except ValueError:
            numeric_val = None
        records.append({
            "dcid": node.get("dcid", node.get("Node", "")),
            "variableMeasured": var_measured,
            "observationAbout": obs_about,
            "observationDate": obs_date,
            "value": numeric_val,
            "valueStr": val_str,
            "unit": node.get("unit", ""),
            "measurementMethod": node.get("measurementMethod", ""),
            "observationPeriod": node.get("observationPeriod", ""),
            "scalingFactor": node.get("scalingFactor", ""),
        })

    for mcf_path in mcf_paths:
        current_node: Dict[str, str] = {}
        with open(mcf_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, raw_val = line.split(":", 1)
                key = key.strip()
                val = _strip_mcf_value(raw_val)
                if key == "Node":
                    if current_node:
                        _flush_node(current_node)
                    current_node = {"Node": val}
                else:
                    current_node[key] = val
        if current_node:
            _flush_node(current_node)

    return records


def write_avro_observations(
    records: Sequence[Dict[str, Any]], output_avro_path: str
) -> None:
    """Writes StatVarObservation records to an Avro file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_avro_path)), exist_ok=True)
    with open(output_avro_path, "wb") as out_f:
        fastavro.writer(
            out_f,
            PARSED_AVRO_SCHEMA,
            records,
            codec="deflate",
        )


def read_avro_observations(avro_paths: Iterable[str]) -> List[Dict[str, Any]]:
    """Reads StatVarObservation records from one or more Avro files."""
    records: List[Dict[str, Any]] = []
    for avro_path in avro_paths:
        with open(avro_path, "rb") as in_f:
            reader = fastavro.reader(in_f)
            for rec in reader:
                records.append(dict(rec))
    return records


def mcf_to_avro(mcf_paths: Sequence[str], output_avro_path: str) -> int:
    """Fallback converter from MCF files to Avro observation file."""
    records = parse_mcf_observations(mcf_paths)
    write_avro_observations(records, output_avro_path)
    return len(records)


def write_mcf_observations(
    records: Sequence[Dict[str, Any]], output_mcf_path: str
) -> None:
    """Writes aggregated StatVarObservation records to a .mcf file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_mcf_path)), exist_ok=True)
    lines: List[str] = []
    for rec in records:
        dcid = rec["dcid"]
        lines.append(f"Node: dcid:{dcid}")
        lines.append("typeOf: dcs:StatVarObservation")
        lines.append(f'dcid: "{dcid}"')
        lines.append(f'variableMeasured: dcs:{rec["variableMeasured"]}')
        lines.append(f'observationAbout: dcid:{rec["observationAbout"]}')
        lines.append(f'observationDate: "{rec["observationDate"]}"')
        lines.append(f'value: {rec["valueStr"]}')
        if rec.get("observationPeriod"):
            lines.append(f'observationPeriod: "{rec["observationPeriod"]}"')
        if rec.get("measurementMethod"):
            lines.append(f'measurementMethod: dcs:{rec["measurementMethod"]}')
        if rec.get("unit"):
            lines.append(f'unit: dcs:{rec["unit"]}')
        if rec.get("scalingFactor"):
            lines.append(f'scalingFactor: "{rec["scalingFactor"]}"')
        lines.append("")

    with open(output_mcf_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(lines))


def _build_rules_arrow_table(expanded_rules: Sequence[Dict[str, Any]]) -> pa.Table:
    """Builds a PyArrow table representing expanded StatVar aggregation rules."""
    rule_ids: List[int] = []
    ancestor_sv_ids: List[str] = []
    source_sv_ids: List[str] = []
    expected_counts: List[int] = []
    skip_checks: List[bool] = []
    agg_methods: List[str] = []

    for idx, rule in enumerate(expanded_rules):
        anc = str(rule["ancestor_sv_id"])
        sources = list(dict.fromkeys(str(s) for s in rule["source_sv_ids"]))
        expected_count = len(sources)
        skip_check = bool(rule.get("skip_all_sources_present_check", False))
        agg_method = str(rule.get("aggregation_method", "SUM")).upper()
        if agg_method not in ALLOWED_AGG_METHODS:
            raise ValueError(f"Invalid aggregation_method: {agg_method}")
        for src in sources:
            rule_ids.append(idx)
            ancestor_sv_ids.append(anc)
            source_sv_ids.append(src)
            expected_counts.append(expected_count)
            skip_checks.append(skip_check)
            agg_methods.append(agg_method)

    schema = pa.schema([
        ("rule_id", pa.int32()),
        ("ancestor_sv_id", pa.string()),
        ("source_sv_id", pa.string()),
        ("expected_source_count", pa.int32()),
        ("skip_check", pa.bool_()),
        ("agg_method", pa.string()),
    ])
    return pa.Table.from_pydict(
        {
            "rule_id": rule_ids,
            "ancestor_sv_id": ancestor_sv_ids,
            "source_sv_id": source_sv_ids,
            "expected_source_count": expected_counts,
            "skip_check": skip_checks,
            "agg_method": agg_methods,
        },
        schema=schema,
    )


def _build_observations_arrow_table(records: Sequence[Dict[str, Any]]) -> pa.Table:
    """Builds a PyArrow table from StatVarObservation records with input row order."""
    schema = pa.schema([
        ("row_num", pa.int64()),
        ("variableMeasured", pa.string()),
        ("observationAbout", pa.string()),
        ("observationDate", pa.string()),
        ("value", pa.float64()),
        ("unit", pa.string()),
        ("measurementMethod", pa.string()),
        ("observationPeriod", pa.string()),
        ("scalingFactor", pa.string()),
    ])
    if not records:
        return pa.Table.from_pydict(
            {name: [] for name in schema.names}, schema=schema
        )

    return pa.Table.from_pydict(
        {
            "row_num": list(range(len(records))),
            "variableMeasured": [str(r.get("variableMeasured") or "") for r in records],
            "observationAbout": [str(r.get("observationAbout") or "") for r in records],
            "observationDate": [str(r.get("observationDate") or "") for r in records],
            "value": [
                float(r["value"]) if r.get("value") is not None else None
                for r in records
            ],
            "unit": [str(r.get("unit") or "") for r in records],
            "measurementMethod": [
                str(r.get("measurementMethod") or "") for r in records
            ],
            "observationPeriod": [
                str(r.get("observationPeriod") or "") for r in records
            ],
            "scalingFactor": [str(r.get("scalingFactor") or "") for r in records],
        },
        schema=schema,
    )


DUCKDB_AGGREGATION_SQL = """
WITH dedup_obs AS (
    SELECT
        variableMeasured,
        observationAbout,
        observationDate,
        COALESCE(observationPeriod, '') AS observationPeriod,
        COALESCE(unit, '') AS unit,
        COALESCE(measurementMethod, '') AS origMeasurementMethod,
        COALESCE(scalingFactor, '') AS scalingFactor,
        ARG_MAX(value, row_num) AS value
    FROM obs_table
    WHERE value IS NOT NULL
      AND variableMeasured IN (SELECT DISTINCT source_sv_id FROM rules_table)
    GROUP BY
        variableMeasured,
        observationAbout,
        observationDate,
        COALESCE(observationPeriod, ''),
        COALESCE(unit, ''),
        COALESCE(measurementMethod, ''),
        COALESCE(scalingFactor, '')
),
grouped AS (
    SELECT
        r.rule_id,
        r.ancestor_sv_id AS variableMeasured,
        o.observationAbout,
        o.observationDate,
        o.observationPeriod,
        o.unit,
        o.origMeasurementMethod,
        o.scalingFactor,
        r.agg_method,
        r.skip_check,
        r.expected_source_count,
        COUNT(DISTINCT o.variableMeasured) AS present_source_count,
        SUM(o.value) AS sum_val,
        MIN(o.value) AS min_val,
        MAX(o.value) AS max_val,
        AVG(o.value) AS avg_val
    FROM dedup_obs o
    INNER JOIN rules_table r
        ON o.variableMeasured = r.source_sv_id
    GROUP BY
        r.rule_id,
        r.ancestor_sv_id,
        o.observationAbout,
        o.observationDate,
        o.observationPeriod,
        o.unit,
        o.origMeasurementMethod,
        o.scalingFactor,
        r.agg_method,
        r.skip_check,
        r.expected_source_count
    HAVING r.skip_check OR COUNT(DISTINCT o.variableMeasured) = r.expected_source_count
)
SELECT
    variableMeasured,
    observationAbout,
    observationDate,
    CASE agg_method
        WHEN 'SUM' THEN sum_val
        WHEN 'MIN' THEN min_val
        WHEN 'MAX' THEN max_val
        WHEN 'AVG' THEN avg_val
        ELSE sum_val
    END AS value,
    observationPeriod,
    unit,
    CASE
        WHEN origMeasurementMethod = '' THEN 'DataCommonsAggregate'
        WHEN origMeasurementMethod = 'DataCommonsAggregate' THEN 'DataCommonsAggregate'
        WHEN origMeasurementMethod LIKE 'dcAggregate/%' THEN origMeasurementMethod
        ELSE 'dcAggregate/' || origMeasurementMethod
    END AS measurementMethod,
    scalingFactor
FROM grouped
ORDER BY
    rule_id,
    variableMeasured,
    observationAbout,
    observationDate,
    origMeasurementMethod,
    observationPeriod,
    unit,
    scalingFactor
"""


def run_stat_var_aggregation_duckdb(
    avro_paths: Sequence[str],
    aggregations: Sequence[Dict[str, Any]],
    duckdb_temp_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Executes StatVar aggregation over local Avro files using DuckDB."""
    expanded_rules = expand_stat_var_aggregation_config(aggregations)
    if not expanded_rules or not avro_paths:
        return []

    raw_records = read_avro_observations(avro_paths)
    if not raw_records:
        return []

    obs_arrow = _build_observations_arrow_table(raw_records)
    rules_arrow = _build_rules_arrow_table(expanded_rules)

    con = duckdb.connect(database=":memory:")
    try:
        if duckdb_temp_dir:
            os.makedirs(duckdb_temp_dir, exist_ok=True)
            con.execute("SET temp_directory = ?", [duckdb_temp_dir])
        con.register("obs_table", obs_arrow)
        con.register("rules_table", rules_arrow)
        rows = con.execute(DUCKDB_AGGREGATION_SQL).fetchall()
    finally:
        con.close()

    output_records: List[Dict[str, Any]] = []
    for (
        var_measured,
        obs_about,
        obs_date,
        val,
        obs_period,
        unit,
        m_method,
        scaling_factor,
    ) in rows:
        numeric_val = float(val)
        val_str = format_numeric_value(numeric_val)
        dcid = compute_observation_dcid(
            variable_measured=var_measured,
            observation_about=obs_about,
            observation_date=obs_date,
            value_str=val_str,
            observation_period=obs_period,
            measurement_method=m_method,
            unit=unit,
            scaling_factor=scaling_factor,
        )
        output_records.append({
            "dcid": dcid,
            "variableMeasured": var_measured,
            "observationAbout": obs_about,
            "observationDate": obs_date,
            "value": numeric_val,
            "valueStr": val_str,
            "unit": unit,
            "measurementMethod": m_method,
            "observationPeriod": obs_period,
            "scalingFactor": scaling_factor,
        })

    return output_records


def run_stat_var_aggregation_bigquery(
    gcs_avro_uris: Sequence[str],
    aggregations: Sequence[Dict[str, Any]],
    project_id: str,
    dataset_id: str,
) -> List[Dict[str, Any]]:
    """Executes StatVar aggregation over GCS Avro files using BigQuery."""
    from google.cloud import bigquery

    expanded_rules = expand_stat_var_aggregation_config(aggregations)
    if not expanded_rules or not gcs_avro_uris:
        return []

    client = bigquery.Client(project=project_id)
    run_id = uuid.uuid4().hex[:12]
    obs_table_id = f"{project_id}.{dataset_id}.temp_et_obs_{run_id}"
    rules_table_id = f"{project_id}.{dataset_id}.temp_et_rules_{run_id}"

    try:
        load_cfg = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.AVRO,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        client.load_table_from_uri(
            list(gcs_avro_uris), obs_table_id, job_config=load_cfg
        ).result()

        rules_arrow = _build_rules_arrow_table(expanded_rules)
        client.load_table_from_dataframe(
            rules_arrow.to_pandas(),
            rules_table_id,
            job_config=bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            ),
        ).result()

        bq_sql = f"""
        WITH dedup_obs AS (
            SELECT
                variableMeasured,
                observationAbout,
                observationDate,
                COALESCE(observationPeriod, '') AS observationPeriod,
                COALESCE(unit, '') AS unit,
                COALESCE(measurementMethod, '') AS origMeasurementMethod,
                COALESCE(scalingFactor, '') AS scalingFactor,
                ANY_VALUE(value) AS value
            FROM `{obs_table_id}`
            WHERE value IS NOT NULL
              AND variableMeasured IN (SELECT DISTINCT source_sv_id FROM `{rules_table_id}`)
            GROUP BY
                variableMeasured,
                observationAbout,
                observationDate,
                COALESCE(observationPeriod, ''),
                COALESCE(unit, ''),
                COALESCE(measurementMethod, ''),
                COALESCE(scalingFactor, '')
        ),
        grouped AS (
            SELECT
                r.rule_id,
                r.ancestor_sv_id AS variableMeasured,
                o.observationAbout,
                o.observationDate,
                o.observationPeriod,
                o.unit,
                o.origMeasurementMethod,
                o.scalingFactor,
                r.agg_method,
                r.skip_check,
                r.expected_source_count,
                COUNT(DISTINCT o.variableMeasured) AS present_source_count,
                SUM(o.value) AS sum_val,
                MIN(o.value) AS min_val,
                MAX(o.value) AS max_val,
                AVG(o.value) AS avg_val
            FROM dedup_obs o
            INNER JOIN `{rules_table_id}` r
                ON o.variableMeasured = r.source_sv_id
            GROUP BY
                r.rule_id,
                r.ancestor_sv_id,
                o.observationAbout,
                o.observationDate,
                o.observationPeriod,
                o.unit,
                o.origMeasurementMethod,
                o.scalingFactor,
                r.agg_method,
                r.skip_check,
                r.expected_source_count
            HAVING r.skip_check OR COUNT(DISTINCT o.variableMeasured) = r.expected_source_count
        )
        SELECT
            variableMeasured,
            observationAbout,
            observationDate,
            CASE agg_method
                WHEN 'SUM' THEN sum_val
                WHEN 'MIN' THEN min_val
                WHEN 'MAX' THEN max_val
                WHEN 'AVG' THEN avg_val
                ELSE sum_val
            END AS value,
            observationPeriod,
            unit,
            CASE
                WHEN origMeasurementMethod = '' THEN 'DataCommonsAggregate'
                WHEN origMeasurementMethod = 'DataCommonsAggregate' THEN 'DataCommonsAggregate'
                WHEN STARTS_WITH(origMeasurementMethod, 'dcAggregate/') THEN origMeasurementMethod
                ELSE CONCAT('dcAggregate/', origMeasurementMethod)
            END AS measurementMethod,
            scalingFactor
        FROM grouped
        ORDER BY
            rule_id,
            variableMeasured,
            observationAbout,
            observationDate,
            origMeasurementMethod,
            observationPeriod,
            unit,
            scalingFactor
        """
        rows = client.query(bq_sql).result()
        output_records: List[Dict[str, Any]] = []
        for row in rows:
            numeric_val = float(row.value)
            val_str = format_numeric_value(numeric_val)
            dcid = compute_observation_dcid(
                variable_measured=row.variableMeasured,
                observation_about=row.observationAbout,
                observation_date=row.observationDate,
                value_str=val_str,
                observation_period=row.observationPeriod,
                measurement_method=row.measurementMethod,
                unit=row.unit,
                scaling_factor=row.scalingFactor,
            )
            output_records.append({
                "dcid": dcid,
                "variableMeasured": row.variableMeasured,
                "observationAbout": row.observationAbout,
                "observationDate": row.observationDate,
                "value": numeric_val,
                "valueStr": val_str,
                "unit": row.unit,
                "measurementMethod": row.measurementMethod,
                "observationPeriod": row.observationPeriod,
                "scalingFactor": row.scalingFactor,
            })
        return output_records
    finally:
        client.delete_table(obs_table_id, not_found_ok=True)
        client.delete_table(rules_table_id, not_found_ok=True)


def update_summary_report_csv(
    summary_report_path: str, aggregated_records: Sequence[Dict[str, Any]]
) -> None:
    """Appends summary statistics for aggregated StatVars to summary_report.csv."""
    if not aggregated_records or not os.path.exists(summary_report_path):
        return

    by_sv: Dict[str, List[Dict[str, Any]]] = {}
    for rec in aggregated_records:
        by_sv.setdefault(rec["variableMeasured"], []).append(rec)

    def _fmt_java_set(items: Iterable[str]) -> str:
        non_empty = sorted({x for x in items if x})
        return "[" + ", ".join(non_empty) + "]"

    rows_to_append: List[List[Any]] = []
    for sv in sorted(by_sv.keys()):
        recs = by_sv[sv]
        places = {r["observationAbout"] for r in recs if r.get("observationAbout")}
        dates = sorted({r["observationDate"] for r in recs if r.get("observationDate")})
        vals = [float(r["value"]) for r in recs if r.get("value") is not None]
        m_methods = [f'dcs:{r["measurementMethod"]}' for r in recs if r.get("measurementMethod")]
        units = [f'dcs:{r["unit"]}' for r in recs if r.get("unit")]
        s_factors = [r["scalingFactor"] for r in recs if r.get("scalingFactor")]
        obs_periods = [r["observationPeriod"] for r in recs if r.get("observationPeriod")]

        rows_to_append.append([
            f"dcs:{sv}",
            len(places),
            len(recs),
            min(vals) if vals else float("nan"),
            max(vals) if vals else float("nan"),
            len(dates),
            dates[0] if dates else "",
            dates[-1] if dates else "",
            _fmt_java_set(m_methods),
            _fmt_java_set(units),
            _fmt_java_set(s_factors),
            _fmt_java_set(obs_periods),
        ])

    with open(summary_report_path, "a", encoding="utf-8", newline="") as csv_f:
        writer = csv.writer(csv_f)
        writer.writerows(rows_to_append)


def run_stat_var_aggregation_for_genmcf(
    import_name: str,
    genmcf_output_path: str,
    config_path: Optional[str] = None,
    import_spec: Optional[Dict[str, Any]] = None,
    engine: str = "duckdb",
    bigquery_project_id: Optional[str] = None,
    bigquery_dataset_id: Optional[str] = None,
    gcs_avro_uris: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """Runs ET-layer StatVar aggregation for a genmcf output directory if configured.

    Returns the path to the generated stat_var_agg_nodes.mcf file if aggregations
    were produced, or None otherwise.
    """
    rules = load_stat_var_aggregation_config(
        import_name=import_name,
        config_path=config_path,
        import_spec=import_spec,
    )
    if not rules:
        return None

    if not os.path.exists(genmcf_output_path):
        logging.warning(
            "genmcf output path %s does not exist for %s",
            genmcf_output_path,
            import_name,
        )
        return None

    avro_files = sorted(
        f
        for f in glob.glob(os.path.join(genmcf_output_path, "*.avro"))
        if os.path.basename(f) != STAT_VAR_AGG_AVRO_FILENAME
    )

    if not avro_files:
        # Fallback: convert table_mcf_nodes_*.mcf (or other observation MCFs) to Avro
        candidate_mcfs = sorted(
            f
            for f in glob.glob(os.path.join(genmcf_output_path, "*.mcf"))
            if os.path.basename(f)
            not in (
                STAT_VAR_AGG_MCF_FILENAME,
                "instance_mcf_nodes.mcf",
                "failed_instance_mcf_nodes.mcf",
            )
            and not os.path.basename(f).startswith("failed_")
        )
        if not candidate_mcfs:
            logging.info(
                "No input Avro or observation MCF files found in %s for %s",
                genmcf_output_path,
                import_name,
            )
            return None
        fallback_avro = os.path.join(
            genmcf_output_path, FALLBACK_OBS_AVRO_FILENAME
        )
        count = mcf_to_avro(candidate_mcfs, fallback_avro)
        logging.info(
            "Converted %d MCF observations into fallback Avro %s",
            count,
            fallback_avro,
        )
        avro_files = [fallback_avro]

    engine_norm = (engine or "duckdb").strip().lower()
    if engine_norm == "bigquery":
        if not (bigquery_project_id and bigquery_dataset_id and gcs_avro_uris):
            raise ValueError(
                "bigquery_project_id, bigquery_dataset_id, and gcs_avro_uris "
                "are required when engine='bigquery'"
            )
        agg_records = run_stat_var_aggregation_bigquery(
            gcs_avro_uris=gcs_avro_uris,
            aggregations=rules,
            project_id=bigquery_project_id,
            dataset_id=bigquery_dataset_id,
        )
    else:
        agg_records = run_stat_var_aggregation_duckdb(
            avro_paths=avro_files,
            aggregations=rules,
        )

    if not agg_records:
        logging.info(
            "StatVar aggregation for %s produced 0 aggregated observations",
            import_name,
        )
        return None

    output_mcf_path = os.path.join(
        genmcf_output_path, STAT_VAR_AGG_MCF_FILENAME
    )
    output_avro_path = os.path.join(
        genmcf_output_path, STAT_VAR_AGG_AVRO_FILENAME
    )
    write_mcf_observations(agg_records, output_mcf_path)
    write_avro_observations(agg_records, output_avro_path)

    summary_csv_path = os.path.join(genmcf_output_path, "summary_report.csv")
    update_summary_report_csv(summary_csv_path, agg_records)

    logging.info(
        "Generated %d aggregated StatVarObservations for %s in %s",
        len(agg_records),
        import_name,
        output_mcf_path,
    )
    return output_mcf_path
