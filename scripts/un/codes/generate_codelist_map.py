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
"""Script to generate codelist mappings for UN codelists.

Converts input CSV codelist files into property-value maps (pvmaps) used by the
StatVar processor.

Usage:
  python3 generate_codelist_map.py \
    --input_codelist=path/to/codelist.csv \
    --output_pvmap=path/to/codelist_pvmap.csv \
    --namespace=un \
    --skip_concepts=UNIT_MULT,FREQUENCY,GEOGRAPHY
"""

import os
import re
import sys
import unicodedata
from typing import Union

from absl import app
from absl import flags
from absl import logging
from anyascii import anyascii
import pprint

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_DATA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import file_util
import mcf_file_util
import eval_functions

from counters import Counters

_DEFAULT_PVMAP_TEMPLATE = os.path.join(_SCRIPT_DIR,
                                       'codelist_pvmap_template.py')

flags.DEFINE_string('input_codelist', '', 'CSV file with codelist.')
flags.DEFINE_string('output_pvmap', '', 'Output pvmap csv.')
flags.DEFINE_string('namespace', 'un', 'Namespace prefix for agency')
flags.DEFINE_string('pvmap_template', _DEFAULT_PVMAP_TEMPLATE,
                    'Python file with pvmap template.')
flags.DEFINE_list(
    'skip_concepts',
    ['UNIT_MULT', 'FREQUENCY', 'GEOGRAPHY'],
    'List of concepts to skip generating pvmaps for.',
)
flags.DEFINE_integer('logging_level', logging.INFO, 'Logging level.')

_FLAGS = flags.FLAGS

# Columns in a source codelist
_DEFAULT_CODE_PROPS = [
    'CONCEPT',
    'CODE',
    'NAME_EN',
    'PARENT',
    'SORT_ORDER',
    'NAME_FR',
    'NAME_ES',
    'DESCRIPTION',
]

# Mapping from concept to properties.
# If not set it map, the concept is used as the property.
_DEFAULT_CONCEPT_PROP_MAP = {
    'SERIES': 'populationType',
    'UNIT_MEASURE': 'unit',
}


def quote(value: Union[str, None]) -> str:
    """Returns a string enclosed in double quotes after trimming spaces.

    Args:
        value: Input string to be quoted.

    Returns:
        The string wrapped in double quotes.

    Example:
        >>> quote('  Total Population  ')
        '"Total Population"'
        >>> quote('"Already Quoted"')
        '"Already Quoted"'
    """
    if value is None:
        return '""'
    value = str(value).strip().strip('"').strip()
    return f'"{value}"'


def to_property(concept: str) -> str:
    """Converts a concept string into a lowerCamelCase property name.

    Args:
        concept: The uppercase or underscore-separated concept string.

    Returns:
        A lowerCamelCase property string suitable for StatVar definition.

    Example:
        >>> to_property('UNIT_MEASURE')
        'unitMeasure'
        >>> to_property('SERIES')
        'series'
    """
    c = eval_functions.str_to_camel_case(concept.lower().replace('_', ' '))
    return c[0].lower() + c[1:]


def to_dcid(code: str) -> str:
    """Sanitizes a code string to create a valid DCID.

    Replaces non-alphanumeric characters with underscores.

    Args:
        code: The raw code or identifier string.

    Returns:
        A valid DCID string with the first character capitalized.

    Example:
        >>> to_dcid('un_series-total_pop')
        'Un_series_total_pop'
        >>> to_dcid('ABC.123:foo-bar')
        'ABC_123_foo_bar'
    """
    value = re.sub(r'[^A-Za-z0-9\._:-]+', '_', code)
    return value[0].upper() + value[1:]


def clean_value_str(val: Union[str, None],
                    regex: str = 'r[^A-Za-z0-9()[]".-]+',
                    replace: str = '_') -> str:
    """Cleans up a value string by removing redundant chars and outer quotes.

    Args:
        val: The raw value string to clean.
        regex: Regular expression pattern identifying characters to replace.
        replace: Replacement string for characters matching `regex`.

    Returns:
        The cleaned value string.

    Example:
        >>> clean_value_str('"  Some Value  "')
        '"Some Value"'
    """
    if not val:
        return ''
    val = str(val).strip()
    if val[0] == '"' and val[-1] == '"':
        val = '"' + val[1:-1].strip() + '"'
    val = re.sub(regex, replace, val)
    return val


_EVAL_FUNCTIONS = dict(eval_functions.EVAL_GLOBALS)
_EVAL_FUNCTIONS.update({
    'to_property': to_property,
    'to_dcid': to_dcid,
    'clean_value_str': clean_value_str,
    'quote': quote,

    # Additional modules for text manipulations
    'unicodedata': unicodedata,
    'anyascii': anyascii,
})


def get_value(tpl_val: str, input_pvs: dict) -> str:
    """Evaluates a template value using formatting or Python evaluation.

    If `tpl_val` contains `{`, it is formatted using `input_pvs` pairs.
    If `tpl_val` contains `(`, it is evaluated via `_EVAL_FUNCTIONS`.

    Args:
        tpl_val: The template string or function call to evaluate.
        input_pvs: Dictionary with variable values/props for substitution.

    Returns:
        The evaluated string value with pvs applied.

    Example:
        >>> get_value('{CONCEPT}:{CODE}', {'CONCEPT': 'SERIES', 'CODE': 'POP'})
        'SERIES:POP'
        >>> get_value('to_property(CONCEPT)', {'CONCEPT': 'UNIT_MEASURE'})
        'unitMeasure'
    """
    value = tpl_val
    if '{' in tpl_val:
        # Format template string by substituting input_pvs placeholders
        try:
            value = tpl_val.format(**input_pvs)
        except Exception as e:
            logging.error(
                f'Failed formatting "{tpl_val}" with dict {input_pvs}: {e}'
            )
            value = ''
    elif '(' in tpl_val:
        # Evaluate Python function call against _EVAL_FUNCTIONS lookup table
        try:
            prop, value = eval_functions.evaluate_statement(
                tpl_val, input_pvs, _EVAL_FUNCTIONS)
        except Exception as e:
            logging.error(
                f'Failed evaluating "{tpl_val}" with dict {input_pvs}: {e}'
            )
            value = ''
    if value:
        # Clean and normalize quotes/redundant chars in evaluated value
        value = clean_value_str(value)
    return value or ''


def generate_code_map(code_pvs: dict,
                      namespace: str = 'un',
                      template: dict = None) -> dict:
    """Generates a property-value mapping dict for a single codelist row.

    Args:
        code_pvs: Dictionary representing a single row from a codelist CSV,
            with keys like 'CONCEPT', 'CODE', 'NAME_EN', and 'DESCRIPTION'.
        namespace: Namespace prefix (e.g. 'un') for constraint values.
        template: Dictionary template defining mapping rules from source
            props to output props.

    Returns:
        A dictionary containing the generated property-value map for the code.

    Example:
        >>> generate_code_map({
        ...     'CONCEPT': 'SERIES',
        ...     'CODE': 'POP',
        ...     'NAME_EN': 'Population',
        ...     'DESCRIPTION': 'Total pop'
        ... })
        {
            'key': 'SERIES:POP',
            'ConstraintProp': 'populationType',
            'ConstraintPropValue': 'UN_SERIES-POP',
            'ConstraintPropType': 'TypeOf',
            ...
        }
    """
    if template is None:
        template = file_util.file_load_py_dict(_DEFAULT_PVMAP_TEMPLATE)
    if not template:
        logging.error('No valid template available for generate_code_map')
        return {}
    output_pvs = dict()
    input_pvs = dict(code_pvs)

    # Normalize namespace case across both lower and uppercase keys
    input_pvs.setdefault('namespace', namespace.lower())
    input_pvs.setdefault('NAMESPACE', namespace.upper())

    # Determine target property for concept (e.g. populationType for SERIES)
    concept = code_pvs.get('CONCEPT')
    concept_prop = _DEFAULT_CONCEPT_PROP_MAP.get(concept)
    if not concept_prop:
        concept_prop = to_property(concept)
    input_pvs['PROPERTY'] = concept_prop

    # Iterate over mapping rules to evaluate key-value pairs for pvmap row
    for tpl_prop, tpl_val in template.items():
        tpl_prop = get_value(tpl_prop, input_pvs)
        value = get_value(tpl_val, input_pvs)
        output_pvs[tpl_prop] = value
        input_pvs[tpl_prop] = value
        logging.log(2, f'Mapped {tpl_prop} using {tpl_val} to {value}')
    return output_pvs


def normalize_skip_concepts(
    skip_concepts: Union[list[str], set[str], tuple[str, ...], str, None]
) -> set[str]:
    """Normalizes skip concepts into an uppercase set of strings.

    Args:
        skip_concepts: Collection, comma/space string, or set of concept names.

    Returns:
        A set of uppercase concept strings to skip.

    Example:
        >>> normalize_skip_concepts(['unit_mult', 'frequency'])
        {'UNIT_MULT', 'FREQUENCY'}
    """
    if not skip_concepts:
        return set()
    if isinstance(skip_concepts, set):
        return {str(c).strip().upper() for c in skip_concepts if c}
    if isinstance(skip_concepts, str):
        parts = re.split(r'[,;\s]+', skip_concepts)
        return {p.strip().upper() for p in parts if p.strip()}
    return {
        str(c).strip().upper() for c in skip_concepts if c and str(c).strip()
    }


def resolve_output_file(cl_file: str,
                        output_path: str,
                        is_multi_file: bool = False) -> str:
    """Resolves target output file path for a codelist file.

    Args:
        cl_file: Path to the source codelist CSV file.
        output_path: Requested target file or directory path.
        is_multi_file: Whether multiple codelist files are being processed.

    Returns:
        The resolved output CSV file path.

    Example:
        >>> resolve_output_file('codes/cl1.csv', 'out/', is_multi_file=True)
        'out/cl1_pvmap.csv'
    """
    if (not output_path or is_multi_file or os.path.isdir(output_path) or
            output_path.endswith('/')):
        output_name = file_util.file_get_name(cl_file,
                                              suffix='_pvmap',
                                              file_ext='.csv')
        if output_path and (is_multi_file or os.path.isdir(output_path) or
                            output_path.endswith('/')):
            dir_path = output_path + (
                '/' if not output_path.endswith('/') else ''
            )
            file_util.file_makedirs(dir_path)
            return os.path.join(output_path, os.path.basename(output_name))
        return output_name
    return output_path


def generate_codelist_pvmap(cl_file: str,
                            output: str,
                            namespace: str = 'un',
                            pvmap_template: dict = None,
                            skip_concepts_set: set[str] = None,
                            counters: Counters = None) -> dict:
    """Generates a property-value map (pvmap) CSV from a single codelist CSV.

    Args:
        cl_file: Absolute or relative path to the input CSV codelist file.
        output: Path where the generated pvmap CSV file will be written.
        namespace: Namespace prefix for the agency (defaults to 'un').
        pvmap_template: Template mappings dict. Defaults to loading
            `_DEFAULT_PVMAP_TEMPLATE`.
        skip_concepts_set: Set of uppercase concepts to skip (e.g.
            {'UNIT_MULT'}).
        counters: Optional `Counters` instance for aggregating metrics.

    Returns:
        A dictionary mapping row indices to generated pvmap row dicts.

    Example:
        >>> generate_codelist_pvmap(
        ...     cl_file='data/codes/SDG_SERIES.csv',
        ...     output='output/SDG_SERIES_pvmap.csv',
        ...     namespace='un',
        ...     skip_concepts_set={'UNIT_MULT'}
        ... )
        {0: {'key': 'SERIES:TOTAL_POP', 'ConstraintProp': ...}}
    """
    # Initialize standalone counters if not called from a multi-file wrapper
    print_counters = False
    if counters is None:
        counters = Counters()
        print_counters = True

    # Load source rows from the codelist CSV file
    input_codes = file_util.file_load_csv_dict(cl_file, key_index=True)
    if input_codes is None:
        logging.error(f'Failed to load codelist CSV dictionary: {cl_file}')
        return {}
    logging.info(f'Loaded {len(input_codes)} from codelist: {cl_file}')
    counters.add_counter('input-codes', len(input_codes))

    # Resolve default template dictionary and skip concept set if not supplied
    if pvmap_template is None:
        pvmap_template = file_util.file_load_py_dict(_DEFAULT_PVMAP_TEMPLATE)
    if not pvmap_template:
        logging.error(f'Failed to load valid pvmap template for: {cl_file}')
        return {}

    skip_concepts_set = normalize_skip_concepts(skip_concepts_set)

    # Process each code row in the input codelist
    output_pvs = {}
    for index, code_pvs in input_codes.items():
        concept = code_pvs.get('CONCEPT', '').strip()
        # Skip generating pvmap for excluded concepts (e.g. UNIT_MULT)
        if concept and concept.upper() in skip_concepts_set:
            counters.add_counter(f'skipped-concept-{concept}', 1)
            counters.add_counter('skipped-codes', 1)
            logging.debug(f'Skipping concept {concept} for code {code_pvs}')
            continue
        pvs = generate_code_map(code_pvs, namespace, pvmap_template)
        output_pvs[index] = pvs
        logging.debug(f'Mapped {code_pvs} to {pvs}')

    # Write generated pvs to the output CSV file
    if output and output_pvs:
        file_util.file_write_csv_dict(output_pvs, output)

    # Compute unique value counts across all output columns for metrics
    unique_counts = dict()
    for index, pvs in output_pvs.items():
        for prop, val in pvs.items():
            if val:
                unique_counts.setdefault(prop, set()).add(val)
    for prop, vals in unique_counts.items():
        counters.add_counter(f'output-unique-{prop}', len(vals))

    counters.add_counter('output-rows', len(output_pvs))
    if print_counters:
        counters.print_counters()
    return output_pvs


def generate_codelist_pvmaps(
    input_files: Union[list[str], str],
    output_path: str = '',
    namespace: str = 'un',
    template_file: str = _DEFAULT_PVMAP_TEMPLATE,
    skip_concepts: Union[list[str], set[str],
                         tuple[str,
                               ...]] = ('UNIT_MULT', 'FREQUENCY', 'GEOGRAPHY')
) -> dict:
    """Generates pvmap files across multiple codelist input files.

    Args:
        input_files: A single path, comma-separated paths, glob pattern, or
            list of input CSV file paths.
        output_path: Output file or directory. If multiple files matched,
            `output_path` is treated as a directory for per-file outputs.
        namespace: Namespace prefix for the agency (defaults to 'un').
        template_file: Path to a Python template file with mapping rules.
        skip_concepts: List, set, or tuple of concept names to skip when
            generating pvmaps.

    Returns:
        A dictionary mapping each input file path to its generated pvmap dict.

    Example:
        >>> generate_codelist_pvmaps(
        ...     input_files=['codes/cl1.csv', 'codes/cl2.csv'],
        ...     output_path='output/',
        ...     namespace='un'
        ... )
        {
            'codes/cl1.csv': {0: {'key': ...}},
            'codes/cl2.csv': {0: {'key': ...}}
        }
    """
    counters = Counters()

    # Match input codelist files via glob, comma-separated string, or list
    files = file_util.file_get_matching(input_files)
    if not files:
        logging.warning(f'No codelist files found matching: {input_files}')
        return {}
    logging.info(f'Processing {len(files)} codelist files: {files}')
    counters.add_counter('input-files', len(files))

    # Load mapping template dictionary once across all input files
    pvmap_template = file_util.file_load_py_dict(
        template_file or _DEFAULT_PVMAP_TEMPLATE
    )
    if not pvmap_template:
        logging.error(
            f'Failed to load valid pvmap template from: {template_file}'
        )
        return {}
    logging.info(f'Using template:\n{pprint.pformat(pvmap_template)}')

    # Normalize skip_concepts parameter into uppercase set for O(1) lookups
    if skip_concepts is None:
        skip_concepts = ['UNIT_MULT', 'FREQUENCY', 'GEOGRAPHY']
    skip_concepts_set = normalize_skip_concepts(skip_concepts)
    if skip_concepts_set:
        logging.info(f'Skipping concepts across files: {skip_concepts_set}')

    # Process each matched codelist file and generate corresponding output
    all_output_pvs = {}
    is_multi_file = len(files) > 1
    for cl_file in files:
        output_file = resolve_output_file(cl_file, output_path, is_multi_file)
        logging.info(f'Generating pvmap for {cl_file} -> {output_file}')
        pvs = generate_codelist_pvmap(
            cl_file=cl_file,
            output=output_file,
            namespace=namespace,
            pvmap_template=pvmap_template,
            skip_concepts_set=skip_concepts_set,
            counters=counters,
        )
        all_output_pvs[cl_file] = pvs
        counters.add_counter('processed-files', 1)
        if pvs is not None:
            counters.add_counter('output-codes', len(pvs))

    counters.print_counters()
    return all_output_pvs


def main(_):
    """Parses flags and executes multi-file codelist pvmap generation."""
    logging.set_verbosity(_FLAGS.logging_level)
    generate_codelist_pvmaps(_FLAGS.input_codelist, _FLAGS.output_pvmap,
                             _FLAGS.namespace, _FLAGS.pvmap_template,
                             _FLAGS.skip_concepts)


if __name__ == '__main__':
    app.run(main)
