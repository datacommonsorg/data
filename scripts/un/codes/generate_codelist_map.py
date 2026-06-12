"""Script to geenrate codelist mapings for a specific codelist file."""

import os
import re
import sys

from absl import app
from absl import flags
from absl import logging

import file_util
import mcf_file_util
import eval_functions

from counters import Counters

flags.DEFINE_string('input_codelist', '', 'CSV file with codelist.')
flags.DEFINE_string('output_pvmap', '', 'Output pvmap csv.')
flags.DEFINE_string('namespace', 'un', 'Namespace prefix for agency')
flags.DEFINE_integer('logging_level', logging.INFO, 'Logging level.')
flags.DEFINE_string('pvmap_template', '', 'Python file with pvmap template.')

_FLAGS = flags.FLAGS

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

# Map from a code to a pvmap
_DEFAULT_CODE_PVMAP = {
    'key': '{CONCEPT}:{CODE}',
    'UnConceptProp': 'Property',
    'UnConcept': '"{CONCEPT}"',
    'UnCodeProp': 'UnCode',
    'UnCode': '"{CODE}"',
    'ConstraintProp': 'to_property(CONCEPT)',
    'ConstraintPropValue': 'to_dcid(NAMESPACE+"_"+CODE)',
    'ConstraintPropType': 'TypeOf',
    'ConstraintPropEnum': 'str(ConstraintProp[0].upper() + ConstraintProp[1:]+"Enum")',
    'NameProp': '{CONCEPT}_name',
    'ConstraintValueName': '"{NAME_EN}"',
    'DescriptionProp': '{CONCEPT}_description',
    'ConstraintValueDescription': '{DESCRIPTION}',
    'End': 'End',
    'Dummy': '.',
}


def to_property(concept: str) -> str:
    """Returns a property for the concept."""
    c = eval_functions.str_to_camel_case(concept.lower().replace('_', ' '))
    return c[0].lower() + c[1:]


def to_dcid(code: str) -> str:
    """Replace any non alphanumeric characters with '_'"""
    value = re.sub(r'[^A-Za-z0-9\.]+', '_', code)
    return value[0].upper() + value[1:]


def clean_value_str(val: str,
                    regex: str = 'r[^A-Za-z0-9()[]".-]+',
                    replace: str = '_') -> str:
    """Cleanup value string to remove redundant characters."""
    val = val.strip()
    if val[0] == '"' and val[-1] == '"':
        val = '"' + val[1:-1].strip() + '"'
    val = re.sub(regex, replace, val)
    return val


_EVAL_FUNCTIONS = dict(eval_functions.EVAL_GLOBALS)
_EVAL_FUNCTIONS.update({
    'to_property': to_property,
    'to_dcid': to_dcid,
    'clean_value_str': clean_value_str,
})

def get_value(tpl_val: str, input_pvs: dict) -> str:
  """Retuns a value with the pvs applied."""
  value = tpl_val
  if '{' in tpl_val:
      # Format string
      try:
          value = tpl_val.format(**input_pvs)
      except Exception as e:
          logging.error(
              f'Failed to format "{tpl_val}" using dict: {input_pvs}, error:{e}'
          )
          value = ''
  elif '(' in tpl_val:
      # Evaluate a function
      try:
          prop, value = eval_functions.evaluate_statement(
              tpl_val, input_pvs, _EVAL_FUNCTIONS)
      except Exception as e:
          lgging.error(
              f'Failed to evaluate "{tpl_val}" using dict: {pvs}, error:{e}'
          )
          value = ''
  if value:
      # Cleanup value
      value = clean_value_str(value)
  return value


def generate_code_map(code_pvs: dict,
                      namespace: str = 'un',
                      template: dict = _DEFAULT_CODE_PVMAP) -> dict:
    """Returns a pvmap pvs for a single code.
   A code has keys listed in _DEFAULT_CODE_PROPS
   It returns a dictionary with the keys in template.
   """
    output_pvs = dict()
    input_pvs = dict(code_pvs)
    input_pvs.setdefault('namespace', namespace.lower())
    input_pvs.setdefault('NAMESPACE', namespace.upper())
    for tpl_prop, tpl_val in template.items():
        tpl_prop = get_value(tpl_prop, input_pvs)
        value = get_value(tpl_val, input_pvs)
        output_pvs[tpl_prop] = value
        input_pvs[tpl_prop] = value
        logging.log(2, f'Mapped {tpl_prop} using {tpl_val} to {value}')
    return output_pvs


def generate_codelist_pvmap(cl_file: str,
                            output: str,
                            namespace: str = 'un') -> dict:
    """Generate a pvmap file for a codelist."""
    counters = Counters()

    input_codes = file_util.file_load_csv_dict(cl_file, key_index=True)
    logging.info(f'Loaded {len(input_codes)} from codelist: {cl_file}')
    counters.add_counter('input-codes', len(input_codes))

    output_pvs = {}
    for index, code_pvs in input_codes.items():
        pvs = generate_code_map(code_pvs, namespace)
        output_pvs[index] = pvs
        logging.debug(f'Mapped {code_pvs} to {pvs}')

    # Write to output file
    if output:
        file_util.file_write_csv_dict(output_pvs, output)

    # Get unique counts across output columns
    unique_counts = dict()
    for index, pvs in output_pvs.items():
        for prop, val in pvs.items():
            if val:
                unique_counts.setdefault(prop, set()).add(val)
    for prop, vals in unique_counts.items():
        counters.add_counter(f'output-unique-{prop}', len(vals))

    counters.add_counter('output-rows', len(output_pvs))
    counters.print_counters()


def main(_):
    logging.set_verbosity(_FLAGS.logging_level)
    generate_codelist_pvmap(_FLAGS.input_codelist, _FLAGS.output_pvmap,
                            _FLAGS.namespace)


if __name__ == '__main__':
    app.run(main)
