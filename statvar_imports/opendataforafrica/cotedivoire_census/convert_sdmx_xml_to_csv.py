# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Converts Côte d'Ivoire Census SDMX XML files to Data Commons CSV format."""

import contextlib
from decimal import Decimal
from decimal import InvalidOperation
import glob
import io
import math
import os
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import sdmx

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_HEX_ESCAPE_RE = re.compile(r'_[xX]([0-9A-Fa-f]{4})_')
_XML_LANG_ATTR = '{http://www.w3.org/XML/1998/namespace}lang'
_MAX_DECIMAL_EXPONENT = 1000
_NON_FINITE_STRINGS = frozenset({
    'nan',
    '+nan',
    '-nan',
    'snan',
    '+snan',
    '-snan',
    'inf',
    '+inf',
    '-inf',
    'infinity',
    '+infinity',
    '-infinity',
})
_CANONICAL_COLUMN_ALIASES = {
    'ID_D_PARTEMENT': 'ID_DÉPARTEMENT',
    'NOM_D_PARTEMENT': 'NOM_DÉPARTEMENT',
}

EXPECTED_TABLES = (
    'CIEI2010R',
    'akfhutb',
    'bdwcmfd',
    'hxghsjf',
    'hznvdtd',
    'jgwlmgg',
    'jynwpug',
    'kcnetge',
    'ojtbus',
    'qdanpdb',
    'rimffwf',
    'saxmnv',
    'wayfqyd',
    'wwamxhe',
    'yukugyf',
    'yxrzxug',
)


def _define_flags() -> None:
    """Registers CLI flags when executed as a standalone script."""
    flags_obj = flags.FLAGS
    if 'input_file' in flags_obj:
        return
    flags.DEFINE_string(
        'input_file',
        None,
        'Path to single SDMX XML file (e.g. raw_inputs/akfhutb.xml).',
    )
    flags.DEFINE_string(
        'xml_dir',
        None,
        'Path to directory containing SDMX XML files to convert.',
    )
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_MODULE_DIR, 'input_files'),
        'Directory where output CSVs should be written (default: input_files).',
    )
    flags.DEFINE_bool(
        'allow_empty_xml_dir',
        False,
        'Allow --xml_dir to have no .xml files when CSVs are pre-staged.',
    )
    flags.DEFINE_bool(
        'verify_expected_tables',
        False,
        'Verify all 16 expected Cotedivoire_Census CSV files exist.',
    )


def _local_tag(tag: str) -> str:
    """Strips XML namespace URI from an element tag."""
    return tag.split('}')[-1]


def _decode_knoema_text(text: str) -> str:
    """Decodes Knoema _xHHHH_ hex escapes and normalizes Unicode to NFC."""
    decoded = _HEX_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)
    return unicodedata.normalize('NFC', decoded)


def _strip_ns(attrib: dict[str, str]) -> dict[str, str]:
    """Strips XML namespace prefixes and normalizes keys/values."""
    return {
        _decode_knoema_text(k.split('}')[-1]): _decode_knoema_text(v)
        for k, v in attrib.items()
    }


def _is_missing_value(val: object) -> bool:
    """Safely checks whether a cell value is null/NaN/empty."""
    if val is None:
        return True
    if isinstance(val, str):
        return val.strip() == ''
    if isinstance(val, Decimal):
        return not val.is_finite()
    if isinstance(val, float):
        return math.isnan(val) or math.isinf(val)
    try:
        return bool(pd.isna(val))
    except (TypeError, ValueError, InvalidOperation):
        return False


def _format_obs_value(val: object) -> object:
    """Formats scientific-notation values as plain strings and clears NaN/Inf."""
    if val is None:
        return val
    if isinstance(val, Decimal):
        if not val.is_finite():
            return ''
        if val.is_zero():
            return '0'
        if abs(val.adjusted()) > _MAX_DECIMAL_EXPONENT:
            return str(val)
        formatted = format(val, 'f')
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return '0' if formatted in ('', '-0', '+0') else formatted
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return ''
    else:
        try:
            if pd.isna(val):
                return ''
        except (TypeError, ValueError, InvalidOperation):
            pass

    s = str(val).strip()
    if s.lower() in _NON_FINITE_STRINGS:
        return ''
    if 'e' not in s.lower():
        return val
    try:
        dec = Decimal(s)
        if not dec.is_finite():
            return ''
        if dec.is_zero():
            return '0'
        if abs(dec.adjusted()) > _MAX_DECIMAL_EXPONENT:
            return str(dec)
        formatted = format(dec, 'f')
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        if formatted in ('', '-0', '+0'):
            return '0'
        return formatted
    except InvalidOperation:
        return val


def _normalize_cell_value(val: object) -> object:
    """Normalizes string cell values (hex escapes + NFC) without casting."""
    if isinstance(val, str):
        return _decode_knoema_text(val)
    return val


def _canonicalize_col_name(raw_col: object) -> str:
    """Normalizes a column header to uppercase NFC and canonical aliases."""
    col = _decode_knoema_text(str(raw_col)).lstrip('@').strip().upper()
    return _CANONICAL_COLUMN_ALIASES.get(col, col)


def _coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicates columns that normalize to the same name via coalescing."""
    raw_cols = [str(c) for c in df.columns]
    norm_cols = [_canonicalize_col_name(c) for c in df.columns]

    grouped_indices: dict[str, list[int]] = {}
    for idx, norm_name in enumerate(norm_cols):
        if norm_name == '':
            continue
        grouped_indices.setdefault(norm_name, []).append(idx)

    if not grouped_indices:
        return pd.DataFrame(index=df.index)

    has_duplicates = any(len(idxs) > 1 for idxs in grouped_indices.values())
    if not has_duplicates and list(grouped_indices.keys()) == norm_cols:
        out = df.copy()
        out.columns = norm_cols
        return out

    series_map: dict[str, pd.Series] = {}
    for norm_name, idxs in grouped_indices.items():
        if len(idxs) == 1:
            series_map[norm_name] = df.iloc[:, idxs[0]].copy()
            continue
        # Prefer non-'@'-prefixed columns over '@'-prefixed attribute duplicates.
        ordered_idxs = sorted(idxs,
                              key=lambda i: 1
                              if raw_cols[i].strip().startswith('@') else 0)
        combined = df.iloc[:, ordered_idxs[0]].copy()
        for next_idx in ordered_idxs[1:]:
            candidate = df.iloc[:, next_idx]
            mask = combined.map(_is_missing_value)
            if mask.any():
                combined = combined.where(~mask, candidate)
        series_map[norm_name] = combined

    return pd.DataFrame(series_map, index=df.index)


def _normalize_obs_column(
    df: pd.DataFrame,
    xml_path: str | None = None,
) -> pd.DataFrame:
    """Normalizes columns/values, formats OBS_VALUE, and places OBS_VALUE last.

    Args:
      df: Raw DataFrame produced by sdmx1 or ElementTree parsing.
      xml_path: Optional source XML path for error reporting.

    Returns:
      Normalized DataFrame with 'OBS_VALUE' as the final column.

    Raises:
      ValueError: If 'OBS_VALUE' is missing after normalization.
    """
    df = _coalesce_duplicate_columns(df)

    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].map(_normalize_cell_value)

    if 'OBS_VALUE' not in df.columns:
        if 'VALUE' in df.columns:
            df = df.rename(columns={'VALUE': 'OBS_VALUE'})
        elif '0' in df.columns:
            df = df.rename(columns={'0': 'OBS_VALUE'})

    if len(df.columns) == 0 or 'OBS_VALUE' not in df.columns:
        source_desc = f' in {xml_path}' if xml_path else ''
        raise ValueError(f"Missing 'OBS_VALUE' column{source_desc}")

    df['OBS_VALUE'] = df['OBS_VALUE'].map(_format_obs_value)
    ordered_cols = [c for c in df.columns if c != 'OBS_VALUE'] + ['OBS_VALUE']
    return df[ordered_cols]


def _to_normalized_df(
    obj: object,
    xml_path: str | None = None,
) -> pd.DataFrame | None:
    """Converts a parsed sdmx1 DataFrame or Series into a normalized DataFrame."""
    if isinstance(obj, pd.DataFrame):
        if isinstance(obj.index, pd.MultiIndex) or obj.index.name is not None:
            df = obj.reset_index()
        else:
            df = obj.copy()
    elif isinstance(obj, pd.Series):
        if isinstance(obj.index, pd.MultiIndex) or obj.index.name is not None:
            df = obj.reset_index()
        else:
            df = obj.to_frame()
    elif hasattr(obj, 'reset_index'):
        df = obj.reset_index()
    else:
        return None
    if df.empty:
        return None
    return _normalize_obs_column(df, xml_path=xml_path)


def _extract_codelists(root: ET.Element) -> dict[str, dict[str, str]]:
    """Extracts Codelist ID -> {code_id: French/default label} from SDMX XML."""
    codelists: dict[str, dict[str, str]] = {}
    for elem in root.iter():
        if _local_tag(elem.tag) != 'Codelist':
            continue
        cl_id = _decode_knoema_text(elem.attrib.get('id', '')).strip().upper()
        if not cl_id:
            continue
        codes: dict[str, str] = {}
        for code_elem in elem:
            if _local_tag(code_elem.tag) != 'Code':
                continue
            code_id = _decode_knoema_text(
                code_elem.attrib.get('id', '') or
                code_elem.attrib.get('value', '')).strip()
            if not code_id:
                continue
            fr_name = None
            default_name = None
            fr_desc = None
            default_desc = None
            for child in code_elem:
                child_tag = _local_tag(child.tag)
                if child_tag not in ('Name',
                                     'Description') or not (child.text and
                                                            child.text.strip()):
                    continue
                label = _decode_knoema_text(child.text.strip())
                lang = (child.attrib.get(_XML_LANG_ATTR) or
                        child.attrib.get('lang') or '').lower()
                if child_tag == 'Name':
                    if lang.startswith('fr') and fr_name is None:
                        fr_name = label
                    if default_name is None:
                        default_name = label
                else:
                    if lang.startswith('fr') and fr_desc is None:
                        fr_desc = label
                    if default_desc is None:
                        default_desc = label
            chosen = fr_name or default_name or fr_desc or default_desc
            if chosen:
                codes[code_id] = chosen
        if codes:
            codelists[cl_id] = codes
            base_id = cl_id[3:] if cl_id.startswith('CL_') else cl_id
            codelists[base_id] = codes
            if base_id in ('DÉPARTEMENT', 'D_PARTEMENT', 'DEPARTEMENT'):
                for alias in ('DÉPARTEMENT', 'D_PARTEMENT'):
                    codelists.setdefault(alias, codes)
                    codelists.setdefault(f'CL_{alias}', codes)
    return codelists


def _target_id_and_nom_cols(dim: str) -> tuple[str, str]:
    """Returns canonical (ID_<dim>, NOM_<dim>) column names for a dimension."""
    if dim == 'D_PARTEMENT':
        return 'ID_DÉPARTEMENT', 'NOM_DÉPARTEMENT'
    return f'ID_{dim}', f'NOM_{dim}'


def _enrich_series_from_codelists(
    row_attrib: dict[str, str],
    codelists: dict[str, dict[str, str]],
) -> dict[str, str]:
    """Enriches row attributes from inline Codelists and department aliases."""
    enriched = dict(row_attrib)
    upper_keys = {_canonicalize_col_name(k) for k in enriched}
    for key, val in list(row_attrib.items()):
        dim = _canonicalize_col_name(key)
        if dim in ('FREQ', 'TIME_PERIOD', 'OBS_VALUE',
                   'VALUE') or dim.startswith(('ID_', 'NOM_', 'LIBELLE_')):
            continue
        id_col, nom_col = _target_id_and_nom_cols(dim)
        if dim == 'D_PARTEMENT' and id_col not in upper_keys:
            enriched[id_col] = val
            upper_keys.add(id_col)
        if not codelists:
            continue
        code_map = codelists.get(dim) or codelists.get(f'CL_{dim}')
        if not code_map or val not in code_map:
            continue
        if id_col not in upper_keys:
            enriched[id_col] = val
            upper_keys.add(id_col)
        lib_col = f'LIBELLE_FRANCAIS_{dim}'
        if nom_col not in upper_keys and lib_col not in upper_keys:
            enriched[nom_col] = code_map[val]
            upper_keys.add(nom_col)
    return enriched


def _enrich_dataframe_from_codelists(
    df: pd.DataFrame,
    codelists: dict[str, dict[str, str]],
) -> pd.DataFrame:
    """Enriches a normalized DataFrame with ID_* / NOM_* columns if missing."""
    df = df.copy()
    if 'D_PARTEMENT' in df.columns and 'ID_DÉPARTEMENT' not in df.columns:
        df['ID_DÉPARTEMENT'] = df['D_PARTEMENT']

    if not codelists:
        ordered = [c for c in df.columns if c != 'OBS_VALUE'] + ['OBS_VALUE']
        return df[ordered]

    for dim in list(df.columns):
        if dim in ('FREQ', 'TIME_PERIOD', 'OBS_VALUE',
                   'VALUE') or dim.startswith(('ID_', 'NOM_', 'LIBELLE_')):
            continue
        code_map = codelists.get(dim) or codelists.get(f'CL_{dim}')
        if not code_map:
            continue
        col_series = df[dim]
        has_known_code = col_series.map(lambda v, cm=code_map: (
            not _is_missing_value(v)) and str(v) in cm).any()
        if not has_known_code:
            continue
        id_col, nom_col = _target_id_and_nom_cols(dim)
        if id_col not in df.columns:
            df[id_col] = col_series
        lib_col = f'LIBELLE_FRANCAIS_{dim}'
        if nom_col not in df.columns and lib_col not in df.columns:
            df[nom_col] = col_series.map(lambda v, cm=code_map: cm.get(
                str(v), '') if not _is_missing_value(v) else '')

    ordered = [c for c in df.columns if c != 'OBS_VALUE'] + ['OBS_VALUE']
    return df[ordered]


def _extract_kv_children(container: ET.Element) -> dict[str, str]:
    """Extracts <Value id/concept='...' value='...'/> pairs from GenericData."""
    kv: dict[str, str] = {}
    for val_elem in container:
        if _local_tag(val_elem.tag) != 'Value':
            continue
        v_attrib = _strip_ns(val_elem.attrib)
        key = (v_attrib.get('id') or v_attrib.get('ID') or
               v_attrib.get('concept') or v_attrib.get('CONCEPT') or
               '').strip()
        val = v_attrib.get('value')
        if val is None:
            val = v_attrib.get('VALUE')
        if val is None and val_elem.text:
            val = _decode_knoema_text(val_elem.text.strip())
        if key and val is not None:
            kv[key] = val
    return kv


def _extract_series_dict(series_elem: ET.Element) -> dict[str, str]:
    """Extracts Series attributes from StructureSpecific or GenericData XML."""
    data = _strip_ns(series_elem.attrib)
    for child in series_elem:
        if _local_tag(child.tag) in ('SeriesKey', 'Attributes'):
            data.update(_extract_kv_children(child))
    return data


def _extract_obs_dict(obs_elem: ET.Element) -> dict[str, str]:
    """Extracts Obs attributes/values from StructureSpecific or GenericData."""
    data = _strip_ns(obs_elem.attrib)
    for child in obs_elem:
        ctag = _local_tag(child.tag)
        if ctag in ('ObsKey', 'Attributes'):
            data.update(_extract_kv_children(child))
        elif ctag == 'ObsDimension':
            c_attr = _strip_ns(child.attrib)
            dim_id = (c_attr.get('id') or c_attr.get('ID') or
                      c_attr.get('concept') or 'TIME_PERIOD').strip()
            dim_val = (c_attr['value']
                       if 'value' in c_attr else c_attr.get('VALUE'))
            if dim_val is None and child.text:
                dim_val = _decode_knoema_text(child.text.strip())
            if dim_val is not None:
                data[dim_id] = dim_val
        elif ctag in ('Time', 'TIME_PERIOD'):
            if child.text and child.text.strip():
                data['TIME_PERIOD'] = _decode_knoema_text(child.text.strip())
        elif ctag == 'ObsValue':
            c_attr = _strip_ns(child.attrib)
            obs_val = (c_attr['value']
                       if 'value' in c_attr else c_attr.get('VALUE'))
            if obs_val is None and child.text:
                obs_val = _decode_knoema_text(child.text.strip())
            if obs_val is not None:
                data['OBS_VALUE'] = obs_val
    return data


def convert_sdmx_xml_to_dataframe(xml_path: str) -> pd.DataFrame:
    """Reads an SDMX XML file using sdmx1 or ElementTree into a DataFrame.

    Args:
      xml_path: Path to the input SDMX XML file.

    Returns:
      A normalized pandas DataFrame with uppercase NFC column headers,
      expanded scientific-notation numbers, Codelist-enriched ID_*/NOM_* columns
      when applicable, and 'OBS_VALUE' ordered as the final column.

    Raises:
      FileNotFoundError: If xml_path does not exist.
      ValueError: If xml_path is malformed XML, contains no observations, or
        lacks an 'OBS_VALUE' column.
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f'XML file not found: {xml_path}')

    with open(xml_path, 'rb') as f:
        xml_bytes = f.read()

    root = None
    xml_parse_error = None
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        xml_parse_error = e

    codelists = _extract_codelists(root) if root is not None else {}

    # 1. Primary path: read SDMX XML with sdmx1.
    parsed = None
    try:
        with contextlib.redirect_stdout(
                io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            msg = sdmx.read_sdmx(io.BytesIO(xml_bytes), format='XML')
            try:
                parsed = sdmx.to_pandas(msg, attributes='osgd', dtype=object)
            except TypeError:
                parsed = sdmx.to_pandas(msg)
    except Exception as e:
        logging.info('sdmx parser skipped for %s (%s); attempting fallback',
                     xml_path, e)

    if parsed is not None:
        if isinstance(parsed, dict):
            dfs = []
            for v in parsed.values():
                norm_v = _to_normalized_df(v, xml_path=xml_path)
                if norm_v is not None:
                    dfs.append(norm_v)
            if dfs:
                combined_df = _normalize_obs_column(pd.concat(
                    dfs, ignore_index=True),
                                                    xml_path=xml_path)
                return _enrich_dataframe_from_codelists(combined_df, codelists)
        else:
            norm_df = _to_normalized_df(parsed, xml_path=xml_path)
            if norm_df is not None:
                return _enrich_dataframe_from_codelists(norm_df, codelists)

    # 2. Fallback path for headerless, StructureSpecific, or GenericData XMLs.
    if root is None:
        logging.error('Failed to parse XML file %s: %s', xml_path,
                      xml_parse_error)
        raise ValueError(
            f'Failed to parse XML file {xml_path}: {xml_parse_error}'
        ) from xml_parse_error

    rows = []
    for elem in root.iter():
        tag = _local_tag(elem.tag)
        if tag == 'Series':
            series_attrib = _enrich_series_from_codelists(
                _extract_series_dict(elem), codelists)
            for child in elem:
                if _local_tag(child.tag) == 'Obs':
                    obs_attrib = _extract_obs_dict(child)
                    rows.append(
                        _enrich_series_from_codelists(
                            {
                                **series_attrib,
                                **obs_attrib,
                            }, codelists))
        elif tag == 'DataSet':
            for child in elem:
                if _local_tag(child.tag) == 'Obs':
                    obs_attrib = _enrich_series_from_codelists(
                        _extract_obs_dict(child), codelists)
                    rows.append(obs_attrib)

    if not rows:
        raise ValueError(f'No <Series> or <Obs> records found in {xml_path}')

    df = _normalize_obs_column(pd.DataFrame(rows), xml_path=xml_path)
    return _enrich_dataframe_from_codelists(df, codelists)


def convert_sdmx_xml_to_csv(xml_path: str, output_csv_path: str) -> None:
    """Converts an SDMX XML file to a CSV file atomically.

    Args:
      xml_path: Path to the input SDMX XML file.
      output_csv_path: Destination path for the normalized CSV file.

    Raises:
      FileNotFoundError: If xml_path does not exist.
      ValueError: If xml_path cannot be parsed into valid observations.
      OSError: If writing or replacing output_csv_path fails.
    """
    df = convert_sdmx_xml_to_dataframe(xml_path)
    out_dir = os.path.dirname(os.path.abspath(output_csv_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            df.to_csv(f, index=False)
        os.replace(tmp_path, output_csv_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    logging.info('Converted %s -> %s (%d rows)', xml_path, output_csv_path,
                 len(df))


def _verify_expected_csvs(output_dir: str) -> None:
    """Verifies that all 16 expected CSV tables exist and are non-empty.

    Args:
      output_dir: Directory expected to contain `<table_id>.csv` files.

    Raises:
      FileNotFoundError: If one or more expected CSV files are missing or empty.
    """
    missing_or_empty: list[str] = []
    for table_id in EXPECTED_TABLES:
        csv_file = os.path.join(output_dir, f'{table_id}.csv')
        if not os.path.isfile(csv_file) or os.path.getsize(csv_file) == 0:
            missing_or_empty.append(csv_file)
    if missing_or_empty:
        raise FileNotFoundError(
            f'Missing or empty {len(missing_or_empty)} expected CSV file(s): '
            f'{", ".join(missing_or_empty)}')


def main(argv: list[str] | None = None) -> None:
    """Runs CLI conversion of SDMX XML file(s) to Data Commons CSV format.

    Args:
      argv: Command-line arguments passed by absl.app.run.

    Raises:
      ValueError: If unexpected positional arguments are provided or if neither
        or both of --input_file and --xml_dir are set.
      FileNotFoundError: If the requested input file, XML directory, or any
        expected output CSV table is missing or empty.
    """
    if argv and len(argv) > 1:
        raise ValueError(f'Unexpected positional arguments: {argv[1:]}')

    flags_obj = flags.FLAGS
    input_file = flags_obj.input_file
    xml_dir = flags_obj.xml_dir
    output_dir = flags_obj.output_dir
    allow_empty_xml_dir = flags_obj.allow_empty_xml_dir
    verify_expected_tables = flags_obj.verify_expected_tables

    if bool(input_file) == bool(xml_dir):
        raise ValueError(
            'Exactly one of --input_file or --xml_dir must be specified.')

    if input_file:
        resolved_input = os.path.abspath(input_file)
        if not os.path.isfile(resolved_input):
            raise FileNotFoundError(f'Input file not found: {resolved_input}')
        base_name = os.path.splitext(os.path.basename(resolved_input))[0]
        out_csv = os.path.join(output_dir, f'{base_name}.csv')
        convert_sdmx_xml_to_csv(resolved_input, out_csv)
        if verify_expected_tables:
            _verify_expected_csvs(output_dir)
        return

    resolved_xml_dir = os.path.abspath(xml_dir)
    if not os.path.isdir(resolved_xml_dir):
        if not allow_empty_xml_dir:
            raise FileNotFoundError(
                f'XML directory not found: {resolved_xml_dir}')
        xml_files = []
    else:
        xml_files = sorted(glob.glob(os.path.join(resolved_xml_dir, '*.xml')))

    if not xml_files:
        if not allow_empty_xml_dir:
            raise FileNotFoundError(
                f'No XML files found in directory: {resolved_xml_dir}')
        logging.info(
            'No XML files found in %s; skipping XML conversion '
            '(--allow_empty_xml_dir)',
            resolved_xml_dir,
        )
    else:
        for xf in xml_files:
            base_name = os.path.splitext(os.path.basename(xf))[0]
            out_csv = os.path.join(output_dir, f'{base_name}.csv')
            convert_sdmx_xml_to_csv(xf, out_csv)

    if verify_expected_tables:
        _verify_expected_csvs(output_dir)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
