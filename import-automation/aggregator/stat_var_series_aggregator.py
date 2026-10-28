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
"""ET-layer StatVar series aggregation runner (BigQuery).

Implements multi-round time-series and multi-model ensemble StatVarObservation
aggregations (modeled on google3/datacommons/prophet/derived_graph/
stat_var_series_aggregation/processor.cc with clean calendar windows):
1. Compiles all configured rounds (Round 1 -> Round 2 -> Round 3) for a single
   import into one BigQuery SQL query using chained CTEs.
2. Supports all 5 series aggregation functions:
   - max_diff_across_measurement_methods
   - diff_relative_to_base_date (discrete earliest-year fallback & year range)
   - stats_across_models (exact nearest-rank 10th, Median, 90th percentiles)
   - aggr_over_time (clean calendar windows, first-matching sv_config)
   - count_threshold_exception_over_time (clean calendar windows, count > 0)
3. Preserves 15 significant digits (%.15g) so small scientific climate values
   (e.g. PrecipitationRate ~1e-6) are never truncated to 0.
4. Emits StatVarObservation MCF nodes only (genmcf/stat_var_series_agg_nodes.mcf)
   and updates summary_report.csv in O(1) streaming memory.
"""

import contextlib
from datetime import datetime, timedelta, timezone
import logging
import math
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from google.cloud import bigquery
from omegaconf import OmegaConf

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = (_SCRIPT_DIR if os.path.exists(os.path.join(_SCRIPT_DIR, "tools"))
             else os.path.dirname(os.path.dirname(_SCRIPT_DIR)))

for _p in [
        _SCRIPT_DIR,
        _ROOT_DIR,
        os.path.join(_ROOT_DIR, "util"),
        os.path.join(_ROOT_DIR, "tools", "import_differ"),
        os.path.join(_ROOT_DIR, "tools", "statvar_importer"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import file_util
import stat_var_aggregator
from tools.import_differ import bigquery_differ

DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR,
                                   "statvar_series_aggregation.yaml")

STAT_VAR_SERIES_AGG_MCF_FILENAME = "stat_var_series_agg_nodes.mcf"

DEFAULT_EXCLUDE_FILENAMES = frozenset({
    "stat_var_agg_nodes.mcf",
    STAT_VAR_SERIES_AGG_MCF_FILENAME,
    "instance_mcf_nodes.mcf",
    "failed_instance_mcf_nodes.mcf",
})

ALLOWED_SERIES_FUNC_TYPES = frozenset({
    "max_diff_across_measurement_methods",
    "diff_relative_to_base_date",
    "stats_across_models",
    "aggr_over_time",
    "count_threshold_exception_over_time",
})

ALLOWED_SERIES_AGG_OPS = frozenset({"MAX", "MIN", "MEAN", "SUM"})
ALLOWED_SERIES_COMPARISONS = frozenset({"GE", "LE"})

_BQ_TABLE_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_/\-]+$")
_YEAR_OR_MONTH_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?$")
_OUTPUT_PERIOD_RE = re.compile(r"^P([1-9][0-9]*)([YM])$")
_AOT_INPUT_PERIOD_RE = re.compile(r"^P1[MY]$")
_THRESHOLD_INPUT_PERIOD_RE = re.compile(r"^P1[MD]$")
_UNSUPPORTED_RE2_CONSTRUCT_RE = re.compile(r"\(\?(?:!|=|<=|<!|>|P<|P=)|\\[1-9]")
_NEG_CHAR_LOOP_RE = re.compile(r"^(.*?)(\((?:\?:)?\(\?!([^()]+)\)\.\)\*)(.*)$")
_LEADING_NEG_LOOKAHEAD_RE = re.compile(r"^\(\?!([^()]+)\)(.+)$")

# Re-export shared observation helpers from stat_var_aggregator.
compute_observation_dcid = stat_var_aggregator.compute_observation_dcid
parse_mcf_observations = stat_var_aggregator.parse_mcf_observations
update_summary_report_csv = stat_var_aggregator.update_summary_report_csv


def format_numeric_value(val: Union[float, int, str, None]) -> str:
    """Formats a numeric observation value with up to 15 significant digits (%.15g).

    Preserves clean integer strings when fval.is_integer() and abs(fval) < 1e16,
    avoids '-0', and preserves small scientific values (e.g. 1.25e-06) identically
    to BigQuery SQL formatting.
    """
    if val is None or val == "" or isinstance(val, bool):
        return ""
    if isinstance(val, str) and not val.strip():
        return ""
    try:
        fval = float(val)
    except (ValueError, TypeError):
        return str(val)
    if math.isnan(fval) or math.isinf(fval):
        return ""
    if fval == 0.0:
        return "0"
    if fval.is_integer() and abs(fval) < 1e16:
        return str(int(round(fval)))
    formatted = f"{fval:.15g}"
    return "0" if formatted in ("", "-0") else formatted


def write_mcf_observations(records: Sequence[Mapping[str, Any]],
                           output_mcf_path: str) -> None:
    """Writes StatVarObservation records to a .mcf file using 15-sig-fig formatting."""
    prepared_records: List[Dict[str, Any]] = []
    for rec in records:
        rec_copy = dict(rec)
        if not rec_copy.get("valueStr"):
            rec_copy["valueStr"] = format_numeric_value(rec_copy.get("value"))
        prepared_records.append(rec_copy)
    stat_var_aggregator.write_mcf_observations(prepared_records,
                                               output_mcf_path)


def _validate_bq_table_id(table_id: str, param_name: str) -> str:
    """Validates a BigQuery table identifier against SQL injection."""
    if not isinstance(table_id, str) or not table_id.strip():
        raise ValueError(f"{param_name} must be a non-empty string.")
    cleaned = table_id.strip()
    if not _BQ_TABLE_ID_RE.match(cleaned) or "--" in cleaned:
        raise ValueError(
            f"Invalid BigQuery table identifier for {param_name}: {table_id!r}")
    return cleaned


def _validate_safe_token(val: Any,
                         field_name: str,
                         allow_empty: bool = False) -> str:
    """Validates a unit, prefix, or property identifier for SQL safety."""
    if val is None:
        val = ""
    if not isinstance(val, str):
        raise ValueError(
            f"{field_name} must be a string, got {type(val).__name__}.")
    cleaned = val.strip()
    if not cleaned:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} must be a non-empty string.")
    if not _SAFE_TOKEN_RE.match(cleaned) or "--" in cleaned:
        raise ValueError(
            f"Invalid characters in {field_name}: {val!r}. "
            "Only alphanumeric, '_', '/', and single '-' characters are allowed."
        )
    return cleaned


def _validate_year_or_month_date(date_val: Any, field_name: str) -> str:
    """Validates a 'YYYY' or 'YYYY-MM' date string."""
    if not isinstance(date_val, str):
        raise ValueError(
            f"{field_name} must be a 'YYYY' or 'YYYY-MM' string, got {date_val!r}."
        )
    cleaned = date_val.strip()
    m = _YEAR_OR_MONTH_DATE_RE.match(cleaned)
    if not m:
        raise ValueError(f"Invalid date format for {field_name}: {date_val!r} "
                         "(expected 'YYYY' or 'YYYY-MM').")
    if m.group(2) is not None:
        month_num = int(m.group(2))
        if month_num < 1 or month_num > 12:
            raise ValueError(
                f"Month out of range in {field_name}: {date_val!r}.")
    return cleaned


def _date_sort_tuple(date_str: str) -> Tuple[int, int]:
    """Converts a validated 'YYYY' or 'YYYY-MM' string into a comparable (year, month) tuple."""
    year = int(date_str[:4])
    month = int(date_str[5:7]) if len(date_str) == 7 else 1
    return (year, month)


def _to_non_capturing_re2(pattern: str) -> str:
    """Converts unescaped capturing groups '(...)' into non-capturing '(?:...)'."""
    out: List[str] = []
    i = 0
    n = len(pattern)
    in_char_class = False
    while i < n:
        ch = pattern[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError(f"Trailing backslash in regex: {pattern!r}")
            out.append(pattern[i:i + 2])
            i += 2
            continue
        if in_char_class:
            if ch == "]":
                in_char_class = False
            out.append(ch)
            i += 1
            continue
        if ch == "[":
            in_char_class = True
            out.append(ch)
            i += 1
            if i < n and pattern[i] == "^":
                out.append(pattern[i])
                i += 1
            if i < n and pattern[i] == "]":
                out.append(pattern[i])
                i += 1
            continue
        if ch == "(":
            if i + 1 < n and pattern[i + 1] == "?":
                out.append("(")
            else:
                out.append("(?:")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _strip_outer_anchors(pattern: str) -> str:
    """Strips outer '^' and unescaped '$' when there is no top-level alternation."""
    depth = 0
    in_char_class = False
    has_top_level_alt = False
    i = 0
    n = len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == "\\":
            i += 2
            continue
        if in_char_class:
            if ch == "]":
                in_char_class = False
            i += 1
            continue
        if ch == "[":
            in_char_class = True
            i += 1
            if i < n and pattern[i] == "^":
                i += 1
            if i < n and pattern[i] == "]":
                i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
        elif ch == "|" and depth == 0:
            has_top_level_alt = True
            break
        i += 1

    if has_top_level_alt:
        return pattern

    stripped = pattern
    if stripped.startswith("^"):
        stripped = stripped[1:]
    if stripped.endswith("$"):
        bs_count = 0
        j = len(stripped) - 2
        while j >= 0 and stripped[j] == "\\":
            bs_count += 1
            j -= 1
        if bs_count % 2 == 0:
            stripped = stripped[:-1]
    return stripped


def _validate_pure_re2_fragment(fragment: str, orig_regex: str) -> str:
    """Validates that a regex fragment is safe and compatible with BigQuery RE2."""
    if _UNSUPPORTED_RE2_CONSTRUCT_RE.search(fragment):
        raise ValueError(
            f"sv_regex {orig_regex!r} contains unsupported RE2 construct in {fragment!r}."
        )
    try:
        re.compile(fragment)
    except re.error as exc:
        raise ValueError(f"Invalid sv_regex {orig_regex!r}: {exc}") from exc
    return fragment


def _compile_sv_regex_to_bq_sql(sv_expr: str, raw_regex: Any) -> str:
    """Validates sv_regex and compiles a full-match predicate safe for BigQuery RE2.

    Decomposes Perl-style negative lookahead idioms such as
    '((?!Max|Min).)*DifferenceRelativeToBaseDate.*_Temperature.*' into pure RE2
    REGEXP_CONTAINS / REGEXP_EXTRACT expressions so BigQuery RE2 never sees '(?!...)'.
    """
    if not isinstance(raw_regex, str) or not raw_regex.strip():
        raise ValueError("sv_regex must be a non-empty string.")
    if any(ord(ch) < 32 for ch in raw_regex):
        raise ValueError(
            f"sv_regex must not contain control characters: {raw_regex!r}")
    if any(q in raw_regex for q in ("'", '"', "`")):
        raise ValueError(
            f"sv_regex must not contain quote characters: {raw_regex!r}")
    try:
        re.compile(raw_regex)
    except re.error as exc:
        raise ValueError(f"Invalid sv_regex {raw_regex!r}: {exc}") from exc

    body = _strip_outer_anchors(raw_regex.strip())

    # Idiom 1: <prefix>((?!<neg>).)*<suffix> or <prefix>(?:(?!<neg>).)*<suffix>
    m_loop = _NEG_CHAR_LOOP_RE.match(body)
    if m_loop:
        prefix_raw, _, neg_raw, suffix_raw = m_loop.groups()
        prefix_nc = _validate_pure_re2_fragment(
            _to_non_capturing_re2(prefix_raw), raw_regex)
        neg_nc = _validate_pure_re2_fragment(_to_non_capturing_re2(neg_raw),
                                             raw_regex)
        suffix_nc = _validate_pure_re2_fragment(
            _to_non_capturing_re2(suffix_raw), raw_regex)
        full_pat = f"^{prefix_nc}(?:.*){suffix_nc}$"
        extract_pat = f"^{prefix_nc}(.*?){suffix_nc}$"
        _validate_pure_re2_fragment(full_pat, raw_regex)
        if re.compile(extract_pat).groups != 1:
            raise ValueError(
                f"Failed to isolate single capture group for sv_regex: {raw_regex!r}"
            )
        return (f"(REGEXP_CONTAINS({sv_expr}, r'{full_pat}') "
                f"AND NOT REGEXP_CONTAINS("
                f"IFNULL(REGEXP_EXTRACT({sv_expr}, r'{extract_pat}'), ''), "
                f"r'(?:{neg_nc})'))")

    # Idiom 2: ^(?!<neg>)<rest>
    m_lead = _LEADING_NEG_LOOKAHEAD_RE.match(body)
    if m_lead:
        neg_raw, rest_raw = m_lead.groups()
        neg_nc = _validate_pure_re2_fragment(_to_non_capturing_re2(neg_raw),
                                             raw_regex)
        rest_nc = _validate_pure_re2_fragment(_to_non_capturing_re2(rest_raw),
                                              raw_regex)
        return (f"(REGEXP_CONTAINS({sv_expr}, r'^(?:{rest_nc})$') "
                f"AND NOT REGEXP_CONTAINS({sv_expr}, r'^(?:{neg_nc})'))")

    body_nc = _validate_pure_re2_fragment(_to_non_capturing_re2(body),
                                          raw_regex)
    return f"REGEXP_CONTAINS({sv_expr}, r'^(?:{body_nc})$')"


def _normalize_aggregation_op(raw_op: Any) -> str:
    """Validates and normalizes aggregation_op ('MAX', 'MIN', 'MEAN', 'SUM')."""
    if not isinstance(raw_op, str) or not raw_op.strip():
        raise ValueError(
            f"aggregation_op must be a non-empty string, got {raw_op!r}.")
    op = raw_op.strip().upper()
    if op.startswith("OPERATOR_"):
        op = op[len("OPERATOR_"):]
    if op not in ALLOWED_SERIES_AGG_OPS:
        raise ValueError(f"Unsupported aggregation_op {raw_op!r}. "
                         f"Allowed: {sorted(ALLOWED_SERIES_AGG_OPS)}")
    return op


def _normalize_comparison_op(raw_comp: Any) -> str:
    """Validates and normalizes comparison ('GE', 'LE')."""
    if not isinstance(raw_comp, str) or not raw_comp.strip():
        raise ValueError(
            f"comparison must be a non-empty string, got {raw_comp!r}.")
    comp = raw_comp.strip().upper()
    if comp.startswith("OPERATOR_"):
        comp = comp[len("OPERATOR_"):]
    if comp not in ALLOWED_SERIES_COMPARISONS:
        raise ValueError(f"Unsupported comparison {raw_comp!r}. "
                         f"Allowed: {sorted(ALLOWED_SERIES_COMPARISONS)}")
    return comp


def _validate_time_range(
    raw_time_range: Any,
    input_period_re: re.Pattern[str],
    func_type: str,
) -> Dict[str, str]:
    """Validates a time_range mapping for aggr_over_time or count_threshold_exception_over_time."""
    if not isinstance(raw_time_range, Mapping):
        raise ValueError(f"{func_type}.time_range must be a mapping.")
    in_period = raw_time_range.get("input_obs_period")
    out_period = raw_time_range.get("output_obs_period")
    out_date = raw_time_range.get("output_obs_date")

    if not isinstance(in_period, str) or not input_period_re.match(
            in_period.strip()):
        raise ValueError(
            f"Unsupported input_obs_period {in_period!r} for {func_type}.")
    if not isinstance(out_period, str) or not _OUTPUT_PERIOD_RE.match(
            out_period.strip()):
        raise ValueError(
            f"Unsupported output_obs_period {out_period!r} for {func_type} "
            "(expected ^P[1-9][0-9]*[YM]$).")
    validated_date = _validate_year_or_month_date(
        out_date, f"{func_type}.time_range.output_obs_date")

    return {
        "input_obs_period": in_period.strip(),
        "output_obs_period": out_period.strip(),
        "output_obs_date": validated_date,
    }


def _unwrap_aggr_func(raw_func: Any) -> Tuple[str, Mapping[str, Any]]:
    """Extracts (func_type, func_body) from either {'type': ...} or single-key proto dict."""
    if not isinstance(raw_func, Mapping):
        raise ValueError(f"Each aggr_func must be a mapping, got {raw_func!r}.")
    func_type = raw_func.get("type")
    if isinstance(func_type, str) and func_type.strip():
        return func_type.strip(), raw_func
    if "type" not in raw_func and len(raw_func) == 1:
        only_key, inner = next(iter(raw_func.items()))
        if isinstance(only_key, str):
            if inner is None:
                return only_key.strip(), {}
            if isinstance(inner, Mapping):
                return only_key.strip(), inner
    raise ValueError(f"Missing or invalid 'type' in aggr_func: {raw_func!r}")


def validate_stat_var_series_config(
    rounds: Sequence[Mapping[str, Any]],) -> List[Dict[str, Any]]:
    """Strictly validates and normalizes StatVar series aggregation rounds."""
    if not isinstance(rounds, Sequence) or isinstance(rounds, (str, bytes)):
        raise ValueError("rounds must be a sequence of round mappings.")
    if not rounds:
        return []

    normalized_rounds: List[Dict[str, Any]] = []
    for idx, raw_round in enumerate(rounds):
        expected_round_num = idx + 1
        if not isinstance(raw_round, Mapping):
            raise ValueError(f"Round entry at index {idx} must be a mapping.")
        round_num = raw_round.get("round")
        if (isinstance(round_num, bool) or not isinstance(round_num, int) or
                round_num != expected_round_num):
            raise ValueError(
                f"Rounds must have sequential positive integer 'round' values "
                f"(expected {expected_round_num}, got {round_num!r}).")

        raw_funcs = raw_round.get("aggr_funcs")
        if (not isinstance(raw_funcs, Sequence) or
                isinstance(raw_funcs, (str, bytes)) or not raw_funcs):
            raise ValueError(
                f"Round {round_num} must have a non-empty 'aggr_funcs' list.")

        normalized_funcs: List[Dict[str, Any]] = []
        for raw_func in raw_funcs:
            func_type, func_body = _unwrap_aggr_func(raw_func)
            if func_type not in ALLOWED_SERIES_FUNC_TYPES:
                raise ValueError(
                    f"Unsupported series aggregation type {func_type!r}. "
                    f"Allowed: {sorted(ALLOWED_SERIES_FUNC_TYPES)}")

            if func_type == "max_diff_across_measurement_methods":
                normalized_funcs.append({
                    "type": "max_diff_across_measurement_methods",
                })

            elif func_type == "diff_relative_to_base_date":
                raw_specs = func_body.get("date_specs")
                if (not isinstance(raw_specs, Sequence) or
                        isinstance(raw_specs, (str, bytes)) or not raw_specs):
                    raise ValueError(
                        "diff_relative_to_base_date requires a non-empty 'date_specs' list."
                    )
                norm_specs: List[Dict[str, Any]] = []
                for spec_idx, raw_spec in enumerate(raw_specs):
                    if not isinstance(raw_spec, Mapping):
                        raise ValueError(
                            f"date_specs[{spec_idx}] must be a mapping.")
                    has_start = raw_spec.get("start_date") is not None
                    has_end = raw_spec.get("end_date") is not None
                    if has_start != has_end:
                        raise ValueError(
                            "diff_relative_to_base_date date_spec must specify both "
                            "'start_date' and 'end_date' when using a range.")

                    norm_spec: Dict[str, Any] = {}
                    if has_start and has_end:
                        start_d = _validate_year_or_month_date(
                            raw_spec["start_date"], "start_date")
                        end_d = _validate_year_or_month_date(
                            raw_spec["end_date"], "end_date")
                        if _date_sort_tuple(start_d) > _date_sort_tuple(end_d):
                            raise ValueError(
                                f"start_date ({start_d!r}) must be <= end_date ({end_d!r})."
                            )
                        norm_spec["start_date"] = start_d
                        norm_spec["end_date"] = end_d

                    raw_dates = raw_spec.get("dates")
                    if raw_dates is not None:
                        if (not isinstance(raw_dates, Sequence) or
                                isinstance(raw_dates,
                                           (str, bytes)) or not raw_dates):
                            raise ValueError(
                                "date_spec.dates must be a non-empty list when provided."
                            )
                        validated_dates = [
                            _validate_year_or_month_date(d, "dates[]")
                            for d in raw_dates
                        ]
                        norm_spec["dates"] = sorted(
                            dict.fromkeys(validated_dates),
                            key=_date_sort_tuple,
                        )

                    if not norm_spec:
                        raise ValueError(
                            "diff_relative_to_base_date date_spec must define "
                            "'dates' or ('start_date', 'end_date').")
                    norm_specs.append(norm_spec)

                normalized_funcs.append({
                    "type": "diff_relative_to_base_date",
                    "date_specs": norm_specs,
                })

            elif func_type == "stats_across_models":
                norm_stats: Dict[str, Any] = {"type": "stats_across_models"}
                if func_body.get("sv_regex") is not None:
                    _compile_sv_regex_to_bq_sql("sv_id", func_body["sv_regex"])
                    norm_stats["sv_regex"] = func_body["sv_regex"].strip()
                normalized_funcs.append(norm_stats)

            elif func_type == "aggr_over_time":
                norm_tr = _validate_time_range(
                    func_body.get("time_range"),
                    _AOT_INPUT_PERIOD_RE,
                    "aggr_over_time",
                )
                raw_use_input_sv = func_body.get("use_input_sv_for_output",
                                                 False)
                if not isinstance(raw_use_input_sv, bool):
                    raise ValueError(
                        "aggr_over_time.use_input_sv_for_output must be a bool."
                    )
                default_prefix = _validate_safe_token(
                    func_body.get("output_sv_prefix", ""),
                    "aggr_over_time.output_sv_prefix",
                    allow_empty=True,
                )
                raw_num_periods = func_body.get("num_output_periods", 1)
                if (isinstance(raw_num_periods, bool) or
                        not isinstance(raw_num_periods, int) or
                        raw_num_periods < 1):
                    raise ValueError(
                        "aggr_over_time.num_output_periods must be a positive integer."
                    )
                raw_align_left = func_body.get("date_align_left", False)
                if not isinstance(raw_align_left, bool):
                    raise ValueError(
                        "aggr_over_time.date_align_left must be a bool.")

                raw_sv_configs = func_body.get("sv_configs")
                if (not isinstance(raw_sv_configs, Sequence) or
                        isinstance(raw_sv_configs,
                                   (str, bytes)) or not raw_sv_configs):
                    raise ValueError(
                        "aggr_over_time requires a non-empty 'sv_configs' list."
                    )

                norm_sv_configs: List[Dict[str, Any]] = []
                for svc_idx, raw_svc in enumerate(raw_sv_configs):
                    if not isinstance(raw_svc, Mapping):
                        raise ValueError(
                            f"aggr_over_time.sv_configs[{svc_idx}] must be a mapping."
                        )
                    sv_regex = raw_svc.get("sv_regex")
                    _compile_sv_regex_to_bq_sql("sv_id", sv_regex)
                    agg_op = _normalize_aggregation_op(
                        raw_svc.get("aggregation_op"))
                    unit = _validate_safe_token(
                        raw_svc.get("unit", ""),
                        "aggr_over_time.sv_configs.unit",
                        allow_empty=True,
                    )
                    svc_use_input = raw_svc.get("use_input_sv_for_output",
                                                raw_use_input_sv)
                    if not isinstance(svc_use_input, bool):
                        raise ValueError(
                            "sv_configs.use_input_sv_for_output must be a bool."
                        )
                    svc_prefix = _validate_safe_token(
                        raw_svc.get("output_sv_prefix", default_prefix),
                        "sv_configs.output_sv_prefix",
                        allow_empty=True,
                    )
                    norm_sv_configs.append({
                        "sv_regex": sv_regex.strip(),
                        "aggregation_op": agg_op,
                        "unit": unit,
                        "use_input_sv_for_output": svc_use_input,
                        "output_sv_prefix": svc_prefix,
                    })

                normalized_funcs.append({
                    "type": "aggr_over_time",
                    "time_range": norm_tr,
                    "use_input_sv_for_output": raw_use_input_sv,
                    "output_sv_prefix": default_prefix,
                    "num_output_periods": raw_num_periods,
                    "date_align_left": raw_align_left,
                    "sv_configs": norm_sv_configs,
                })

            elif func_type == "count_threshold_exception_over_time":
                norm_tr = _validate_time_range(
                    func_body.get("time_range"),
                    _THRESHOLD_INPUT_PERIOD_RE,
                    "count_threshold_exception_over_time",
                )
                raw_thresholds = func_body.get("thresholds")
                if (not isinstance(raw_thresholds, Sequence) or
                        isinstance(raw_thresholds,
                                   (str, bytes)) or not raw_thresholds):
                    raise ValueError(
                        "count_threshold_exception_over_time requires a non-empty 'thresholds' list."
                    )

                norm_thresholds: List[Dict[str, Any]] = []
                for thres_idx, raw_thres in enumerate(raw_thresholds):
                    if not isinstance(raw_thres, Mapping):
                        raise ValueError(
                            f"thresholds[{thres_idx}] must be a mapping.")
                    sv_regex = raw_thres.get("sv_regex")
                    _compile_sv_regex_to_bq_sql("sv_id", sv_regex)

                    raw_tval = raw_thres.get("threshold_value")
                    if isinstance(
                            raw_tval,
                            bool) or not isinstance(raw_tval, (int, float)):
                        raise ValueError(
                            f"threshold_value must be a finite number, got {raw_tval!r}."
                        )
                    tval = float(raw_tval)
                    if not math.isfinite(tval):
                        raise ValueError(
                            f"threshold_value must be finite, got {raw_tval!r}."
                        )

                    comp = _normalize_comparison_op(raw_thres.get("comparison"))
                    unit = _validate_safe_token(
                        raw_thres.get("unit"),
                        "count_threshold_exception_over_time.thresholds.unit",
                        allow_empty=False,
                    )
                    output_cprop = _validate_safe_token(
                        raw_thres.get("output_cprop", ""),
                        "count_threshold_exception_over_time.thresholds.output_cprop",
                        allow_empty=True,
                    )
                    norm_thresholds.append({
                        "sv_regex": sv_regex.strip(),
                        "threshold_value": tval,
                        "comparison": comp,
                        "unit": unit,
                        "output_cprop": output_cprop,
                    })

                normalized_funcs.append({
                    "type": "count_threshold_exception_over_time",
                    "time_range": norm_tr,
                    "thresholds": norm_thresholds,
                })

        normalized_rounds.append({
            "round": round_num,
            "aggr_funcs": normalized_funcs,
        })

    return normalized_rounds


def load_stat_var_series_aggregation_config(
    import_name: str,
    config_path: Optional[str] = None,
    import_spec: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Loads and validates StatVar series aggregation rounds for an import_name."""
    if import_spec and import_spec.get(
            "stat_var_series_aggregation") is not None:
        raw_override = import_spec["stat_var_series_aggregation"]
        if not raw_override:
            return []
        if isinstance(raw_override, Mapping):
            if "rounds" in raw_override:
                raw_rounds = raw_override["rounds"]
            elif "stat_var_series_aggregation" in raw_override:
                raw_rounds = raw_override["stat_var_series_aggregation"]
            else:
                raise ValueError(
                    "import_spec['stat_var_series_aggregation'] mapping must "
                    "contain 'rounds' or 'stat_var_series_aggregation'.")
        elif isinstance(raw_override,
                        Sequence) and not isinstance(raw_override,
                                                     (str, bytes)):
            raw_rounds = raw_override
        else:
            raise ValueError(
                "import_spec['stat_var_series_aggregation'] must be a list of "
                "rounds or a mapping.")
        if not raw_rounds:
            return []
        return validate_stat_var_series_config(raw_rounds)

    if not import_name or not str(import_name).strip():
        return []

    resolved_path = config_path or DEFAULT_CONFIG_PATH
    if not resolved_path or not os.path.exists(resolved_path):
        logging.debug("StatVar series aggregation config file not found at %s",
                      resolved_path)
        return []

    cfg = OmegaConf.load(resolved_path)
    cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    if not isinstance(cfg_dict, Mapping):
        return []

    imports_map = cfg_dict.get("imports", {})
    if not isinstance(imports_map, Mapping):
        raise ValueError(
            "Expected 'imports' mapping in statvar_series_aggregation config.")

    import_entry = imports_map.get(import_name)
    if not import_entry:
        return []

    if isinstance(import_entry,
                  Sequence) and not isinstance(import_entry, (str, bytes)):
        raw_rounds = import_entry
    elif isinstance(import_entry, Mapping):
        if "stat_var_series_aggregation" in import_entry:
            sub = import_entry["stat_var_series_aggregation"]
            if isinstance(sub, Mapping) and "rounds" in sub:
                raw_rounds = sub["rounds"]
            else:
                raw_rounds = sub
        elif "rounds" in import_entry:
            raw_rounds = import_entry["rounds"]
        else:
            return []
    else:
        raise ValueError(
            f"Invalid config entry for import {import_name!r} in {resolved_path}."
        )

    if not raw_rounds:
        return []
    return validate_stat_var_series_config(raw_rounds)


def _build_clean_window_sql_predicate(
    date_expr: str,
    output_obs_date: str,
    output_obs_period: str,
    date_align_left: bool = False,
) -> str:
    """Builds a clean calendar window predicate on ISO observationDate."""
    m = _OUTPUT_PERIOD_RE.match(output_obs_period)
    if not m:
        raise ValueError(f"Invalid output_obs_period: {output_obs_period!r}")
    amount = int(m.group(1))
    unit_char = m.group(2)

    iso_guard = f"REGEXP_CONTAINS({date_expr}, r'^\\d{{4}}(-(0[1-9]|1[0-2])(-\\d{{2}})?)?$')"

    if len(output_obs_date) == 4 and unit_char == "Y":
        end_year = int(output_obs_date) - (1 if date_align_left else 0)
        start_year = end_year - amount + 1
        return (
            f"{iso_guard} AND "
            f"CAST(SUBSTR({date_expr}, 1, 4) AS INT64) BETWEEN {start_year} AND {end_year}"
        )

    duration_months = amount * 12 if unit_char == "Y" else amount
    if len(output_obs_date) == 7:
        end_y = int(output_obs_date[:4])
        end_m = int(output_obs_date[5:7])
        end_month_idx = end_y * 12 + (end_m - 1) - (1 if date_align_left else 0)
    else:
        end_y = int(output_obs_date[:4]) - (1 if date_align_left else 0)
        end_month_idx = end_y * 12 + 11
    start_month_idx = end_month_idx - duration_months + 1

    obs_month_idx_expr = (
        f"(CAST(SUBSTR({date_expr}, 1, 4) AS INT64) * 12 + "
        f"IF(LENGTH({date_expr}) >= 7, CAST(SUBSTR({date_expr}, 6, 2) AS INT64), 1) - 1)"
    )
    return (
        f"{iso_guard} AND "
        f"{obs_month_idx_expr} BETWEEN {start_month_idx} AND {end_month_idx}")


def _compute_single_window_output_date(
    output_obs_date: str,
    output_obs_period: str,
    date_align_left: bool = False,
) -> str:
    """Computes the output observationDate string for a single window."""
    if not date_align_left:
        return output_obs_date
    m = _OUTPUT_PERIOD_RE.match(output_obs_period)
    if not m:
        raise ValueError(f"Invalid output_obs_period: {output_obs_period!r}")
    amount = int(m.group(1))
    unit_char = m.group(2)
    if len(output_obs_date) == 4 and unit_char == "Y":
        end_year = int(output_obs_date) - 1
        start_year = end_year - amount + 1
        return f"{start_year:04d}"
    duration_months = amount * 12 if unit_char == "Y" else amount
    if len(output_obs_date) == 7:
        end_idx = int(output_obs_date[:4]) * 12 + int(output_obs_date[5:7]) - 2
        start_idx = end_idx - duration_months + 1
        sy, sm0 = divmod(start_idx, 12)
        return f"{sy:04d}-{sm0 + 1:02d}"
    end_idx = (int(output_obs_date[:4]) - 1) * 12 + 11
    start_idx = end_idx - duration_months + 1
    sy, _ = divmod(start_idx, 12)
    return f"{sy:04d}"


def _build_multi_period_bins(
    output_obs_date: str,
    output_obs_period: str,
    num_output_periods: int,
    date_align_left: bool,
) -> Tuple[bool, List[Tuple[int, int, str]]]:
    """Computes (is_year_mode, [(start_bound, end_bound, out_date), ...]) for num_output_periods > 1."""
    m = _OUTPUT_PERIOD_RE.match(output_obs_period)
    if not m:
        raise ValueError(f"Invalid output_obs_period: {output_obs_period!r}")
    amount = int(m.group(1))
    unit_char = m.group(2)

    if len(output_obs_date) == 4 and unit_char == "Y":
        bins: List[Tuple[int, int, str]] = []
        base_end_year = int(output_obs_date) - (1 if date_align_left else 0)
        for k in range(num_output_periods):
            end_y = base_end_year - k * amount
            start_y = end_y - amount + 1
            out_d = f"{start_y:04d}" if date_align_left else f"{end_y:04d}"
            bins.append((start_y, end_y, out_d))
        return True, bins

    duration_months = amount * 12 if unit_char == "Y" else amount
    if len(output_obs_date) == 7:
        base_end_idx = (int(output_obs_date[:4]) * 12 +
                        (int(output_obs_date[5:7]) - 1) -
                        (1 if date_align_left else 0))
    else:
        base_end_idx = ((int(output_obs_date[:4]) -
                         (1 if date_align_left else 0)) * 12 + 11)

    bins = []
    for k in range(num_output_periods):
        end_idx = base_end_idx - k * duration_months
        start_idx = end_idx - duration_months + 1
        ref_idx = start_idx if date_align_left else end_idx
        ry, rm0 = divmod(ref_idx, 12)
        out_d = (f"{ry:04d}-{rm0 + 1:02d}"
                 if len(output_obs_date) == 7 else f"{ry:04d}")
        bins.append((start_idx, end_idx, out_d))
    return False, bins


def build_bigquery_series_agg_obs_sql(
    raw_obs_table: str,
    agg_obs_table: str,
    rounds: Sequence[Mapping[str, Any]],
    append_to_existing: bool = False,
) -> str:
    """Builds a single multi-round BigQuery SQL query matching OBS_BQ_SCHEMA."""
    safe_raw_table = _validate_bq_table_id(raw_obs_table, "raw_obs_table")
    safe_agg_table = _validate_bq_table_id(agg_obs_table, "agg_obs_table")
    validated_rounds = validate_stat_var_series_config(rounds)
    if not validated_rounds:
        raise ValueError("rounds must not be empty.")

    ctes: List[str] = [
        f"""deduped_raw AS (
        SELECT
            REGEXP_REPLACE(COALESCE(variableMeasured, ''), r'^(dcid|dcs|schema):', '') AS sv_id,
            REGEXP_REPLACE(COALESCE(observationAbout, ''), r'^(dcid|dcs|schema):', '') AS observationAbout,
            COALESCE(observationDate, '') AS observationDate,
            COALESCE(observationPeriod, '') AS observationPeriod,
            REGEXP_REPLACE(COALESCE(measurementMethod, ''), r'^(dcid|dcs|schema):', '') AS measurementMethod,
            REGEXP_REPLACE(COALESCE(unit, ''), r'^(dcid|dcs|schema):', '') AS unit,
            COALESCE(scalingFactor, '') AS scalingFactor,
            ARRAY_AGG(SAFE_CAST(value AS FLOAT64) ORDER BY row_num DESC LIMIT 1)[OFFSET(0)] AS val
        FROM `{safe_raw_table}`
        WHERE SAFE_CAST(value AS FLOAT64) IS NOT NULL
          AND NOT IS_NAN(SAFE_CAST(value AS FLOAT64))
          AND NOT IS_INF(SAFE_CAST(value AS FLOAT64))
          AND REGEXP_REPLACE(COALESCE(variableMeasured, ''), r'^(dcid|dcs|schema):', '') != ''
          AND REGEXP_REPLACE(COALESCE(observationAbout, ''), r'^(dcid|dcs|schema):', '') != ''
          AND COALESCE(observationDate, '') != ''
        GROUP BY
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor
    )"""
    ]

    round_cte_names: List[str] = []

    for round_cfg in validated_rounds:
        r_num = int(round_cfg["round"])
        source_cte = "deduped_raw" if r_num == 1 else f"round_{r_num - 1}"
        func_output_ctes: List[str] = []

        for f_idx, func in enumerate(round_cfg["aggr_funcs"]):
            f_type = func["type"]
            tag = f"r{r_num}_f{f_idx}"

            if f_type == "max_diff_across_measurement_methods":
                out_cte = f"{tag}_max_diff"
                ctes.append(f"""{out_cte} AS (
        SELECT
            CONCAT('DifferenceAcrossModels_', sv_id) AS sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            'dcAggregate/MaxDiffAcrossMeasurementMethods' AS measurementMethod,
            unit,
            scalingFactor,
            MAX(val) - MIN(val) AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM {source_cte}
        GROUP BY
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            unit,
            scalingFactor
        HAVING COUNT(*) >= 2
    )""")
                func_output_ctes.append(out_cte)

            elif f_type == "diff_relative_to_base_date":
                series_cte = f"{tag}_series"
                ctes.append(f"""{series_cte} AS (
        SELECT
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            CASE
                WHEN measurementMethod = '' THEN 'DataCommonsAggregate'
                WHEN measurementMethod = 'DataCommonsAggregate' THEN 'DataCommonsAggregate'
                WHEN STARTS_WITH(measurementMethod, 'dcAggregate/') THEN measurementMethod
                ELSE CONCAT('dcAggregate/', measurementMethod)
            END AS outMeasurementMethod,
            unit,
            scalingFactor,
            val,
            CAST(SUBSTR(observationDate, 1, 4) AS INT64) AS obs_year,
            IF(LENGTH(observationDate) = 7, SUBSTR(observationDate, 6, 2), '') AS obs_month
        FROM (
            SELECT
                *,
                COUNT(*) OVER (
                    PARTITION BY
                        sv_id,
                        observationAbout,
                        observationPeriod,
                        measurementMethod,
                        unit,
                        scalingFactor
                ) AS series_cnt
            FROM {source_cte}
            WHERE REGEXP_CONTAINS(observationDate, r'^\\d{{4}}(-(0[1-9]|1[0-2]))?$')
        )
        WHERE series_cnt >= 2
    )""")

                for s_idx, spec in enumerate(func["date_specs"]):
                    spec_tag = f"{tag}_s{s_idx}"
                    if "start_date" in spec and "end_date" in spec:
                        start_y = int(spec["start_date"][:4])
                        end_y = int(spec["end_date"][:4])
                        range_base_cte = f"{spec_tag}_range_base"
                        range_out_cte = f"{spec_tag}_range_out"
                        ctes.append(f"""{range_base_cte} AS (
        SELECT
            sv_id,
            observationAbout,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            obs_month,
            AVG(val) AS base_val
        FROM {series_cte}
        WHERE obs_year BETWEEN {start_y} AND {end_y}
        GROUP BY
            sv_id,
            observationAbout,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            obs_month
    )""")
                        ctes.append(f"""{range_out_cte} AS (
        SELECT
            CONCAT('DifferenceRelativeToBaseDate{start_y}To{end_y}_', s.sv_id) AS sv_id,
            s.observationAbout,
            s.observationDate,
            s.observationPeriod,
            s.outMeasurementMethod AS measurementMethod,
            s.unit,
            s.scalingFactor,
            s.val - b.base_val AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM {series_cte} s
        INNER JOIN {range_base_cte} b
            ON s.sv_id = b.sv_id
           AND s.observationAbout = b.observationAbout
           AND s.observationPeriod = b.observationPeriod
           AND s.measurementMethod = b.measurementMethod
           AND s.unit = b.unit
           AND s.scalingFactor = b.scalingFactor
           AND s.obs_month = b.obs_month
        WHERE s.obs_year > {end_y}
    )""")
                        func_output_ctes.append(range_out_cte)

                    if "dates" in spec:
                        cand_years = sorted({int(d[:4]) for d in spec["dates"]})
                        years_sql = ", ".join(str(y) for y in cand_years)
                        chosen_cte = f"{spec_tag}_chosen_year"
                        disc_base_cte = f"{spec_tag}_disc_base"
                        disc_out_cte = f"{spec_tag}_disc_out"
                        ctes.append(f"""{chosen_cte} AS (
        SELECT
            sv_id,
            observationAbout,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            MIN(IF(obs_year IN ({years_sql}), obs_year, NULL)) AS base_year
        FROM {series_cte}
        GROUP BY
            sv_id,
            observationAbout,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor
        HAVING MIN(IF(obs_year IN ({years_sql}), obs_year, NULL)) IS NOT NULL
    )""")
                        ctes.append(f"""{disc_base_cte} AS (
        SELECT
            s.sv_id,
            s.observationAbout,
            s.observationPeriod,
            s.measurementMethod,
            s.unit,
            s.scalingFactor,
            c.base_year,
            s.obs_month,
            ANY_VALUE(s.val) AS base_val
        FROM {series_cte} s
        INNER JOIN {chosen_cte} c
            ON s.sv_id = c.sv_id
           AND s.observationAbout = c.observationAbout
           AND s.observationPeriod = c.observationPeriod
           AND s.measurementMethod = c.measurementMethod
           AND s.unit = c.unit
           AND s.scalingFactor = c.scalingFactor
           AND s.obs_year = c.base_year
        GROUP BY
            s.sv_id,
            s.observationAbout,
            s.observationPeriod,
            s.measurementMethod,
            s.unit,
            s.scalingFactor,
            c.base_year,
            s.obs_month
    )""")
                        ctes.append(f"""{disc_out_cte} AS (
        SELECT
            CONCAT('DifferenceRelativeToBaseDate', CAST(b.base_year AS STRING), '_', s.sv_id) AS sv_id,
            s.observationAbout,
            s.observationDate,
            s.observationPeriod,
            s.outMeasurementMethod AS measurementMethod,
            s.unit,
            s.scalingFactor,
            s.val - b.base_val AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM {series_cte} s
        INNER JOIN {disc_base_cte} b
            ON s.sv_id = b.sv_id
           AND s.observationAbout = b.observationAbout
           AND s.observationPeriod = b.observationPeriod
           AND s.measurementMethod = b.measurementMethod
           AND s.unit = b.unit
           AND s.scalingFactor = b.scalingFactor
           AND s.obs_month = b.obs_month
        WHERE s.obs_year > b.base_year
    )""")
                        func_output_ctes.append(disc_out_cte)

            elif f_type == "stats_across_models":
                out_cte = f"{tag}_stats"
                extra_where = ""
                if func.get("sv_regex"):
                    extra_where = (
                        " AND " +
                        _compile_sv_regex_to_bq_sql("sv_id", func["sv_regex"]))
                ctes.append(f"""{out_cte} AS (
        SELECT
            CONCAT(ens.prefix, '_', g.sv_id) AS sv_id,
            g.observationAbout,
            g.observationDate,
            g.observationPeriod,
            CONCAT('dcAggregate/', ens.prefix) AS measurementMethod,
            g.unit,
            g.scalingFactor,
            g.sorted_vals[OFFSET(CAST(CEIL((ens.p * g.n) / 100.0) AS INT64) - 1)] AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM (
            SELECT
                sv_id,
                observationAbout,
                observationDate,
                observationPeriod,
                unit,
                scalingFactor,
                ARRAY_AGG(val ORDER BY val ASC) AS sorted_vals,
                COUNT(*) AS n
            FROM {source_cte}
            WHERE NOT STARTS_WITH(sv_id, 'DifferenceAcrossModels_'){extra_where}
            GROUP BY
                sv_id,
                observationAbout,
                observationDate,
                observationPeriod,
                unit,
                scalingFactor
        ) g
        CROSS JOIN UNNEST([
            STRUCT('Percentile10AcrossModels' AS prefix, 10 AS p),
            STRUCT('MedianAcrossModels' AS prefix, 50 AS p),
            STRUCT('Percentile90AcrossModels' AS prefix, 90 AS p)
        ]) AS ens
    )""")
                func_output_ctes.append(out_cte)

            elif f_type == "aggr_over_time":
                tr = func["time_range"]
                in_period = tr["input_obs_period"]
                out_period = tr["output_obs_period"]
                out_date = tr["output_obs_date"]
                num_periods = int(func.get("num_output_periods", 1))
                align_left = bool(func.get("date_align_left", False))

                case_branches: List[str] = []
                cfg_structs: List[str] = []
                op_to_auto_prefix = {
                    "MAX": "AggregateMax_",
                    "MIN": "AggregateMin_",
                    "MEAN": "AggregateMean_",
                    "SUM": "AggregateSum_",
                }
                for c_idx, svc in enumerate(func["sv_configs"]):
                    cond_sql = _compile_sv_regex_to_bq_sql(
                        "o.sv_id", svc["sv_regex"])
                    case_branches.append(f"WHEN {cond_sql} THEN {c_idx}")
                    agg_op = svc["aggregation_op"]
                    auto_pref = op_to_auto_prefix[agg_op]
                    use_in_lit = ("TRUE" if svc["use_input_sv_for_output"] else
                                  "FALSE")
                    cfg_structs.append(
                        f"STRUCT({c_idx} AS cfg_idx, "
                        f"'{svc['unit']}' AS req_unit, "
                        f"'{agg_op}' AS agg_op, "
                        f"'{auto_pref}' AS auto_prefix, "
                        f"{use_in_lit} AS use_input_sv, "
                        f"'{svc['output_sv_prefix']}' AS out_sv_prefix)")

                case_sql = (
                    "CASE\n                    " +
                    "\n                    ".join(case_branches) +
                    "\n                    ELSE NULL\n                END")
                cfg_unnest_sql = "UNNEST([\n            " + ",\n            ".join(
                    cfg_structs) + "\n        ])"

                out_cte = f"{tag}_aot"
                if num_periods == 1:
                    win_pred = _build_clean_window_sql_predicate(
                        "o.observationDate",
                        out_date,
                        out_period,
                        date_align_left=align_left,
                    )
                    effective_out_date = _compute_single_window_output_date(
                        out_date, out_period, date_align_left=align_left)
                    ctes.append(f"""{out_cte} AS (
        SELECT
            IF(c.use_input_sv, CONCAT(c.out_sv_prefix, m.sv_id), CONCAT(c.auto_prefix, m.sv_id)) AS sv_id,
            m.observationAbout,
            '{effective_out_date}' AS observationDate,
            '{out_period}' AS observationPeriod,
            m.measurementMethod,
            m.unit,
            m.scalingFactor,
            CASE c.agg_op
                WHEN 'MAX' THEN MAX(m.val)
                WHEN 'MIN' THEN MIN(m.val)
                WHEN 'MEAN' THEN AVG(m.val)
                WHEN 'SUM' THEN SUM(m.val)
            END AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM (
            SELECT
                o.*,
                {case_sql} AS cfg_idx
            FROM {source_cte} o
            WHERE o.observationPeriod = '{in_period}'
              AND {win_pred}
        ) m
        INNER JOIN {cfg_unnest_sql} c
            ON m.cfg_idx = c.cfg_idx
        WHERE (c.req_unit = '' OR m.unit = c.req_unit)
        GROUP BY
            c.cfg_idx,
            c.use_input_sv,
            c.out_sv_prefix,
            c.auto_prefix,
            c.agg_op,
            m.sv_id,
            m.observationAbout,
            m.measurementMethod,
            m.unit,
            m.scalingFactor
    )""")
                else:
                    is_year_mode, bins = _build_multi_period_bins(
                        out_date, out_period, num_periods, align_left)
                    bin_structs = ", ".join(
                        f"STRUCT({b_start} AS b_start, {b_end} AS b_end, '{b_date}' AS out_date)"
                        for b_start, b_end, b_date in bins)
                    pos_expr = (
                        "CAST(SUBSTR(m.observationDate, 1, 4) AS INT64)"
                        if is_year_mode else
                        "(CAST(SUBSTR(m.observationDate, 1, 4) AS INT64) * 12 + "
                        "IF(LENGTH(m.observationDate) >= 7, CAST(SUBSTR(m.observationDate, 6, 2) AS INT64), 1) - 1)"
                    )
                    ctes.append(f"""{out_cte} AS (
        SELECT
            IF(c.use_input_sv, CONCAT(c.out_sv_prefix, m.sv_id), CONCAT(c.auto_prefix, m.sv_id)) AS sv_id,
            m.observationAbout,
            wb.out_date AS observationDate,
            '{out_period}' AS observationPeriod,
            m.measurementMethod,
            m.unit,
            m.scalingFactor,
            CASE c.agg_op
                WHEN 'MAX' THEN MAX(m.val)
                WHEN 'MIN' THEN MIN(m.val)
                WHEN 'MEAN' THEN AVG(m.val)
                WHEN 'SUM' THEN SUM(m.val)
            END AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM (
            SELECT
                o.*,
                {case_sql} AS cfg_idx
            FROM {source_cte} o
            WHERE o.observationPeriod = '{in_period}'
              AND REGEXP_CONTAINS(o.observationDate, r'^\\d{{4}}(-(0[1-9]|1[0-2])(-\\d{{2}})?)?$')
        ) m
        INNER JOIN {cfg_unnest_sql} c
            ON m.cfg_idx = c.cfg_idx
        INNER JOIN UNNEST([{bin_structs}]) wb
            ON {pos_expr} BETWEEN wb.b_start AND wb.b_end
        WHERE (c.req_unit = '' OR m.unit = c.req_unit)
        GROUP BY
            c.cfg_idx,
            c.use_input_sv,
            c.out_sv_prefix,
            c.auto_prefix,
            c.agg_op,
            wb.out_date,
            m.sv_id,
            m.observationAbout,
            m.measurementMethod,
            m.unit,
            m.scalingFactor
    )""")
                func_output_ctes.append(out_cte)

            elif f_type == "count_threshold_exception_over_time":
                tr = func["time_range"]
                in_period = tr["input_obs_period"]
                out_period = tr["output_obs_period"]
                out_date = tr["output_obs_date"]
                period_prefix = ("NumberOfMonths_"
                                 if in_period == "P1M" else "NumberOfDays_")
                win_pred = _build_clean_window_sql_predicate(
                    "o.observationDate", out_date, out_period)

                case_branches = []
                thres_structs: List[str] = []
                for t_idx, thres in enumerate(func["thresholds"]):
                    cond_sql = _compile_sv_regex_to_bq_sql(
                        "o.sv_id", thres["sv_regex"])
                    case_branches.append(f"WHEN {cond_sql} THEN {t_idx}")
                    t_val = float(thres["threshold_value"])
                    t_str = format_numeric_value(t_val)
                    comp = thres["comparison"]
                    unit_str = thres["unit"]
                    comp_suffix = "OrMore_" if comp == "GE" else "OrLess_"
                    sv_prefix = f"{period_prefix}{t_str}{unit_str}{comp_suffix}"
                    thres_structs.append(
                        f"STRUCT({t_idx} AS thres_idx, "
                        f"'{unit_str}' AS req_unit, "
                        f"'{comp}' AS comp, "
                        f"CAST({repr(t_val)} AS FLOAT64) AS threshold_val, "
                        f"'{sv_prefix}' AS sv_prefix)")

                case_sql = (
                    "CASE\n                    " +
                    "\n                    ".join(case_branches) +
                    "\n                    ELSE NULL\n                END")
                thres_unnest_sql = "UNNEST([\n            " + ",\n            ".join(
                    thres_structs) + "\n        ])"
                cnt_expr = (
                    "COUNTIF((t.comp = 'GE' AND m.val >= t.threshold_val) "
                    "OR (t.comp = 'LE' AND m.val <= t.threshold_val))")

                out_cte = f"{tag}_cnt"
                ctes.append(f"""{out_cte} AS (
        SELECT
            CONCAT(t.sv_prefix, m.sv_id) AS sv_id,
            m.observationAbout,
            '{out_date}' AS observationDate,
            '{out_period}' AS observationPeriod,
            m.measurementMethod,
            '' AS unit,
            m.scalingFactor,
            CAST({cnt_expr} AS FLOAT64) AS val,
            {r_num} AS round_num,
            {f_idx} AS func_idx
        FROM (
            SELECT
                o.*,
                {case_sql} AS thres_idx
            FROM {source_cte} o
            WHERE o.observationPeriod = '{in_period}'
              AND {win_pred}
        ) m
        INNER JOIN {thres_unnest_sql} t
            ON m.thres_idx = t.thres_idx
        WHERE m.unit = t.req_unit
        GROUP BY
            t.thres_idx,
            t.sv_prefix,
            m.sv_id,
            m.observationAbout,
            m.measurementMethod,
            m.scalingFactor
        HAVING {cnt_expr} > 0
    )""")
                func_output_ctes.append(out_cte)

        round_union_sql = "\n            UNION ALL\n            ".join(
            f"SELECT * FROM {c_name}" for c_name in func_output_ctes)
        round_cte = f"round_{r_num}"
        ctes.append(f"""{round_cte} AS (
        SELECT
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            ARRAY_AGG(val ORDER BY func_idx DESC LIMIT 1)[OFFSET(0)] AS val,
            {r_num} AS round_num,
            MAX(func_idx) AS func_idx
        FROM (
            {round_union_sql}
        )
        GROUP BY
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor
    )""")
        round_cte_names.append(round_cte)

    all_rounds_union_sql = "\n            UNION ALL\n            ".join(
        f"SELECT * FROM {r_cte}" for r_cte in round_cte_names)

    ctes.append(f"""all_rounds AS (
        SELECT
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            ARRAY_AGG(val ORDER BY round_num DESC, func_idx DESC LIMIT 1)[OFFSET(0)] AS raw_val,
            MAX(round_num) AS round_num,
            MAX(func_idx) AS func_idx
        FROM (
            {all_rounds_union_sql}
        )
        GROUP BY
            sv_id,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor
    )""")

    row_offset_sql = (
        f" + COALESCE((SELECT MAX(row_num) FROM `{safe_agg_table}`), 0)"
        if append_to_existing else "")

    ctes.append(f"""formatted AS (
        SELECT
            sv_id,
            CONCAT('dcid:', sv_id) AS variableMeasured,
            CASE
                WHEN raw_val = 0 THEN '0'
                WHEN raw_val = ROUND(raw_val) AND ABS(raw_val) < 1e16
                    THEN CAST(CAST(ROUND(raw_val) AS INT64) AS STRING)
                ELSE FORMAT('%.15g', raw_val)
            END AS value,
            observationAbout,
            observationDate,
            observationPeriod,
            measurementMethod,
            unit,
            scalingFactor,
            ROW_NUMBER() OVER (
                ORDER BY
                    round_num,
                    func_idx,
                    sv_id,
                    observationAbout,
                    observationDate,
                    measurementMethod,
                    observationPeriod,
                    unit,
                    scalingFactor
            ){row_offset_sql} AS row_num
        FROM all_rounds
    )""")

    key_combined_expr = bigquery_differ.format_key_combined_sql(
        var_expr="sv_id",
        about_expr="observationAbout",
        date_expr="observationDate",
        period_expr="observationPeriod",
        method_expr="measurementMethod",
        unit_expr="unit",
        scaling_expr="scalingFactor",
    )

    with_block = ",\n    ".join(ctes)
    if append_to_existing:
        header = f"""INSERT INTO `{safe_agg_table}` (
        key_combined,
        variableMeasured,
        value,
        observationAbout,
        observationDate,
        observationPeriod,
        measurementMethod,
        unit,
        scalingFactor,
        row_num
    )"""
        order_clause = ""
    else:
        header = f"CREATE OR REPLACE TABLE `{safe_agg_table}` AS"
        order_clause = "\n    ORDER BY row_num"

    return f"""
    {header}
    WITH {with_block}
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
    FROM formatted{order_clause}
    """


def _extract_series_row_fields(
        row: Any) -> Tuple[str, str, str, str, str, str, str, str]:
    """Extracts 8 StatVarObservation fields from a DB row using 15-sig-fig formatting."""
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

    strip_mcf = stat_var_aggregator._strip_mcf_value
    return (
        strip_mcf(var_m),
        format_numeric_value(val),
        strip_mcf(about),
        strip_mcf(date),
        strip_mcf(period),
        strip_mcf(method),
        strip_mcf(unit),
        strip_mcf(scaling),
    )


def _stream_series_chunks_to_mcf_and_summary(
    chunks: Iterable[Iterable[Any]],
    output_mcf_path: str,
    summary_report_path: Optional[str] = None,
) -> int:
    """Streams pages of series-aggregated rows to MCF and summary_report.csv in O(1) memory."""
    total_written = 0
    stats_by_sv: Dict[str, stat_var_aggregator._StatVarSummaryStats] = {}

    with contextlib.ExitStack() as stack:
        out_stream = None
        for chunk in chunks:
            for row in chunk:
                sv, val_str, about, date, period, method, unit, scaling = (
                    _extract_series_row_fields(row))
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
                node_lines = stat_var_aggregator._format_mcf_node_lines(
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
                stats_by_sv.setdefault(
                    sv, stat_var_aggregator._StatVarSummaryStats()).add(
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


def run_bigquery_series_aggregation(
    mcf_pattern: str,
    rounds: Sequence[Mapping[str, Any]],
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
    reuse_existing_raw_obs: bool = False,
    append_to_agg_obs: bool = False,
) -> Dict[str, Any]:
    """Executes StatVar series aggregation in BigQuery and streams stat_var_series_agg_nodes.mcf."""
    validated_rounds = validate_stat_var_series_config(rounds)
    if not validated_rounds:
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
    raw_obs_table = _validate_bq_table_id(table_ids["raw_obs"], "raw_obs_table")
    raw_schema_table = _validate_bq_table_id(table_ids["raw_schema"],
                                             "raw_schema_table")
    agg_obs_table = _validate_bq_table_id(table_ids["agg_obs"], "agg_obs_table")

    if reuse_existing_raw_obs:
        raw_obs_tbl = bigquery_differ._get_existing_bq_table(
            client, raw_obs_table)
        raw_schema_tbl = bigquery_differ._get_existing_bq_table(
            client, raw_schema_table)
        raw_schema_count = (bigquery_differ._get_table_num_rows(raw_schema_tbl)
                            if raw_schema_tbl is not None else 0)
        if raw_obs_tbl is None:
            logging.info(
                "Existing raw_obs table %s not found; skipping series aggregation.",
                raw_obs_table,
            )
            return {
                "raw_obs_count": 0,
                "raw_schema_count": raw_schema_count,
                "agg_obs_count": 0,
                "output_mcf_path": None,
                "table_ids": table_ids,
            }
        raw_num_rows = getattr(raw_obs_tbl, "num_rows", None)
        if isinstance(raw_num_rows,
                      (int, float)) and not isinstance(raw_num_rows, bool):
            raw_obs_count = int(raw_num_rows)
            if raw_obs_count == 0:
                logging.info(
                    "Existing raw_obs table %s has 0 rows; skipping series aggregation.",
                    raw_obs_table,
                )
                return {
                    "raw_obs_count": 0,
                    "raw_schema_count": raw_schema_count,
                    "agg_obs_count": 0,
                    "output_mcf_path": None,
                    "table_ids": table_ids,
                }
        else:
            raw_obs_count = 0
    else:
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
                "stat_var_agg_nodes.mcf",
                STAT_VAR_SERIES_AGG_MCF_FILENAME,
            },
        )
        if raw_obs_count == 0:
            logging.info(
                "No raw observations found in %s; skipping series agg_obs creation.",
                mcf_pattern,
            )
            return {
                "raw_obs_count": 0,
                "raw_schema_count": raw_schema_count,
                "agg_obs_count": 0,
                "output_mcf_path": None,
                "table_ids": table_ids,
            }

    if append_to_agg_obs:
        series_agg_table = _validate_bq_table_id(f"{agg_obs_table}_series",
                                                 "series_agg_table")
        logging.info(
            "Step 2/3: Computing StatVar series aggregations into %s and appending to %s...",
            series_agg_table,
            agg_obs_table,
        )
        try:
            create_series_sql = build_bigquery_series_agg_obs_sql(
                raw_obs_table=raw_obs_table,
                agg_obs_table=series_agg_table,
                rounds=validated_rounds,
                append_to_existing=False,
            )
            client.query(create_series_sql).result()

            series_table_obj = client.get_table(series_agg_table)
            series_table_obj.expires = datetime.now(
                timezone.utc) + timedelta(hours=expiration_hours)
            client.update_table(series_table_obj, ["expires"])

            append_sql = f"""
            INSERT INTO `{agg_obs_table}` (
                key_combined,
                variableMeasured,
                value,
                observationAbout,
                observationDate,
                observationPeriod,
                measurementMethod,
                unit,
                scalingFactor,
                row_num
            )
            SELECT
                s.key_combined,
                s.variableMeasured,
                s.value,
                s.observationAbout,
                s.observationDate,
                s.observationPeriod,
                s.measurementMethod,
                s.unit,
                s.scalingFactor,
                s.row_num + COALESCE((SELECT MAX(row_num) FROM `{agg_obs_table}`), 0) AS row_num
            FROM `{series_agg_table}` s
            """
            client.query(append_sql).result()

            logging.info(
                "Step 3/3: Streaming %s in %d-row pages to %s...",
                series_agg_table,
                page_size,
                output_mcf_path,
            )
            select_series_sql = f"""
            SELECT
                variableMeasured,
                value,
                observationAbout,
                observationDate,
                observationPeriod,
                measurementMethod,
                unit,
                scalingFactor
            FROM `{series_agg_table}`
            ORDER BY row_num
            """
            row_iter = client.query(select_series_sql).result(
                page_size=page_size)
            agg_obs_count = _stream_series_chunks_to_mcf_and_summary(
                chunks=stat_var_aggregator._iter_bq_result_pages(row_iter),
                output_mcf_path=output_mcf_path,
                summary_report_path=summary_report_path,
            )
        finally:
            client.delete_table(series_agg_table, not_found_ok=True)
    else:
        logging.info(
            "Step 2/3: Computing StatVar series aggregations into BigQuery table %s...",
            agg_obs_table,
        )
        create_agg_sql = build_bigquery_series_agg_obs_sql(
            raw_obs_table=raw_obs_table,
            agg_obs_table=agg_obs_table,
            rounds=validated_rounds,
            append_to_existing=False,
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
        agg_obs_count = _stream_series_chunks_to_mcf_and_summary(
            chunks=stat_var_aggregator._iter_bq_result_pages(row_iter),
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


def run_stat_var_series_aggregation_for_genmcf(
    import_name: str,
    genmcf_output_path: str,
    config_path: Optional[str] = None,
    import_spec: Optional[Mapping[str, Any]] = None,
    bigquery_project_id: Optional[str] = None,
    bigquery_dataset_id: str = "datcom_import_differ",
    version: str = "v0",
    input_prefix: str = "input0",
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
    bq_client: Optional[bigquery.Client] = None,
    reuse_existing_raw_obs: bool = False,
    append_to_agg_obs: bool = False,
) -> Optional[str]:
    """Runs ET-layer StatVar series aggregation for a genmcf output directory (local or gs://)."""
    rounds = load_stat_var_series_aggregation_config(
        import_name=import_name,
        config_path=config_path,
        import_spec=import_spec,
    )
    if not rounds:
        return None

    is_gcs = file_util.file_is_gcs(genmcf_output_path)
    base_dir = genmcf_output_path.rstrip("/")
    mcf_pattern = f"{base_dir}/*.mcf" if is_gcs else os.path.join(
        base_dir, "*.mcf")
    output_mcf_path = (f"{base_dir}/{STAT_VAR_SERIES_AGG_MCF_FILENAME}"
                       if is_gcs else os.path.join(
                           base_dir, STAT_VAR_SERIES_AGG_MCF_FILENAME))
    summary_csv_path = (f"{base_dir}/summary_report.csv" if is_gcs else
                        os.path.join(base_dir, "summary_report.csv"))

    if not is_gcs and not os.path.exists(genmcf_output_path):
        logging.warning(
            "genmcf output path %s does not exist for %s",
            genmcf_output_path,
            import_name,
        )
        return None

    res = run_bigquery_series_aggregation(
        mcf_pattern=mcf_pattern,
        rounds=rounds,
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
        reuse_existing_raw_obs=reuse_existing_raw_obs,
        append_to_agg_obs=append_to_agg_obs,
    )

    return res.get("output_mcf_path")
