# Copyright 2022 Google LLC
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
"""Loads NCES NAEP datasets, filters redundant rows, and writes CSV/MCF/TMCF.

Before running this module, run download_input_files.py to download input CSVs
into input_files/.

Folder layout:
  input_files - downloaded CSV files from the NCES NAEP API
  output - generated cleaned CSV, MCF, and TMCF outputs
"""

import os
import re
import sys
from typing import Callable, Optional

from absl import app
from absl import flags
from absl import logging

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MODULE_DIR, '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(1, REPO_ROOT)

# pylint:disable=wrong-import-position,import-error
from scripts.nces_nationsreportcard.config.conf import denominator_ignore_prop
# pylint:enable=wrong-import-position,import-error

_FLAGS = flags.FLAGS

_SUPPRESSED_VALUES = frozenset({'', '999', '999.0'})
_SECTOR_JURISDICTIONS = frozenset({'NP', 'NR', 'NL'})
_PRIVATE_JURISDICTIONS = frozenset({'NR', 'NL'})
_REQUIRED_FAST_COLS = frozenset({
    'year',
    'CohortLabel',
    'stattype',
    'subject',
    'scale',
    'jurisdiction',
    'varValueLabel',
    'value',
})
PERCENT_PROPERTY_NODE = ('\nNode: dcid:percent\n'
                         'typeOf: schema:Property\n'
                         'name: "percent"\n'
                         'domainIncludes: dcs:Student\n')

_PROCESSOR_RUNTIME: Optional[tuple] = None


def strip_mcf_namespace(value: str) -> str:
    """Strips a leading MCF namespace prefix such as `dcs:` or `dcid:`."""
    if value and isinstance(value, str):
        if '"' in value:
            return value
        pos = 0
        while pos < len(value) and value[pos].isalpha():
            pos += 1
        if pos < len(value) and value[pos] == ':':
            return value[pos + 1:].strip()
    return value


def is_valid_mcf_property(prop: str, schemaless: bool = False) -> bool:
    """Returns True if `prop` is a valid MCF property name."""
    if prop and isinstance(prop, str) and prop[0].isalpha():
        if schemaless or prop[0].islower():
            return True
    return False


def is_valid_mcf_value(value: str) -> bool:
    """Returns True if `value` is a non-empty resolved MCF value."""
    if value is None:
        return False
    if isinstance(value, str):
        if not value or value == '""':
            return False
        if '@' in value and not re.search('@[a-z]{2}"$', value):
            return False
        if '{' in value and '}' in value:
            return False
    return True


def is_redundant_naep_row(jurisdiction: str, variable: str,
                          stattype: str) -> bool:
    """Returns True if a raw NAEP row encodes a redundant or tautological SV.

    Specifically filters:
      1. NP/NR/NL x SCHTYPE: double-tags both schoolType and schoolManagement.
      2. NR/NL x CHRTRPT: tautological NCES_PrivateSchool x NCES_CharterNo
         (100% identical to NR + TOTAL since private schools are non-charter).
      3. TOTAL x RP:RP: constant 100% row-percentage total ("All students").
    """
    if jurisdiction in _SECTOR_JURISDICTIONS and variable == 'SCHTYPE':
        return True
    if jurisdiction in _PRIVATE_JURISDICTIONS and variable == 'CHRTRPT':
        return True
    if variable == 'TOTAL' and stattype == 'RP:RP':
        return True
    return False


def should_drop_naep_row(row: list, header_map: Optional[dict]) -> bool:
    """Checks whether a parsed data row is suppressed or redundant."""
    if not header_map:
        return False
    idx_val = header_map.get('value')
    if idx_val is not None and idx_val < len(row):
        if row[idx_val].strip() in _SUPPRESSED_VALUES:
            return True
    idx_disp = header_map.get('isStatDisplayable')
    if idx_disp is not None and idx_disp < len(row):
        if row[idx_disp].strip() == '0':
            return True
    idx_juris = header_map.get('jurisdiction')
    idx_var = header_map.get('variable')
    idx_stat = header_map.get('stattype')
    juris = (row[idx_juris].strip()
             if idx_juris is not None and idx_juris < len(row) else '')
    var = (row[idx_var].strip()
           if idx_var is not None and idx_var < len(row) else '')
    stat = (row[idx_stat].strip()
            if idx_stat is not None and idx_stat < len(row) else '')
    return is_redundant_naep_row(juris, var, stat)


def should_ignore_naep_pvs(pvs: dict) -> bool:
    """Returns True if mapped PVs represent a suppressed or redundant StatVar."""
    if str(pvs['value']).strip() in _SUPPRESSED_VALUES:
        return True
    if 'schoolType' in pvs and 'schoolManagement' in pvs:
        return True
    if (strip_mcf_namespace(pvs.get('schoolType', '')) == 'NCES_PrivateSchool'
            and 'charterStatus' in pvs):
        return True
    return False


def build_denominator_pvs(
    pvs: dict,
    default_svobs_pvs: dict,
    internal_reference_keys: set,
    schemaless: bool = False,
) -> dict:
    """Builds Count_Student_* denominator PVs for achievement-level PVs."""
    if 'educationalAchievementLevel' not in pvs:
        return {}
    denom_pvs = {}
    for key, value in pvs.items():
        if (key not in denominator_ignore_prop and
                key not in default_svobs_pvs and
                key not in internal_reference_keys and
                is_valid_mcf_property(key, schemaless) and
                is_valid_mcf_value(value)):
            denom_pvs[key] = value
    denom_pvs['measuredProperty'] = 'dcs:count'
    denom_pvs['populationType'] = 'dcs:Student'
    return denom_pvs


def _percent_has_student_domain(node_pvs: dict) -> bool:
    """Returns True if `domainIncludes` on `node_pvs` includes `Student`."""
    domain_includes = node_pvs.get('domainIncludes', '')
    if isinstance(domain_includes, str):
        tokens = domain_includes.split(',')
    else:
        tokens = list(domain_includes)
    domains = {
        strip_mcf_namespace(token.strip())
        for token in tokens
        if token and token.strip()
    }
    return 'Student' in domains


def should_emit_percent_student_domain(
    config: dict,
    lookup_fn: Optional[Callable[[list, dict], dict]] = None,
) -> bool:
    """Returns True when `Node: dcid:percent` with `dcs:Student` should be emitted.

    Respects optional config key `emit_percent_student_domain` (default None):
      - False: skip emission.
      - True: always emit.
      - None: query DC API for `percent` via `dc_api_wrapper` and skip if
        `Student` is already in `domainIncludes`; fall back to emitting on error.
    """
    override = config.get('emit_percent_student_domain')
    if override is not None:
        return bool(override)
    if lookup_fn is None:
        _ensure_processor_paths()
        # pylint:disable=import-outside-toplevel,import-error
        from dc_api_wrapper import dc_api_get_node_property_values
        # pylint:enable=import-outside-toplevel,import-error
        lookup_fn = dc_api_get_node_property_values
    try:
        response = lookup_fn(['percent'], config) or {}
    except Exception as err:  # pylint:disable=broad-except
        logging.warning(
            'Unable to inspect dcid:percent domainIncludes (%s); emitting '
            'fallback Property node.', err)
        return True
    percent_pvs = (response.get('dcid:percent') or response.get('percent') or
                   {})
    return not _percent_has_student_domain(percent_pvs)


def append_percent_domain_includes(
    statvar_mcf_file: str,
    config: dict,
    lookup_fn: Optional[Callable[[list, dict], dict]] = None,
) -> bool:
    """Appends `Node: dcid:percent` idempotently when Student domain is needed."""
    if not os.path.exists(statvar_mcf_file):
        return False
    with open(statvar_mcf_file, 'r', encoding='utf-8') as mcf_file:
        content = mcf_file.read()
    if 'Node: dcid:percent' in content:
        return False
    if not should_emit_percent_student_domain(config, lookup_fn=lookup_fn):
        return False
    with open(statvar_mcf_file, 'a', encoding='utf-8') as mcf_file:
        mcf_file.write(PERCENT_PROPERTY_NODE)
    return True


def _ensure_processor_paths() -> None:
    """Adds StatVar importer and util directories to sys.path lazily."""
    for path in (
            os.path.join(REPO_ROOT, 'tools', 'statvar_importer'),
            os.path.join(REPO_ROOT, 'util'),
    ):
        if path not in sys.path:
            sys.path.insert(1, path)


def _load_processor_runtime() -> tuple:
    """Lazily imports StatVarDataProcessor and defines NaepEduPerformance.

    Keeping `stat_var_processor` and `mcf_file_util` imports out of module import
    time prevents global absl.flags (`--output_path`, `--input_file`, `--debug`)
    from colliding across unrelated test modules during `unittest discover`.
    """
    global _PROCESSOR_RUNTIME  # pylint:disable=global-statement
    if _PROCESSOR_RUNTIME is not None:
        return _PROCESSOR_RUNTIME

    _ensure_processor_paths()
    # pylint:disable=import-outside-toplevel,import-error,too-few-public-methods,protected-access
    from mcf_file_util import get_numeric_value
    from stat_var_processor import StatVarDataProcessor, process

    class NaepEduPerformance(StatVarDataProcessor):
        """Custom StatVarDataProcessor for NCES Nation's Report Card (NAEP)."""

        _import_name = 'naep'
        input_path = os.path.join(MODULE_DIR, 'input_files')

        def __init__(self,
                     pv_mapper=None,
                     config_dict: dict = None,
                     counters_dict: dict = None):
            super().__init__(pv_mapper=pv_mapper,
                             config_dict=config_dict,
                             counters_dict=counters_dict)
            self._header_map = None
            self._fast_cols = None
            self._sv_template_cache = {}
            self._place_cache = {}
            self._date_cache = {}
            self._denom_dcid_cache = {}

        def init_file_state(self, filename: str):
            super().init_file_state(filename)
            self._header_map = None
            self._fast_cols = None

        def preprocess_row(self, row: list, row_index: int) -> list:
            """Filters suppressed and redundant rows on uncached path."""
            if row_index > 1 and self._fast_cols is None:
                if should_drop_naep_row(row, self._header_map):
                    return []
            return row

        def process_row(self, row: list, row_index: int):
            """Processes a CSV row with exact StatVar PV memoization."""
            if row_index == 1:
                self._header_map = {
                    col.strip(): idx for idx, col in enumerate(row)
                }
                if (_REQUIRED_FAST_COLS.issubset(self._header_map.keys()) and
                        self._config.get('enable_naep_fast_path', True)):
                    hm = self._header_map
                    req_indices = [hm[c] for c in _REQUIRED_FAST_COLS]
                    self._fast_cols = (
                        hm['year'],
                        hm['CohortLabel'],
                        hm['stattype'],
                        hm['subject'],
                        hm['scale'],
                        hm['jurisdiction'],
                        hm.get('variable'),
                        hm['varValueLabel'],
                        hm['value'],
                        hm.get('isStatDisplayable'),
                        max(req_indices),
                    )
                super().process_row(row, row_index)
                return

            if self._fast_cols is None:
                super().process_row(row, row_index)
                return

            (idx_year, idx_cohort, idx_stat, idx_subj, idx_scale, idx_juris,
             idx_var, idx_var_label, idx_val, idx_disp,
             max_req) = self._fast_cols
            if len(row) <= max_req:
                super().process_row(row, row_index)
                return

            val_str = row[idx_val].strip()
            if val_str in _SUPPRESSED_VALUES or (idx_disp is not None and
                                                 idx_disp < len(row) and
                                                 row[idx_disp].strip() == '0'):
                self._counters.add_counter('input-rows-ignored-preprocess', 1,
                                           self.get_current_filename())
                return

            jurisdiction = row[idx_juris].strip()
            stattype = row[idx_stat].strip()
            variable = (row[idx_var].strip()
                        if idx_var is not None and idx_var < len(row) else '')
            if is_redundant_naep_row(jurisdiction, variable, stattype):
                self._counters.add_counter('input-rows-ignored-preprocess', 1,
                                           self.get_current_filename())
                return

            sv_cache_key = (
                row[idx_cohort].strip(),
                stattype,
                row[idx_subj].strip(),
                row[idx_scale].strip(),
                jurisdiction if jurisdiction in _SECTOR_JURISDICTIONS else '',
                row[idx_var_label].strip(),
            )
            template = self._sv_template_cache.get(sv_cache_key)
            if template is None:
                obs_map = self._statvars_map._statvar_obs_map
                prev_len = len(obs_map)
                super().process_row(row, row_index)
                if len(obs_map) > prev_len:
                    added = next(reversed(obs_map.values()))
                    self._sv_template_cache[sv_cache_key] = dict(added)
                    self._place_cache[jurisdiction] = added['observationAbout']
                    self._date_cache[row[idx_year].strip()] = (
                        added['observationDate'])
                return

            place_dcid = self._place_cache.get(jurisdiction)
            if place_dcid is None:
                place_pvs = self.resolve_value_references(
                    self._pv_mapper.get_all_pvs_for_value(
                        jurisdiction, 'jurisdiction') or [])
                if not place_pvs or not self.resolve_svobs_place(place_pvs):
                    super().process_row(row, row_index)
                    return
                place_dcid = place_pvs['observationAbout']
                self._place_cache[jurisdiction] = place_dcid

            year_raw = row[idx_year].strip()
            obs_date = self._date_cache.get(year_raw)
            if obs_date is None:
                year_num = get_numeric_value(year_raw)
                if year_num is None:
                    super().process_row(row, row_index)
                    return
                date_pvs = {'observationDate': str(year_num)}
                if not self.resolve_svobs_date(date_pvs):
                    super().process_row(row, row_index)
                    return
                obs_date = date_pvs['observationDate']
                self._date_cache[year_raw] = obs_date

            num_val = get_numeric_value(val_str)
            if num_val is None:
                super().process_row(row, row_index)
                return

            input_ref_col = self._config.get('input_reference_column', '#input')
            svobs_pvs = dict(template)
            svobs_pvs['observationDate'] = obs_date
            svobs_pvs['observationAbout'] = place_dcid
            svobs_pvs['value'] = str(num_val)
            svobs_pvs[input_ref_col] = (
                f'{self._context.get("__FILE__")}:{row_index}:{idx_val + 1}')

            statvar_dcid = strip_mcf_namespace(svobs_pvs['variableMeasured'])
            if not self._statvars_map.add_statvar_obs(svobs_pvs):
                self._counters.add_counter('dropped-svobs-invalid', 1,
                                           statvar_dcid)
                self._counters.add_counter('input-rows-processed', 1,
                                           self.get_current_filename())
                return

            self._counters.add_counter('generated-statvars', 1, statvar_dcid)
            self._counters.add_counter('generated-svobs', 1, statvar_dcid)
            self._counters.add_counter(
                'generated-svobs-' + self.get_current_filename(), 1)
            self._section_svobs += 1
            self._counters.add_counter('input-data-rows', 1,
                                       self.get_current_filename())
            self._counters.add_counter('input-rows-processed', 1,
                                       self.get_current_filename())

        def preprocess_stat_var_obs_pvs(self, pvs: dict) -> list:
            """Filters suppressed/redundant PVs and registers denominator SVs."""
            if 'value' not in pvs:
                return [pvs]
            if should_ignore_naep_pvs(pvs):
                pvs['#ignore'] = True
                return [pvs]

            denom_pvs = build_denominator_pvs(
                pvs,
                self._config.get('default_svobs_pvs', {}),
                self._internal_reference_keys,
                self._config.get('schemaless', False),
            )
            if denom_pvs:
                denom_cache_key = tuple(sorted(denom_pvs.items()))
                denominator_dcid = self._denom_dcid_cache.get(denom_cache_key)
                if not denominator_dcid:
                    denominator_dcid = self.process_stat_var_pvs(denom_pvs)
                    if not denominator_dcid:
                        raise RuntimeError(
                            'Failed to register measurementDenominator StatVar:'
                            f' {denom_pvs}')
                    denominator_dcid = strip_mcf_namespace(denominator_dcid)
                    self._denom_dcid_cache[denom_cache_key] = denominator_dcid
                pvs['measurementDenominator'] = f'dcid:{denominator_dcid}'
            return [pvs]

        def write_outputs(self, output_path: str):
            """Writes outputs and optionally appends percent domainIncludes."""
            super().write_outputs(output_path)
            if not self._config.get('generate_statvar_mcf', True):
                return
            statvar_mcf_file = self._config.get('output_statvar_mcf',
                                                f'{output_path}_stat_vars.mcf')
            append_percent_domain_includes(statvar_mcf_file,
                                           self._config.get_configs())

    # pylint:enable=import-outside-toplevel,import-error,too-few-public-methods,protected-access
    _PROCESSOR_RUNTIME = (NaepEduPerformance, process)
    return _PROCESSOR_RUNTIME


def get_naep_processor_class():
    """Returns the lazily loaded NaepEduPerformance processor subclass."""
    naep_cls, _ = _load_processor_runtime()
    return naep_cls


def main(_):
    naep_cls, process_fn = _load_processor_runtime()
    default_input_files = [os.path.join(MODULE_DIR, 'input_files', '*.csv')]
    default_output_path = os.path.join(MODULE_DIR, 'output', 'naep_performance')
    default_conf_path = os.path.join(MODULE_DIR, 'config')
    default_pv_map = [
        os.path.join(default_conf_path, 'pv_map.py'),
        f"jurisdiction:{os.path.join(default_conf_path, 'jurisdiction_map.py')}",
    ]
    default_config_file = os.path.join(default_conf_path, 'naep_conf.py')

    input_data = _FLAGS.input_data or default_input_files
    output_path = _FLAGS.output_path or default_output_path
    config_file = _FLAGS.config_file or default_config_file
    pv_map = _FLAGS.pv_map or default_pv_map

    success = process_fn(
        data_processor_class=naep_cls,
        input_data=input_data,
        output_path=output_path,
        config=config_file,
        pv_map_files=pv_map,
        parallelism=_FLAGS.parallelism,
    )
    if not success:
        raise RuntimeError(
            f'NAEP StatVar processing failed with error counters: {output_path}'
        )


if __name__ == '__main__':
    _load_processor_runtime()
    app.run(main)
