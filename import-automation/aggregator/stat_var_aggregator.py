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
"""ET-layer StatVar aggregation runner (BigQuery).

Implements parity with google3/datacommons/prophet/derived_graph/stat_var_aggregation/processor.cc:
1. Chained/hierarchical rules (where a rule's source_sv_ids reference another rule's
   ancestor_sv_id in the same import) are expanded in memory at runtime.
2. Input observations are deduplicated by (variableMeasured, observationAbout,
   observationDate, observationPeriod, unit, measurementMethod, scalingFactor)
   keeping the last observation in input order (row_num) (matching C++ input_ts_map_).
3. Grouping by facet happens on the ORIGINAL measurementMethod BEFORE prefixing
   with 'dcAggregate/' (or setting 'DataCommonsAggregate').
4. Supports SUM (default), MIN, MAX, and AVG aggregation methods.
"""

import contextlib
import copy
import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import math
import os
import sys
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

from google.cloud import bigquery
from omegaconf import OmegaConf

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = (_SCRIPT_DIR if os.path.exists(os.path.join(_SCRIPT_DIR, "tools"))
             else os.path.dirname(os.path.dirname(_SCRIPT_DIR)))

for _p in [
        _ROOT_DIR,
        os.path.join(_ROOT_DIR, "util"),
        os.path.join(_ROOT_DIR, "tools", "import_differ"),
        os.path.join(_ROOT_DIR, "tools", "statvar_importer"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import file_util
from tools.import_differ import bigquery_differ

ALLOWED_AGG_METHODS = frozenset({"SUM", "MIN", "MAX", "AVG"})

DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "statvar_aggregation.yaml")

STAT_VAR_AGG_MCF_FILENAME = "stat_var_agg_nodes.mcf"
STAT_VAR_SERIES_AGG_MCF_FILENAME = "stat_var_series_agg_nodes.mcf"

DEFAULT_EXCLUDE_FILENAMES = frozenset({
    STAT_VAR_AGG_MCF_FILENAME,
    STAT_VAR_SERIES_AGG_MCF_FILENAME,
    "instance_mcf_nodes.mcf",
    "failed_instance_mcf_nodes.mcf",
})


def format_numeric_value(val: Union[float, int, str, None]) -> str:
    """Formats a numeric observation value cleanly without scientific-notation truncation."""
    if val is None or val == "":
        return ""
    try:
        fval = float(val)
    except (ValueError, TypeError):
        return str(val)
    if math.isnan(fval) or math.isinf(fval):
        return ""
    if fval.is_integer() and abs(fval) < 1e16:
        return str(int(round(fval)))
    formatted = f"{fval:.10f}".rstrip("0").rstrip(".")
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
        logging.debug("StatVar aggregation config file not found at %s",
                      resolved_path)
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
    aggregations: Sequence[Dict[str, Any]],) -> List[Dict[str, Any]]:
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

    def _expand_sources(sv_id: str,
                        visited: set[str]) -> Tuple[List[str], bool]:
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
                f"Allowed methods: {sorted(ALLOWED_AGG_METHODS)}")

        new_rule = copy.deepcopy(dict(rule))
        new_rule["ancestor_sv_id"] = anc
        new_rule["source_sv_ids"] = deduped_leaves
        new_rule["skip_all_sources_present_check"] = inherited_skip
        new_rule["aggregation_method"] = agg_method
        if has_derived:
            new_rule["has_derived_sources"] = True
        expanded_rules.append(new_rule)

    return expanded_rules


def _strip_mcf_value(raw_val: Any) -> str:
    """Strips dcid:/dcs:/schema: prefixes and surrounding quotes from an MCF value."""
    if raw_val is None:
        return ""
    val = str(raw_val).strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        val = val[1:-1]
    for prefix in ("dcid:", "dcs:", "schema:"):
        if val.startswith(prefix):
            val = val[len(prefix):]
            break
    return val.strip()


def _format_mcf_node_lines(
    dcid: str,
    variable_measured: str,
    observation_about: str,
    observation_date: str,
    value_str: str,
    observation_period: str = "",
    measurement_method: str = "",
    unit: str = "",
    scaling_factor: str = "",
) -> List[str]:
    """Formats a single StatVarObservation MCF node as lines."""
    lines = [
        f"Node: dcid:{dcid}",
        "typeOf: dcs:StatVarObservation",
        f'dcid: "{dcid}"',
        f"variableMeasured: dcs:{variable_measured}",
        f"observationAbout: dcid:{observation_about}",
        f'observationDate: "{observation_date}"',
        f"value: {value_str}",
    ]
    if observation_period:
        lines.append(f'observationPeriod: "{observation_period}"')
    if measurement_method:
        lines.append(f"measurementMethod: dcs:{measurement_method}")
    if unit:
        lines.append(f"unit: dcs:{unit}")
    if scaling_factor:
        lines.append(f'scalingFactor: "{scaling_factor}"')
    lines.append("")
    return lines


def parse_mcf_observations(mcf_paths: Iterable[str]) -> List[Dict[str, Any]]:
    """Parses StatVarObservation nodes from MCF files into observation dicts."""
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
        with bigquery_differ._open_text_stream(mcf_path, "r") as f:
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


def write_mcf_observations(records: Sequence[Dict[str, Any]],
                           output_mcf_path: str) -> None:
    """Writes StatVarObservation records to a .mcf file (local or gs://)."""
    with bigquery_differ._open_text_stream(output_mcf_path, "w") as out_f:
        for idx, rec in enumerate(records):
            val_str = str(
                rec.get("valueStr") or format_numeric_value(rec.get("value")))
            sv = _strip_mcf_value(rec.get("variableMeasured", ""))
            about = _strip_mcf_value(rec.get("observationAbout", ""))
            date = _strip_mcf_value(rec.get("observationDate", ""))
            period = _strip_mcf_value(rec.get("observationPeriod", ""))
            method = _strip_mcf_value(rec.get("measurementMethod", ""))
            unit = _strip_mcf_value(rec.get("unit", ""))
            scaling = _strip_mcf_value(rec.get("scalingFactor", ""))
            dcid = rec.get("dcid") or compute_observation_dcid(
                variable_measured=sv,
                observation_about=about,
                observation_date=date,
                value_str=val_str,
                observation_period=period,
                measurement_method=method,
                unit=unit,
                scaling_factor=scaling,
            )
            node_lines = _format_mcf_node_lines(
                dcid=dcid,
                variable_measured=sv,
                observation_about=about,
                observation_date=date,
                value_str=val_str,
                observation_period=period,
                measurement_method=method,
                unit=unit,
                scaling_factor=scaling,
            )
            if idx > 0:
                out_f.write("\n")
            out_f.write("\n".join(node_lines))


@dataclass
class _StatVarSummaryStats:
    """O(1)-memory per-StatVar accumulator for summary_report.csv."""

    places: set[str] = field(default_factory=set)
    num_observations: int = 0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    dates: set[str] = field(default_factory=set)
    m_methods: set[str] = field(default_factory=set)
    units: set[str] = field(default_factory=set)
    s_factors: set[str] = field(default_factory=set)
    obs_periods: set[str] = field(default_factory=set)

    def add(
        self,
        obs_about: str,
        obs_date: str,
        numeric_val: Optional[float],
        m_method: str,
        unit: str,
        scaling_factor: str,
        obs_period: str,
    ) -> None:
        self.num_observations += 1
        if obs_about:
            self.places.add(obs_about)
        if obs_date:
            self.dates.add(obs_date)
        if numeric_val is not None and not math.isnan(numeric_val):
            if numeric_val < self.min_val:
                self.min_val = numeric_val
            if numeric_val > self.max_val:
                self.max_val = numeric_val
        if m_method:
            self.m_methods.add(f"dcs:{m_method}")
        if unit:
            self.units.add(f"dcs:{unit}")
        if scaling_factor:
            self.s_factors.add(scaling_factor)
        if obs_period:
            self.obs_periods.add(obs_period)


def _format_summary_rows(
    stats_by_sv: Mapping[str, _StatVarSummaryStats],) -> List[List[Any]]:
    """Formats per-StatVar summary accumulators into summary_report.csv rows."""

    def _fmt_java_set(items: Iterable[str]) -> str:
        non_empty = sorted({x for x in items if x})
        return "[" + ", ".join(non_empty) + "]"

    rows_to_append: List[List[Any]] = []
    for sv in sorted(stats_by_sv.keys()):
        st = stats_by_sv[sv]
        sorted_dates = sorted(st.dates)
        has_vals = st.min_val != float("inf") and st.max_val != float("-inf")
        rows_to_append.append([
            f"dcs:{sv}",
            len(st.places),
            st.num_observations,
            st.min_val if has_vals else float("nan"),
            st.max_val if has_vals else float("nan"),
            len(sorted_dates),
            sorted_dates[0] if sorted_dates else "",
            sorted_dates[-1] if sorted_dates else "",
            _fmt_java_set(st.m_methods),
            _fmt_java_set(st.units),
            _fmt_java_set(st.s_factors),
            _fmt_java_set(st.obs_periods),
        ])
    return rows_to_append


def update_summary_report_csv(
    summary_report_path: str,
    aggregated_data: Union[Sequence[Dict[str, Any]],
                           Mapping[str, _StatVarSummaryStats]],
) -> None:
    """Appends summary statistics for aggregated StatVars to summary_report.csv (local or gs://)."""
    if not aggregated_data or not summary_report_path:
        return

    is_gcs = file_util.file_is_gcs(summary_report_path)
    if is_gcs:
        if not file_util.file_get_matching(summary_report_path):
            return
    elif not os.path.exists(summary_report_path):
        return

    if isinstance(aggregated_data, Mapping):
        stats_by_sv = aggregated_data
    else:
        stats_by_sv: Dict[str, _StatVarSummaryStats] = {}
        for rec in aggregated_data:
            sv = _strip_mcf_value(rec.get("variableMeasured", ""))
            if not sv:
                continue
            val = rec.get("value")
            numeric_val = float(val) if val is not None and val != "" else None
            stats_by_sv.setdefault(sv, _StatVarSummaryStats()).add(
                obs_about=_strip_mcf_value(rec.get("observationAbout", "")),
                obs_date=_strip_mcf_value(rec.get("observationDate", "")),
                numeric_val=numeric_val,
                m_method=_strip_mcf_value(rec.get("measurementMethod", "")),
                unit=_strip_mcf_value(rec.get("unit", "")),
                scaling_factor=_strip_mcf_value(rec.get("scalingFactor", "")),
                obs_period=_strip_mcf_value(rec.get("observationPeriod", "")),
            )

    rows_to_append = _format_summary_rows(stats_by_sv)
    if not rows_to_append:
        return

    if is_gcs:
        with bigquery_differ._open_text_stream(summary_report_path,
                                               "r") as in_f:
            existing_rows = list(csv.reader(in_f))
        header = existing_rows[0] if existing_rows else []
        existing_body = existing_rows[1:] if len(existing_rows) > 1 else []
        new_sv_set = {r[0] for r in rows_to_append}
        kept_body = [
            r for r in existing_body if not r or r[0] not in new_sv_set
        ]
        with bigquery_differ._open_text_stream(summary_report_path,
                                               "w") as out_f:
            writer = csv.writer(out_f)
            if header:
                writer.writerow(header)
            writer.writerows(kept_body)
            writer.writerows(rows_to_append)
    else:
        with open(summary_report_path, "r", encoding="utf-8",
                  newline="") as in_f:
            existing_rows = list(csv.reader(in_f))
        header = existing_rows[0] if existing_rows else []
        existing_body = existing_rows[1:] if len(existing_rows) > 1 else []
        new_sv_set = {r[0] for r in rows_to_append}
        if any(r and r[0] in new_sv_set for r in existing_body):
            kept_body = [
                r for r in existing_body if not r or r[0] not in new_sv_set
            ]
            with open(summary_report_path, "w", encoding="utf-8",
                      newline="") as out_f:
                writer = csv.writer(out_f)
                if header:
                    writer.writerow(header)
                writer.writerows(kept_body)
                writer.writerows(rows_to_append)
        else:
            with open(summary_report_path, "a", encoding="utf-8",
                      newline="") as csv_f:
                writer = csv.writer(csv_f)
                writer.writerows(rows_to_append)


def _sql_escape(val: str) -> str:
    """Escapes single quotes and backslashes for SQL string literals."""
    return val.replace("\\", "\\\\").replace("'", "\\'")


def _flatten_rules_rows(
    expanded_rules: Sequence[Dict[str, Any]],
) -> List[Tuple[int, str, str, int, bool, str]]:
    """Flattens expanded rules into (rule_id, ancestor_sv_id, source_sv_id, expected_count, skip_check, agg_method)."""
    rows: List[Tuple[int, str, str, int, bool, str]] = []
    for idx, rule in enumerate(expanded_rules):
        anc = str(rule["ancestor_sv_id"])
        sources = list(dict.fromkeys(str(s) for s in rule["source_sv_ids"]))
        expected_count = len(sources)
        skip_check = bool(rule.get("skip_all_sources_present_check", False))
        agg_method = str(rule.get("aggregation_method", "SUM")).upper()
        if agg_method not in ALLOWED_AGG_METHODS:
            raise ValueError(f"Invalid aggregation_method: {agg_method}")
        for src in sources:
            rows.append((idx, anc, src, expected_count, skip_check, agg_method))
    return rows


def build_bigquery_agg_obs_sql(
    raw_obs_table: str,
    agg_obs_table: str,
    expanded_rules: Sequence[Dict[str, Any]],
) -> str:
    """Builds the BigQuery CREATE OR REPLACE TABLE agg_obs SQL query matching OBS_BQ_SCHEMA."""
    rule_rows = _flatten_rules_rows(expanded_rules)
    if not rule_rows:
        raise ValueError("expanded_rules must not be empty")

    struct_literals = []
    for idx, anc, src, expected_count, skip_check, agg_method in rule_rows:
        skip_literal = "TRUE" if skip_check else "FALSE"
        struct_literals.append(f"STRUCT({idx} AS rule_id, "
                               f"'{_sql_escape(anc)}' AS ancestor_sv_id, "
                               f"'{_sql_escape(src)}' AS source_sv_id, "
                               f"{expected_count} AS expected_source_count, "
                               f"{skip_literal} AS skip_check, "
                               f"'{_sql_escape(agg_method)}' AS agg_method)")
    rules_cte = "SELECT * FROM UNNEST([\n            " + ",\n            ".join(
        struct_literals) + "\n        ])"
    key_combined_expr = bigquery_differ.format_key_combined_sql(
        var_expr="sv_id",
        about_expr="observationAbout",
        date_expr="observationDate",
        period_expr="observationPeriod",
        method_expr="measurementMethod",
        unit_expr="unit",
        scaling_expr="scalingFactor",
    )

    return f"""
    CREATE OR REPLACE TABLE `{agg_obs_table}` AS
    WITH rules_table AS (
        {rules_cte}
    ),
    dedup_obs AS (
        SELECT
            REGEXP_REPLACE(variableMeasured, r'^(dcid|dcs|schema):', '') AS sv_id,
            COALESCE(observationAbout, '') AS observationAbout,
            COALESCE(observationDate, '') AS observationDate,
            COALESCE(observationPeriod, '') AS observationPeriod,
            COALESCE(unit, '') AS unit,
            COALESCE(measurementMethod, '') AS origMeasurementMethod,
            COALESCE(scalingFactor, '') AS scalingFactor,
            ARRAY_AGG(SAFE_CAST(value AS FLOAT64) ORDER BY row_num DESC LIMIT 1)[OFFSET(0)] AS value
        FROM `{raw_obs_table}`
        WHERE SAFE_CAST(value AS FLOAT64) IS NOT NULL
          AND REGEXP_REPLACE(variableMeasured, r'^(dcid|dcs|schema):', '') IN (
              SELECT DISTINCT source_sv_id FROM rules_table
          )
        GROUP BY
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            unit,
            origMeasurementMethod,
            scalingFactor
    ),
    grouped AS (
        SELECT
            r.rule_id,
            r.ancestor_sv_id AS sv_id,
            o.observationAbout,
            o.observationDate,
            o.observationPeriod,
            o.unit,
            o.origMeasurementMethod,
            o.scalingFactor,
            r.agg_method,
            r.skip_check,
            r.expected_source_count,
            COUNT(DISTINCT o.sv_id) AS present_source_count,
            SUM(o.value) AS sum_val,
            MIN(o.value) AS min_val,
            MAX(o.value) AS max_val,
            AVG(o.value) AS avg_val
        FROM dedup_obs o
        INNER JOIN rules_table r
            ON o.sv_id = r.source_sv_id
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
        HAVING r.skip_check OR COUNT(DISTINCT o.sv_id) = r.expected_source_count
    ),
    computed AS (
        SELECT
            rule_id,
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            unit,
            origMeasurementMethod,
            CASE
                WHEN origMeasurementMethod = '' THEN 'DataCommonsAggregate'
                WHEN origMeasurementMethod = 'DataCommonsAggregate' THEN 'DataCommonsAggregate'
                WHEN origMeasurementMethod LIKE 'dcAggregate/%' THEN origMeasurementMethod
                ELSE CONCAT('dcAggregate/', origMeasurementMethod)
            END AS measurementMethod,
            scalingFactor,
            CASE agg_method
                WHEN 'SUM' THEN sum_val
                WHEN 'MIN' THEN min_val
                WHEN 'MAX' THEN max_val
                WHEN 'AVG' THEN avg_val
                ELSE sum_val
            END AS raw_val
        FROM grouped
    ),
    formatted AS (
        SELECT
            rule_id,
            sv_id,
            CONCAT('dcid:', sv_id) AS variableMeasured,
            CASE
                WHEN raw_val = ROUND(raw_val) AND ABS(raw_val) < 1e16
                    THEN CAST(CAST(ROUND(raw_val) AS INT64) AS STRING)
                ELSE REGEXP_REPLACE(REGEXP_REPLACE(FORMAT('%.10f', raw_val), r'0+$', ''), r'\\.$', '')
            END AS value,
            observationAbout,
            observationDate,
            observationPeriod,
            origMeasurementMethod,
            measurementMethod,
            unit,
            scalingFactor,
            ROW_NUMBER() OVER (
                ORDER BY
                    rule_id,
                    sv_id,
                    observationAbout,
                    observationDate,
                    origMeasurementMethod,
                    observationPeriod,
                    unit,
                    scalingFactor
            ) AS row_num
        FROM computed
    )
    SELECT
        {key_combined_expr} AS key_combined,
        variableMeasured,
        value,
        observationAbout,
        observationDate,
        observationPeriod,
        measurementMethod,
        unit,
        scalingFactor,
        row_num
    FROM formatted
    ORDER BY row_num
    """


def _extract_row_fields(
        row: Any) -> Tuple[str, str, str, str, str, str, str, str]:
    """Extracts (variableMeasured, value, observationAbout, observationDate, observationPeriod, measurementMethod, unit, scalingFactor) from a DB row."""
    if isinstance(row, Mapping):
        var_m = row.get("variableMeasured", "")
        val = row.get("value", "")
        about = row.get("observationAbout", "")
        date = row.get("observationDate", "")
        period = row.get("observationPeriod", "")
        method = row.get("measurementMethod", "")
        unit = row.get("unit", "")
        scaling = row.get("scalingFactor", "")
    elif hasattr(row, "variableMeasured"):
        var_m = getattr(row, "variableMeasured", "")
        val = getattr(row, "value", "")
        about = getattr(row, "observationAbout", "")
        date = getattr(row, "observationDate", "")
        period = getattr(row, "observationPeriod", "")
        method = getattr(row, "measurementMethod", "")
        unit = getattr(row, "unit", "")
        scaling = getattr(row, "scalingFactor", "")
    else:
        var_m, val, about, date, period, method, unit, scaling = row[:8]

    sv = _strip_mcf_value(var_m)
    val_str = format_numeric_value(val)
    return (
        sv,
        val_str,
        _strip_mcf_value(about),
        _strip_mcf_value(date),
        _strip_mcf_value(period),
        _strip_mcf_value(method),
        _strip_mcf_value(unit),
        _strip_mcf_value(scaling),
    )


def _stream_chunks_to_mcf_and_summary(
    chunks: Iterable[Iterable[Any]],
    output_mcf_path: str,
    summary_report_path: Optional[str] = None,
) -> int:
    """Streams chunks/pages of aggregated rows to stat_var_agg_nodes.mcf and summary_report.csv in O(1) memory."""
    total_written = 0
    stats_by_sv: Dict[str, _StatVarSummaryStats] = {}

    with contextlib.ExitStack() as stack:
        out_stream = None
        for chunk in chunks:
            for row in chunk:
                sv, val_str, about, date, period, method, unit, scaling = (
                    _extract_row_fields(row))
                if not (sv and about and date and val_str):
                    continue
                if out_stream is None:
                    out_stream = stack.enter_context(
                        bigquery_differ._open_text_stream(output_mcf_path, "w"))
                dcid = compute_observation_dcid(
                    variable_measured=sv,
                    observation_about=about,
                    observation_date=date,
                    value_str=val_str,
                    observation_period=period,
                    measurement_method=method,
                    unit=unit,
                    scaling_factor=scaling,
                )
                node_lines = _format_mcf_node_lines(
                    dcid=dcid,
                    variable_measured=sv,
                    observation_about=about,
                    observation_date=date,
                    value_str=val_str,
                    observation_period=period,
                    measurement_method=method,
                    unit=unit,
                    scaling_factor=scaling,
                )
                if total_written > 0:
                    out_stream.write("\n")
                out_stream.write("\n".join(node_lines))
                total_written += 1

                try:
                    numeric_val: Optional[float] = float(val_str)
                except ValueError:
                    numeric_val = None
                stats_by_sv.setdefault(sv, _StatVarSummaryStats()).add(
                    obs_about=about,
                    obs_date=date,
                    numeric_val=numeric_val,
                    m_method=method,
                    unit=unit,
                    scaling_factor=scaling,
                    obs_period=period,
                )

    if total_written > 0 and summary_report_path:
        update_summary_report_csv(summary_report_path, stats_by_sv)

    return total_written


def _iter_bq_result_pages(row_iter: Any) -> Iterator[Iterable[Any]]:
    """Yields pages of rows from a BigQuery RowIterator (or mock result)."""
    pages = getattr(row_iter, "pages", None)
    if pages is not None:
        try:
            yielded_any = False
            for page in pages:
                yielded_any = True
                yield page
            if yielded_any:
                return
        except TypeError:
            pass
    yield row_iter


def run_bigquery_aggregation(
    mcf_pattern: str,
    aggregations: Sequence[Dict[str, Any]],
    output_mcf_path: str,
    project_id: str,
    dataset_id: str = "datcom_import_differ",
    import_name: str = "import",
    version: str = "v0",
    input_prefix: str = "input0",
    summary_report_path: Optional[str] = None,
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
    bq_client: Optional[bigquery.Client] = None,
    page_size: int = 10000,
) -> Dict[str, Any]:
    """Executes StatVar aggregation in BigQuery (raw_obs -> agg_obs -> streaming MCF)."""
    expanded_rules = expand_stat_var_aggregation_config(aggregations)
    if not expanded_rules:
        return {
            "raw_obs_count": 0,
            "raw_schema_count": 0,
            "agg_obs_count": 0,
            "output_mcf_path": None,
            "table_ids": {},
        }

    if not project_id:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get(
            "PROJECT_ID", "")

    client = bq_client or bigquery.Client(project=project_id or None)
    effective_project = project_id or getattr(client, "project",
                                              "") or "default"
    dataset_ref = f"{effective_project}.{dataset_id}"
    bigquery_differ.ensure_bq_dataset(client,
                                      dataset_ref,
                                      expiration_hours=expiration_hours)

    table_ids = bigquery_differ.get_import_bq_table_ids(
        dataset_ref=dataset_ref,
        import_name=import_name,
        version=version,
        input_prefix=input_prefix,
    )
    raw_obs_table = table_ids["raw_obs"]
    raw_schema_table = table_ids["raw_schema"]
    agg_obs_table = table_ids["agg_obs"]

    logging.info(
        "Step 1/3: Streaming MCFs (%s) into BigQuery %s and %s...",
        mcf_pattern,
        raw_obs_table,
        raw_schema_table,
    )
    raw_obs_count, raw_schema_count = bigquery_differ.load_mcf_to_bq_tables(
        bq_client=client,
        mcf_pattern=mcf_pattern,
        obs_table_ref=raw_obs_table,
        schema_table_ref=raw_schema_table,
        temp_dir=gcs_temp_dir,
        suffix=f"raw_{import_name}_{input_prefix}",
        expiration_hours=expiration_hours,
        exclude_filenames={
            STAT_VAR_AGG_MCF_FILENAME,
            STAT_VAR_SERIES_AGG_MCF_FILENAME,
        },
    )
    if raw_obs_count == 0:
        logging.info(
            "No raw observations found in %s; skipping agg_obs creation.",
            mcf_pattern,
        )
        return {
            "raw_obs_count": 0,
            "raw_schema_count": raw_schema_count,
            "agg_obs_count": 0,
            "output_mcf_path": None,
            "table_ids": table_ids,
        }

    logging.info(
        "Step 2/3: Computing StatVar aggregations into BigQuery table %s...",
        agg_obs_table,
    )
    create_agg_sql = build_bigquery_agg_obs_sql(
        raw_obs_table=raw_obs_table,
        agg_obs_table=agg_obs_table,
        expanded_rules=expanded_rules,
    )
    client.query(create_agg_sql).result()

    agg_table = client.get_table(agg_obs_table)
    agg_table.expires = datetime.now(
        timezone.utc) + timedelta(hours=expiration_hours)
    client.update_table(agg_table, ["expires"])

    logging.info(
        "Step 3/3: Streaming agg_obs (%s) in %d-row pages to %s...",
        agg_obs_table,
        page_size,
        output_mcf_path,
    )
    select_agg_sql = f"""
    SELECT
        variableMeasured,
        value,
        observationAbout,
        observationDate,
        observationPeriod,
        measurementMethod,
        unit,
        scalingFactor
    FROM `{agg_obs_table}`
    ORDER BY row_num
    """
    row_iter = client.query(select_agg_sql).result(page_size=page_size)
    agg_obs_count = _stream_chunks_to_mcf_and_summary(
        chunks=_iter_bq_result_pages(row_iter),
        output_mcf_path=output_mcf_path,
        summary_report_path=summary_report_path,
    )

    return {
        "raw_obs_count": raw_obs_count,
        "raw_schema_count": raw_schema_count,
        "agg_obs_count": agg_obs_count,
        "output_mcf_path": output_mcf_path if agg_obs_count > 0 else None,
        "table_ids": table_ids,
    }


def run_stat_var_aggregation_for_genmcf(
    import_name: str,
    genmcf_output_path: str,
    config_path: Optional[str] = None,
    import_spec: Optional[Dict[str, Any]] = None,
    bigquery_project_id: Optional[str] = None,
    bigquery_dataset_id: str = "datcom_import_differ",
    version: str = "v0",
    input_prefix: str = "input0",
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
    bq_client: Optional[bigquery.Client] = None,
) -> Optional[str]:
    """Runs ET-layer StatVar aggregation for a genmcf output directory (local or gs://)."""
    rules = load_stat_var_aggregation_config(
        import_name=import_name,
        config_path=config_path,
        import_spec=import_spec,
    )
    if not rules:
        return None

    is_gcs = file_util.file_is_gcs(genmcf_output_path)
    base_dir = genmcf_output_path.rstrip("/")
    mcf_pattern = f"{base_dir}/*.mcf" if is_gcs else os.path.join(
        base_dir, "*.mcf")
    output_mcf_path = (f"{base_dir}/{STAT_VAR_AGG_MCF_FILENAME}" if is_gcs else
                       os.path.join(base_dir, STAT_VAR_AGG_MCF_FILENAME))
    summary_csv_path = (f"{base_dir}/summary_report.csv" if is_gcs else
                        os.path.join(base_dir, "summary_report.csv"))

    if not is_gcs and not os.path.exists(genmcf_output_path):
        logging.warning(
            "genmcf output path %s does not exist for %s",
            genmcf_output_path,
            import_name,
        )
        return None

    res = run_bigquery_aggregation(
        mcf_pattern=mcf_pattern,
        aggregations=rules,
        output_mcf_path=output_mcf_path,
        project_id=bigquery_project_id or "",
        dataset_id=bigquery_dataset_id,
        import_name=import_name,
        version=version,
        input_prefix=input_prefix,
        summary_report_path=summary_csv_path,
        gcs_temp_dir=gcs_temp_dir,
        expiration_hours=expiration_hours,
        bq_client=bq_client,
    )

    return res.get("output_mcf_path")
