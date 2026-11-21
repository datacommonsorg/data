#!/usr/bin/env python3
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
"""Consolidates the 6 active legacy Dartmouth Atlas CNS tables (1999-2016).

Reads the resolved StatVarObservation TFRecords (graph.tfrecord-00000-of-00001.gz,
serialized datacommons.proto.MCFOptimizedGraph messages, or fallback .mcf files)
produced by the 2026-07-21 StatPop-to-SVObs conversion (cl/954587569, b/527799466)
under:
  /cns/jv-d/home/datcom/v3_resolved_mcf/dartmouth_atlas/stat_pop/

Produces three deterministic artifacts in --output_dir:
  1. dartmouth_atlas_medicare_historical_1999_2016.csv
     (uploaded once to gs://unresolved_mcf/dartmouth_atlas_medicare/historical/)
  2. common_tmcf.tmcf
     (shared TMCF matching stat_var_processor.py output columns)
  3. dartmouth_atlas_medicare_historical_1999_2016.mcf
     (deduplicated baseline MCF suitable for import_differ previous_data)
"""

import argparse
import csv
import gzip
import io
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.abspath(os.path.join(_CODEDIR, "../../util"))
if _UTIL_DIR not in sys.path:
    sys.path.insert(1, _UTIL_DIR)

from absl import logging
import file_util

DEFAULT_CNS_DIR = (
    "/cns/jv-d/home/datcom/v3_resolved_mcf/dartmouth_atlas/stat_pop")
DEFAULT_OUTPUT_DIR = os.path.join(_CODEDIR, "historical")

# Six active sub-tables in cl/954587569 (the other 5 ComparativeObservation
# tables lack graph.tfrecord* files and have 0 rows in production KG). Order
# determines priority when Count_MedicareEnrollee overlaps across tables:
# dartmouth_reim_count (county/state/USA) takes precedence over
# dartmouth_num_overall and dartmouth_mortality_count (HRR/HSA City/Town/Village).
ACTIVE_SUBTABLES: tuple[str, ...] = (
    "dartmouth_reim_count",
    "dartmouth_reim",
    "dartmouth_num_overall",
    "dartmouth_num_enrollees",
    "dartmouth_num_diabetics",
    "dartmouth_mortality_count",
)

REIM_STAT_VAR = "dc/rn90czcrqcv06"

ALLOWED_STAT_VARS: frozenset[str] = frozenset({
    "Count_MedicareEnrollee",
    REIM_STAT_VAR,
    "Count_MedicareEnrollee_MedicareA",
    "Count_MedicareEnrollee_MedicareA_Black",
    "Count_MedicareEnrollee_MedicareA_NonBlack",
    "Count_MedicareEnrollee_MedicareB",
    "Count_MedicareEnrollee_MedicareB_Black",
    "Count_MedicareEnrollee_MedicareB_NonBlack",
    "Count_MedicareEnrollee_ConditionDiabetic_Black",
    "Count_MedicareEnrollee_ConditionDiabetic_NonBlack",
})

OUTPUT_COLUMNS: list[str] = [
    "observationDate",
    "observationAbout",
    "variableMeasured",
    "value",
    "observationPeriod",
]

HISTORICAL_CSV_FILENAME = "dartmouth_atlas_medicare_historical_1999_2016.csv"
HISTORICAL_MCF_FILENAME = "dartmouth_atlas_medicare_historical_1999_2016.mcf"
COMMON_TMCF_FILENAME = "common_tmcf.tmcf"
DEFAULT_OBSERVATION_PERIOD = "P1Y"

COMMON_TMCF_CONTENT = (
    "Node: E:dartmouth_atlas_medicare->E0\n"
    "observationDate: C:dartmouth_atlas_medicare->observationDate\n"
    "observationAbout: C:dartmouth_atlas_medicare->observationAbout\n"
    "variableMeasured: C:dartmouth_atlas_medicare->variableMeasured\n"
    "value: C:dartmouth_atlas_medicare->value\n"
    "observationPeriod: C:dartmouth_atlas_medicare->observationPeriod\n"
    "typeOf: dcs:StatVarObservation\n")

NON_NUMERIC_TOKENS: frozenset[str] = frozenset({
    "",
    ".",
    "-",
    "--",
    "*",
    "na",
    "n/a",
    "nan",
    "none",
    "null",
    "suppressed",
})

VALID_STATE_AND_TERRITORY_FIPS: frozenset[str] = frozenset({
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55",
    "56", "60", "66", "69", "72", "78",
})


def strip_quotes_and_prefix(raw: str) -> str:
    """Strips outer whitespace, quotes, and leading dcid:/dcs: namespace."""
    text = (raw or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1].strip()
    for prefix in ("dcid:", "dcs:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def is_valid_historical_place(place: str) -> bool:
    """Validates historical place DCIDs, dropping legacy CMS/SSA dummy codes.

    Filters out unresolved legacy CNS place codes that fail Data Commons
    existence checks (e.g., geoId/99999, geoId/999999, geoId/99003, geoId/33929)
    while preserving valid 2-digit states, 5-digit counties (including retired
    Alaska/SD/VA counties), 7-digit HRR/HSA Census places, and country/USA.
    """
    if place == "country/USA":
        return True
    if not place.startswith("geoId/"):
        return False
    code = place[6:]
    if not code.isdigit():
        return False
    if len(code) == 2:
        return code in VALID_STATE_AND_TERRITORY_FIPS
    if len(code) == 5:
        if code[:2] not in VALID_STATE_AND_TERRITORY_FIPS:
            return False
        county_subcode = int(code[2:])
        return 0 < county_subcode < 900
    if len(code) == 7:
        return (code[:2] in VALID_STATE_AND_TERRITORY_FIPS and
                int(code[2:]) > 0)
    return False


def format_finite_number(parsed: float) -> tuple[float, str] | None:
    """Validates a finite non-negative float and formats up to 6 decimals."""
    if not math.isfinite(parsed) or parsed < 0:
        return None
    rounded = round(parsed, 6)
    if rounded == int(rounded):
        return parsed, str(int(rounded))
    return parsed, f"{rounded:.6f}".rstrip("0").rstrip(".")


def clean_numeric_value(raw_val: str) -> tuple[float, str] | None:
    """Parses a finite non-negative numeric string, returning (float, str)."""
    if raw_val is None:
        return None
    cleaned = strip_quotes_and_prefix(raw_val).replace(",", "").replace("$", "")
    cleaned = cleaned.strip()
    if cleaned.lower() in NON_NUMERIC_TOKENS:
        return None
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    return format_finite_number(parsed)


def atomic_write_text(target_path: Path, content: str) -> None:
    """Writes UTF-8 text atomically via a sibling temporary file."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target_path.parent, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def list_subtable_data_files(source_dir: str, subtable: str) -> list[str]:
    """Lists resolved TFRecord (preferred) or MCF files for a sub-table."""
    base = source_dir.rstrip("/")
    if base.startswith("/cns/"):
        patterns = (
            f"{base}/{subtable}/graph.tfrecord*",
            f"{base}/{subtable}.tfrecord*",
            f"{base}/{subtable}/nodes.mcf*",
            f"{base}/{subtable}.mcf",
        )
        for pattern in patterns:
            res = subprocess.run(
                ["fileutil", "ls", pattern],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                matches = sorted(
                    line.strip()
                    for line in res.stdout.splitlines()
                    if line.strip() and not line.strip().endswith("/"))
                if matches:
                    return matches
        return []

    if base.startswith("gs://"):
        for pattern in (
                f"{base}/{subtable}/graph.tfrecord*",
                f"{base}/{subtable}.tfrecord*",
                f"{base}/{subtable}/nodes.mcf*",
                f"{base}/{subtable}.mcf",
        ):
            matches = sorted(file_util.file_get_matching(pattern))
            if matches:
                return matches
        return []

    local_base = Path(base)
    subdir = local_base / subtable
    if subdir.is_dir():
        for glob_pat in ("graph.tfrecord*", "nodes.mcf*"):
            matches = sorted(
                str(p) for p in subdir.glob(glob_pat) if p.is_file())
            if matches:
                return matches
    for glob_pat in (f"{subtable}.tfrecord*", f"{subtable}.mcf"):
        flat_matches = sorted(
            str(p) for p in local_base.glob(glob_pat) if p.is_file())
        if flat_matches:
            return flat_matches
    return []


def stage_file_to_local(remote_path: str, stage_dir: Path, idx: int) -> Path:
    """Stages a CNS/GCS file locally or returns the local Path directly."""
    if remote_path.startswith("/cns/"):
        local_dst = stage_dir / f"{idx:03d}_{os.path.basename(remote_path)}"
        res = subprocess.run(
            ["fileutil", "cp", remote_path,
             str(local_dst)],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"fileutil cp failed for {remote_path}: {res.stderr.strip()}")
        return local_dst
    if remote_path.startswith("gs://"):
        local_dst = stage_dir / f"{idx:03d}_{os.path.basename(remote_path)}"
        file_util.file_copy(remote_path, str(local_dst))
        return local_dst
    return Path(remote_path)


def _read_varint(buf: memoryview, pos: int) -> tuple[int, int]:
    """Reads an unsigned base-128 varint from buf starting at pos."""
    result = 0
    shift = 0
    length = len(buf)
    while pos < length:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7
        if shift >= 70:
            raise ValueError("Malformed protobuf varint")
    raise ValueError("Truncated protobuf varint")


def _iter_proto_fields(buf: bytes | memoryview):
    """Yields (field_number, wire_type, raw_value) from a protobuf message."""
    view = buf if isinstance(buf, memoryview) else memoryview(buf)
    pos = 0
    end = len(view)
    while pos < end:
        tag, pos = _read_varint(view, pos)
        field_num = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            val, pos = _read_varint(view, pos)
            yield field_num, wire_type, val
        elif wire_type == 1:
            if pos + 8 > end:
                raise ValueError("Truncated fixed64 field")
            yield field_num, wire_type, view[pos:pos + 8]
            pos += 8
        elif wire_type == 2:
            sub_len, pos = _read_varint(view, pos)
            if pos + sub_len > end:
                raise ValueError("Truncated length-delimited field")
            yield field_num, wire_type, view[pos:pos + sub_len]
            pos += sub_len
        elif wire_type == 5:
            if pos + 4 > end:
                raise ValueError("Truncated fixed32 field")
            yield field_num, wire_type, view[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")


def _decode_vals_first_str(vals_bytes: memoryview) -> str:
    """Extracts the first string value from datacommons.proto.MCFGraph.Vals."""
    for fnum, wtype, raw in _iter_proto_fields(vals_bytes):
        if wtype != 2:
            continue
        if fnum == 1:  # repeated string val = 1 (deprecated)
            return bytes(raw).decode("utf-8", errors="replace")
        if fnum == 2:  # repeated TypedVal typed_val = 2
            for tv_fnum, tv_wtype, tv_raw in _iter_proto_fields(raw):
                if tv_fnum == 2 and tv_wtype == 2:  # string val = 2
                    return bytes(tv_raw).decode("utf-8", errors="replace")
    return ""


def _decode_prop_vals(prop_vals_bytes: memoryview) -> dict[str, str]:
    """Decodes datacommons.proto.MCFGraph.PropVals into dict[prop, val]."""
    pvs: dict[str, str] = {}
    for fnum, wtype, entry_raw in _iter_proto_fields(prop_vals_bytes):
        if fnum != 1 or wtype != 2:  # map<string, Vals> pv = 1
            continue
        prop_key = ""
        prop_val = ""
        for mfnum, mwtype, mraw in _iter_proto_fields(entry_raw):
            if mfnum == 1 and mwtype == 2:
                prop_key = bytes(mraw).decode("utf-8", errors="replace")
            elif mfnum == 2 and mwtype == 2:
                prop_val = _decode_vals_first_str(mraw)
        if prop_key:
            pvs[prop_key] = prop_val
    return pvs


def _decode_sv_obs_series(series_bytes: memoryview):
    """Yields SVObs dicts from datacommons.proto.MCFStatVarObsSeries."""
    about = ""
    variable = ""
    period = ""
    obs_entries: list[memoryview] = []

    for fnum, wtype, raw in _iter_proto_fields(series_bytes):
        if wtype != 2:
            continue
        if fnum == 1:  # Key key = 1
            for kfnum, kwtype, kraw in _iter_proto_fields(raw):
                if kwtype != 2:
                    continue
                if kfnum == 1:
                    about = bytes(kraw).decode("utf-8", errors="replace")
                elif kfnum == 2:
                    variable = bytes(kraw).decode("utf-8", errors="replace")
                elif kfnum == 4:
                    period = bytes(kraw).decode("utf-8", errors="replace")
        elif fnum == 2:  # repeated StatVarObs sv_obs_list = 2
            obs_entries.append(raw)

    for obs_raw in obs_entries:
        date_str = ""
        num_val: float | None = None
        text_val: str | None = None
        extra_pvs: dict[str, str] = {}
        for ofnum, owtype, oraw in _iter_proto_fields(obs_raw):
            if ofnum == 1 and owtype == 2:  # string date = 1
                date_str = bytes(oraw).decode("utf-8", errors="replace")
            elif ofnum == 2 and owtype == 1:  # double number = 2
                num_val = struct.unpack("<d", oraw)[0]
            elif ofnum == 3 and owtype == 2:  # string text = 3
                text_val = bytes(oraw).decode("utf-8", errors="replace")
            elif ofnum == 4 and owtype == 2:  # MCFGraph.PropVals pvs = 4
                extra_pvs = _decode_prop_vals(oraw)

        node: dict[str, object] = {
            "typeOf": "StatVarObservation",
            "observationAbout": about,
            "variableMeasured": variable,
            "observationDate": date_str,
            "observationPeriod": period,
        }
        if extra_pvs:
            node.update(extra_pvs)
        if num_val is not None:
            node["_number_value"] = num_val
        elif text_val is not None:
            node["value"] = text_val
        yield node


def iter_tfrecord_payloads(tfrecord_path: Path):
    """Streams raw record payloads from a plain or gzip-compressed TFRecord."""
    with tfrecord_path.open("rb") as raw_fh:
        magic = raw_fh.read(2)
    is_gzip = tfrecord_path.name.endswith(".gz") or magic == b"\x1f\x8b"
    opener = gzip.open if is_gzip else open
    with opener(tfrecord_path, "rb") as fh:
        while True:
            header = fh.read(12)
            if not header:
                break
            if len(header) < 12:
                raise RuntimeError(
                    f"Truncated TFRecord header in {tfrecord_path}")
            rec_len, _crc_len = struct.unpack("<QI", header)
            body = fh.read(rec_len + 4)
            if len(body) < rec_len + 4:
                raise RuntimeError(
                    f"Truncated TFRecord payload in {tfrecord_path}")
            yield memoryview(body)[:rec_len]


def iter_svobs_from_tfrecord(tfrecord_path: Path):
    """Streams StatVarObservation dicts from an MCFOptimizedGraph TFRecord."""
    for payload in iter_tfrecord_payloads(tfrecord_path):
        for fnum, wtype, raw in _iter_proto_fields(payload):
            # MCFOptimizedGraph.sv_obs_series = 1
            if fnum == 1 and wtype == 2:
                yield from _decode_sv_obs_series(raw)


def iter_svobs_from_mcf(mcf_path: Path):
    """Streams StatVarObservation nodes from a text MCF file in O(1) memory."""
    node: dict[str, object] = {}

    def _is_svobs(cur: dict[str, object]) -> bool:
        return "StatVarObservation" in str(cur.get("typeOf", ""))

    with mcf_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                if node:
                    if _is_svobs(node):
                        yield node
                    node = {}
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key == "Node" and node:
                if _is_svobs(node):
                    yield node
                node = {}
            node[key] = val
    if node and _is_svobs(node):
        yield node


def iter_svobs_from_file(local_path: Path):
    """Dispatches local_path to the TFRecord or text MCF streaming parser."""
    if ".tfrecord" in local_path.name:
        yield from iter_svobs_from_tfrecord(local_path)
    else:
        yield from iter_svobs_from_mcf(local_path)


def parse_reim_csv_overrides(reim_csv_path: str) -> dict[tuple[str, str], str]:
    """Extracts Total priceAgeSexRace observations from legacy dartmouth_reim.csv."""
    overrides: dict[tuple[str, str], str] = {}
    with file_util.FileIO(reim_csv_path, mode="r", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        for raw_row in reader:
            row = {
                (k.lstrip("\ufeff").strip().lower() if k else ""):
                    (v or "").strip() for k, v in raw_row.items()
            }
            adj = strip_quotes_and_prefix(row.get("adjustmenttype", "")).lower()
            reim_for = strip_quotes_and_prefix(
                row.get("hasmedicarereimbursementfor", "")).lower()
            if adj and "priceagesexrace" not in adj:
                continue
            if reim_for and "total" not in reim_for:
                continue
            year = strip_quotes_and_prefix(
                row.get("year") or row.get("observationdate") or "")
            if not year.isdigit() or len(year) != 4:
                continue
            place = strip_quotes_and_prefix(
                row.get("geoid") or row.get("place") or
                row.get("observationabout") or "")
            if not place:
                continue
            if place.isdigit():
                code_int = int(place)
                place = ("country/USA" if code_int in (99, 99999) else
                         f"geoId/{code_int:05d}")
            if not is_valid_historical_place(place):
                continue
            val_parsed = clean_numeric_value(
                row.get("value") or row.get("reimbursement") or
                row.get("measuredvalue") or "")
            if val_parsed is None:
                continue
            overrides[(year, place)] = val_parsed[1]
    logging.info("Loaded %d Total priceAgeSexRace overrides from %s",
                 len(overrides), reim_csv_path)
    return overrides


def _is_canonical_reim_slice(node: dict[str, object]) -> tuple[bool, bool]:
    """Checks extra PVs on a reimbursement SVObs for (has_slice_tags, is_canonical).

    Returns:
      (True, True) if slice tags exist and match Total + priceAgeSexRace.
      (True, False) if slice tags exist and belong to a non-Total/ageSexRace slice.
      (False, False) if slice tags were stripped during StatPop conversion.
    """
    adj = strip_quotes_and_prefix(str(node.get("adjustmentType", ""))).lower()
    reim_for = strip_quotes_and_prefix(
        str(node.get("hasMedicareReimbursementFor", ""))).lower()
    if not adj and not reim_for:
        return False, False
    adj_ok = (not adj) or ("priceagesexrace" in adj)
    reim_ok = (not reim_for) or ("total" in reim_for)
    return True, (adj_ok and reim_ok)


def consolidate_baseline(
    source_dir: str,
    output_dir: Path,
    reim_csv: str = "",
) -> tuple[Path, Path, Path]:
    """Consolidates the 6 active legacy tables into CSV, TMCF, and MCF."""
    # Map (year, place_bare, sv_bare) -> (period, numeric_float, value_str, is_exact_reim)
    observations: dict[tuple[str, str, str], tuple[str, float, str, bool]] = {}
    missing_subtables: list[str] = []

    with tempfile.TemporaryDirectory() as tmp_str:
        stage_dir = Path(tmp_str)
        file_idx = 0
        for subtable in ACTIVE_SUBTABLES:
            data_files = list_subtable_data_files(source_dir, subtable)
            if not data_files:
                missing_subtables.append(subtable)
                continue

            table_rows = 0
            for remote_file in data_files:
                file_idx += 1
                local_file = stage_file_to_local(remote_file, stage_dir,
                                                 file_idx)
                for node in iter_svobs_from_file(local_file):
                    year = strip_quotes_and_prefix(
                        str(node.get("observationDate", "")))
                    if not year.isdigit() or len(year) != 4:
                        continue
                    place = strip_quotes_and_prefix(
                        str(node.get("observationAbout", "")))
                    if not place or "/" not in place:
                        continue
                    sv = strip_quotes_and_prefix(
                        str(node.get("variableMeasured", "")))
                    if sv not in ALLOWED_STAT_VARS:
                        continue

                    if "_number_value" in node:
                        val_parsed = format_finite_number(
                            float(node["_number_value"])
                        )  # type: ignore[arg-type]
                    else:
                        val_parsed = clean_numeric_value(
                            str(node.get("value", "")))
                    if val_parsed is None:
                        continue
                    val_float, val_str = val_parsed
                    period = (strip_quotes_and_prefix(
                        str(node.get("observationPeriod", ""))) or
                              DEFAULT_OBSERVATION_PERIOD)

                    key = (year, place, sv)
                    table_rows += 1
                    if sv == REIM_STAT_VAR:
                        has_tags, is_canonical = _is_canonical_reim_slice(node)
                        if has_tags and not is_canonical:
                            continue
                        existing = observations.get(key)
                        if is_canonical:
                            observations[key] = (period, val_float, val_str,
                                                 True)
                        elif existing is None or (not existing[3] and
                                                  val_float > existing[1]):
                            observations[key] = (period, val_float, val_str,
                                                 False)
                    elif key not in observations:
                        observations[key] = (period, val_float, val_str, False)

            logging.info("Parsed %d valid observations from %s (%d files)",
                         table_rows, subtable, len(data_files))

    if missing_subtables:
        raise RuntimeError(
            f"Missing required legacy Dartmouth Atlas sub-tables under "
            f"{source_dir}: {missing_subtables}")

    if reim_csv:
        reim_overrides = parse_reim_csv_overrides(reim_csv)
        replaced = 0
        for (year, place), val_str in reim_overrides.items():
            key = (year, place, REIM_STAT_VAR)
            if key in observations:
                observations[key] = (observations[key][0], float(val_str),
                                     val_str, True)
                replaced += 1
        logging.info("Applied %d canonical dartmouth_reim.csv overrides",
                     replaced)

    if not observations:
        raise RuntimeError(
            f"No valid StatVarObservations extracted from {source_dir}")

    sorted_items = sorted(observations.items())
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / HISTORICAL_CSV_FILENAME
    tmcf_path = output_dir / COMMON_TMCF_FILENAME
    mcf_path = output_dir / HISTORICAL_MCF_FILENAME

    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf, lineterminator="\n")
    writer.writerow(OUTPUT_COLUMNS)
    mcf_lines: list[str] = []

    csv_rows_written = 0
    for idx, ((year, place, sv), (period, _val_float, val_str,
                                  _exact)) in enumerate(sorted_items):
        about_dcid = f"dcid:{place}"
        sv_dcid = f"dcid:{sv}"
        obs_date_mcf = year if year.isdigit() else f'"{year}"'
        if is_valid_historical_place(place):
            writer.writerow([year, about_dcid, sv_dcid, val_str, period])
            csv_rows_written += 1
        mcf_lines.append(f"Node: E:DartmouthHistorical->E{idx}\n"
                         f"typeOf: dcs:StatVarObservation\n"
                         f"observationDate: {obs_date_mcf}\n"
                         f"observationAbout: {about_dcid}\n"
                         f"variableMeasured: {sv_dcid}\n"
                         f"value: {val_str}\n"
                         f'observationPeriod: "{period}"\n\n')

    atomic_write_text(csv_path, csv_buf.getvalue())
    atomic_write_text(tmcf_path, COMMON_TMCF_CONTENT)
    atomic_write_text(mcf_path, "".join(mcf_lines))

    unique_svs = sorted({sv for _, _, sv in observations})
    unique_places = {place for _, place, _ in observations}
    unique_years = sorted({year for year, _, _ in observations})
    logging.info(
        "Consolidated %d CSV observations and %d unaltered baseline MCF "
        "observations (%d invalid-place rows filtered from CSV; %d StatVars, "
        "%d places, %s..%s) -> %s, %s, %s",
        csv_rows_written,
        len(observations),
        len(observations) - csv_rows_written,
        len(unique_svs),
        len(unique_places),
        unique_years[0],
        unique_years[-1],
        csv_path,
        tmcf_path,
        mcf_path,
    )
    return csv_path, tmcf_path, mcf_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses CLI arguments for legacy CNS historical consolidation."""
    parser = argparse.ArgumentParser(description=(
        "Consolidates the 6 active legacy Dartmouth Atlas CNS tables."))
    parser.add_argument(
        "--cns_dir",
        default=DEFAULT_CNS_DIR,
        help=("Directory (CNS /cns/..., gs://..., or local path) containing "
              "the 6 active Dartmouth Atlas sub-table directories with "
              "graph.tfrecord* or nodes.mcf* files."),
    )
    parser.add_argument(
        "--reim_csv",
        default="",
        help=("Optional local or gs:// path to legacy dartmouth_reim.csv "
              "(gs://datcom-ext-tables/data/dartmouth_reim.csv) to extract "
              "canonical Total priceAgeSexRace values for dc/rn90czcrqcv06."),
    )
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for consolidated historical CSV, TMCF, and MCF.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    args = parse_args(argv)
    consolidate_baseline(
        source_dir=args.cns_dir,
        output_dir=Path(args.output_dir),
        reim_csv=args.reim_csv,
    )


if __name__ == "__main__":
    main()
