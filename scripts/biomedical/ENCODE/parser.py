# Copyright 2021 Google LLC
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

"""Parses files scraped from the Encode project into either an intermediate.

json or MCF format.

This script requires an external plugin:
- rdflib-jsonld (https://github.com/RDFLib/rdflib-jsonld)


NOTE: This script DOES NOT RUN due to PY3 issue. See details in b/179108285.

"""

import collections
import json
import multiprocessing
import os
import re

from absl import app
from absl import flags
from absl import logging

from rdflib import Graph
from rdflib.plugin import Parser
from rdflib.plugin import register

from google3.pyglib import gfile
from google3.pyglib import resources

# Constants
RDF_URL = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

# Vocab namespaces
RDF_NAMESPACE = 'rdf:'

# Entity type prefixes
FILE_PREFIX = 'file://'

# Properties to ignore while scraping
IGNORED_PROPERTIES = {
    '/terms/notes', '/terms/possible_controls', '/terms/internal_tags',
    '/terms/hub', '/terms/documents', '/terms/original_files',
    '/terms/internal_status', '/terms/month_released',
    '/terms/contributing_files', '/terms/replication_type', '/terms/replicates',
    '/terms/aliases', '/terms/schema_version', '/terms/end_date',
    '/terms/viewing_group', '/terms/start_date', '/terms/project',
    '/terms/accession', '/terms/analysis_step_version', '/terms/s3_uri',
    '/terms/file_format_specifications', '/terms/file_size',
    '/terms/no_file_available', '/terms/href', '/terms/step_run',
    '/terms/technical_replicates', '/terms/replicate_libraries',
    '/terms/cloud_metadata', '/terms/submitted_file_name',
    '/terms/derived_from', '/terms/files', '/terms/md5sum', '/terms/rfa',
    '/terms/replicate', '/terms/file_format_type', '/terms/file_format',
    '/terms/content_md5sum', '/terms/revoked_files', '/terms/superseded_by',
    '/terms/supersedes'
}

# Encode prefixes
ENCODE_URL = 'https://www.encodeproject.org'
ENCODE_ROOT_PATTERN = 'https://www.encodeproject.org{}'
ENCODE_GRAPH_KEY = '@graph'
ENCODE_CONTEXT_KEY = '@context'
ENCODE_ID_KEY = '@id'
ENCODE_FILE_TYPE_PROP = '/terms/file_type'
ENCODE_TERM_PREFIX = '/terms/'
ENCODE_AWARDS_PREFIX = '/awards/'
ENCODE_BIOSAMPLE_PREFIX = '/biosamples/'
ENCODE_BIOSAMPLE_TYPE_PREFIX = '/biosample-types/'
ENCODE_LAB_PREFIX = '/labs/'
ENCODE_LIBRARY_PREFIX = '/libraries/'
ENCODE_USER_PREFIX = '/users/'
ENCODE_EXPERIMENT_PREFIX = '/experiments/'
ENCODE_FILE_PREFIX = '/files/'
ENCODE_REF_PREFIXES = [
    ENCODE_AWARDS_PREFIX,
    ENCODE_LAB_PREFIX,
    ENCODE_LIBRARY_PREFIX,
    ENCODE_USER_PREFIX,
    ENCODE_BIOSAMPLE_TYPE_PREFIX,
    ENCODE_BIOSAMPLE_PREFIX,
    ENCODE_EXPERIMENT_PREFIX,
]
ENCODE_TO_SCHEMA_TYPES = {
    '/terms/Award': 'schema:EncodeAward',
    '/terms/Lab': 'schema:Lab',
    '/terms/User': 'schema:Person',
    '/terms/Experiment': 'schema:EncodeExperiment',
    '/terms/BiosampleType': 'schema:EncodeBiosampleType',
    '/terms/Biosample': 'schema:EncodeBiosample',
    '/terms/Library': 'schema:EncodeLibrary',
    '/terms/File': 'schema:EncodeBedFile'
}
# ENCODE_TERMS_URL = 'https://www.encodeproject.org/terms/?format=json'
ENCODE_TERMS_URL = 'parser_data/terms.json'
ENCODE_REF_REGEX = r'\/[A-Za-z0-9-_]+\/[A-Za-z0-9-_]+\/'

# Datacommons type constants
DC_BED_LINE_TYPE = 'schema:BedLine'

# RDF constants
RDF_TYPE_PROP = 'rdf:type'

# Other constants
MAX_BUFFER_LENGTH = 200000
NEW_SCHEMA_ROOT = '/cns/jv-d/home/datcom/encode_project/schema/'
NEW_SCHEMA_FILE_PATTERN = '/cns/jv-d/home/datcom/encode_project/schema/schema_{}.txt'

# File name containing a list of all experiments scraped
# NOTE: this should be contained in the data root
SEARCH_RESULTS_FILE = 'search_results.json'

# --------------------------------- SELECTORS ---------------------------------


def default_select(s, p, o):
  """The default selector to use when filtering triples."""
  return select_allowed_props(s, p, o) and select_type_triple(s, p, o)


def select_type_triple(s, p, o):
  """ Only select triples that denote the entity as a certain type.

  For example, ignore all triples that assign the type /terms/Item to the
  entity.
  """
  if p == RDF_TYPE_PROP:
    return o in ENCODE_TO_SCHEMA_TYPES
  return True


def select_allowed_props(s, p, o):
  """Only select triples not in the IGNORED_PROPERTIES list."""
  return p not in IGNORED_PROPERTIES


def clean_encode_val(value):
  """Performs text cleanup for the given value."""
  value = value.replace('"', '\'')
  value = value.replace('\n', ' ')
  value = value.replace('\r', ' ')
  value = value.replace('\t', ' ')
  return value


# ---------------------------------- HELPERS ----------------------------------


def read_with_context(file_path):
  """Returns the file contents stored at file_path with the fixed context."""
  with gfile.Open(file_path, 'r') as f:
    encode_json = json.load(f)
  if ENCODE_CONTEXT_KEY in encode_json:
    encode_json[ENCODE_CONTEXT_KEY] = os.path.join(
        resources.GetRunfilesDir(), 'google3/datacommons/mcf/encode',
        ENCODE_TERMS_URL)
  return json.dumps(encode_json)


def mkdirs_if_dne(path):
  """Creates the directory at path if it does not exist."""
  if not gfile.IsDirectory(path):
    gfile.MakeDirs(path)


def normalize(word):
  """Normalizes the words used in triples."""
  if FILE_PREFIX in word:
    word = word.replace(FILE_PREFIX, '')
  elif RDF_URL in word:
    word = word.replace(RDF_URL, RDF_NAMESPACE)
  elif ENCODE_URL in word:
    word = word.replace(ENCODE_URL, '')
  return word


def add_triple(data, sub, pred, obj, select):
  """Adds the triple (subject, object, predicte) to the data map."""
  s = normalize(sub)
  p = normalize(pred)
  o = normalize(obj)

  if filter is not None and select(s, p, o):
    if s not in data:
      data[s] = collections.OrderedDict()
    if p not in data[s]:
      data[s][p] = []
    data[s][p].append(o)


def encode_to_schema_triples(encode_triples):
  """Returns the encode_triples translated to use DataCommons schema.

  Additionally returns new translated predicates.
  """
  schema_triples = collections.OrderedDict()
  schema_preds = set()

  # Iterate through all triples and covert them to DC compatible schema.
  for sub in encode_triples:
    schema_sub = encode_to_schema_ref(sub)
    schema_entry = collections.OrderedDict()

    # Copy over all properties and objects
    for prop in encode_triples[sub]:
      schema_prop = encode_to_schema_prop(prop)
      schema_vals = []
      for val in encode_triples[sub][prop]:
        schema_val = encode_to_schema_val(val)
        if schema_val != u'""':
          schema_vals.append(schema_val)

      # Add the property if there is at least one value returned
      if schema_vals:
        schema_entry[schema_prop] = schema_vals
        schema_preds.add(schema_prop)

    # Add the schema entry if at least one property has values. Append a
    # statement linking the schema entity to the Encode Project entity.
    if schema_entry:
      schema_entry['sameAs'] = [u'"{}"'.format(ENCODE_ROOT_PATTERN.format(sub))]
      schema_triples[schema_sub] = schema_entry

  return schema_preds, schema_triples


def encode_to_schema_ref(encode_ref):
  """Converts an ENCODE reference to a schema compatible reference."""
  return encode_ref.replace('/', '_')[1:len(encode_ref) - 1]


def encode_to_schema_prop(encode_prop):
  """Converts an ENCODE property to a schema property."""
  if encode_prop == '/terms/uuid':
    return u'encodeUUID'
  if encode_prop == '/terms/title':
    return u'name'
  if encode_prop == '/terms/dataset':
    return u'fromExperiment'
  if encode_prop == RDF_TYPE_PROP:
    return u'typeOf'
  prop_split = encode_prop.split(ENCODE_TERM_PREFIX)[-1]
  prop_chunks = prop_split.split('_')
  if len(prop_chunks) > 1:
    for idx, chunk in enumerate(prop_chunks[1:]):
      prop_chunks[1 + idx] = chunk.capitalize()
  return u''.join(prop_chunks)


def encode_to_schema_val(encode_val):
  """Converts an ENCODE value to a schema compatible value."""
  if is_encode_type(encode_val):
    return encode_to_schema_type(encode_val)
  elif is_resolved_encode_reference(encode_val):
    return u'l:{}'.format(encode_to_schema_ref(encode_val))
  elif is_unresolved_encode_reference(encode_val):
    return u'"{}"'.format(ENCODE_ROOT_PATTERN.format(encode_val))
  elif isinstance(encode_val, int):
    return encode_val
  return u'"{}"'.format(clean_encode_val(encode_val))


def encode_to_schema_type(encode_type):
  """Converts an ENCODE type to a DataCommons schema type."""
  return ENCODE_TO_SCHEMA_TYPES[encode_type]


def is_encode_type(word):
  """Returns if the word is an ENCODE type."""
  return word.startswith(ENCODE_TERM_PREFIX)


def is_resolved_encode_reference(word):
  """Returns if the word is a resolved Encode reference.

  That is it refers
  to an entity that will be reflected in DataCommons.
  """
  return (isinstance(word, str)) and any(
      word.startswith(pre) for pre in ENCODE_REF_PREFIXES)


def is_unresolved_encode_reference(word):
  """Returns if the word is an unresolved Encode reference i.e.

  an entity
    that will not be created in DataCommons.
  """
  return re.match(ENCODE_REF_REGEX, word) is not None


def write_mcf(schema_triples, dest_path, mode='w'):
  """Creates an MCF file containing all triples in the given dictionary.

  DataCommons schema compatible triples and saves it at the dest_path.
  """
  # If mode set to append, check if file exists
  if mode == 'a' and not gfile.Exists(dest_path):
    mode = 'w'

  # Iterate through all schematized triples and write the MCF file
  mcf_file = gfile.Open(dest_path, mode)
  for sub in schema_triples:
    mcf_file.write(u'Node: {}\n'.format(sub))
    for prop in schema_triples[sub]:
      vals = u', '.join([val for val in schema_triples[sub][prop]]).strip()
      mcf_file.write(u'{}: {}\n'.format(prop, vals))
    mcf_file.write(u'\n')

  # Close the file
  mcf_file.close()


def write_schema(new_schema, new_schema_path):
  """Updates the new schema file with the new_schema to be added."""
  existing_new_schema = set()
  if gfile.Exists(new_schema_path):
    with gfile.Open(new_schema_path, 'r') as f:
      existing_new_schema = {line.strip() for line in f}

  for schema in new_schema:
    existing_new_schema.add(schema)
  existing_new_schema = sorted(existing_new_schema)

  # Write the new schema
  with gfile.Open(new_schema_path, 'w') as f:
    for schema in existing_new_schema:
      f.write(schema + '\n')


# -------------------------- VERIFICATION FUNCTIONS ---------------------------


def get_external_references(data_root):
  """Returns a set of all Encode references."""
  references = set()

  # Go through each auxiliary file and add all references.
  for aux_category in AUXILIARY_CATEGORY_MAP:
    aux_file = '{}.json'.format(aux_category)
    file_path = os.path.join(data_root, aux_file)
    with gfile.Open(file_path, 'r') as f:
      aux_json = json.load(f)

    # Iterate through all entities in the JSON and add their IDs to the set
    potential_jsons = {}
    for entity in aux_json[ENCODE_GRAPH_KEY]:
      entity_id = entity[ENCODE_ID_KEY]
      json_file = '{}.json'.format(entity_id.split('/')[-2])
      potential_jsons[entity_id] = json_file
    aux_dir = os.path.join(data_root, aux_category)
    actual_jsons = gfile.ListDirectory(aux_dir)

    # Iterate through all potential jsons and check if the exist in the folder
    for entity_id, json_file in potential_jsons.items():
      if json_file in actual_jsons:
        references.add(entity_id)

  # Add experiment keys that were scraped
  search_results_path = os.path.join(data_root, SEARCH_RESULTS_FILE)
  with gfile.Open(search_results_path, 'r') as f:
    experiments_json = json.load(f)
  potential_exp = {}
  for entity in experiments_json[ENCODE_GRAPH_KEY]:
    entity_id = entity[ENCODE_ID_KEY]
    exp_dir = entity_id.split('/')[-2]
    potential_exp[entity_id] = exp_dir
  actual_exp = gfile.ListDirectory(data_root)

  # Iterate through all potential experiments and add the ones that exist
  for entity_id, exp_dir in potential_exp.items():
    if exp_dir in actual_exp:
      references.add(entity_id)

  return references


def verify_references(encode_triples, references):
  """ Verifies that all triple objects in the given dictionary of reference

    entities in the given set of references.
  """
  # Iterate through all triples and verify their references.
  verified_triples = collections.OrderedDict()
  for sub in encode_triples:
    entry = collections.OrderedDict()

    # Copy over all properties and objects if it contains valid references
    for prop in encode_triples[sub]:
      vals = []
      for val in encode_triples[sub][prop]:
        if is_resolved_encode_reference(val) and val not in references:
          logging.warning(
              '> WARNING: (%s, %s, %s) contains unknown reference to "%s", sub, prop, val, val'
          )
        else:
          vals.append(val)

      # Add the property if there is at least one value returned
      if vals:
        entry[prop] = vals

    # Add the schema entry if at least one property has values
    if entry:
      verified_triples[sub] = entry

  return verified_triples


# --------------------------- PARSE AUXILIARY FILES ---------------------------


def parse_auxiliary_directories(data_root,
                                dest_root,
                                num_processes,
                                select=None):
  """Parses all auxiliary files stored in the given data_root.

  Saves contents as MCF files in the given dest_root.
  """
  logging.info('> Parsing auxiliary files @ %s', data_root)

  ext_refs = get_external_references(data_root)
  proc_args = []

  # Iterate through all auxiliary categories and convert each into MCF files.
  for aux_category in AUXILIARY_CATEGORY_MAP:
    logging.info('> Now generating %s files', aux_category)

    aux_dest_root = os.path.join(dest_root, aux_category)
    mkdirs_if_dne(aux_dest_root)

    aux_dir = os.path.join(data_root, aux_category)
    allowed_files = [
        name for name in gfile.ListDirectory(aux_dir) if '.json' in name
    ]

    for aux_json in allowed_files:
      # Create the MCF filename
      aux_name = aux_json.split('.json')[0]
      aux_mcf = '{}.mcf'.format(aux_name)

      # Build the source and destination file path, create the directory
      # if it does not exist.
      aux_path = os.path.join(aux_dir, aux_json)
      dest_path = os.path.join(aux_dest_root, aux_mcf)

      # Parse the contents
      # If more than one process is specified, then add the arguments to the
      # otherwise parse the contents.
      if num_processes > 1:
        proc_args.append((AUXILIARY_CATEGORY_MAP[aux_category], aux_path,
                          dest_path, ext_refs, select))
      else:
        AUXILIARY_CATEGORY_MAP[aux_category](aux_path, dest_path, ext_refs,
                                             select)
        logging.info('> Finished parsing %s', aux_category)

  # Helper for parsing aux files in parallel.
  def _parallel(arg_tuple):
    arg_tuple[0](arg_tuple[1], arg_tuple[2], arg_tuple[3], arg_tuple[4])

  # Execute the parallel parse jobs from a pool if more than one proc given
  if num_processes > 1:
    logging.info('> Parsing all jobs in parallel')
    pool = multiprocessing.Pool(num_processes)
    pool.map(_parallel, proc_args)

  logging.info('> Finished parsing all auxiliary files!')


def parse_award(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE Project award into an MCF file."""
  logging.info('> Parsing award file @ %s', src_path)

  contents = read_with_context(src_path)
  award_graph = Graph().parse(data=contents, format='json-ld')
  award_triples = collections.OrderedDict()

  # Add triples from the award JSON
  for s, p, o in award_graph:
    if ENCODE_AWARDS_PREFIX in s:
      add_triple(award_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(award_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! award file @ %s stored to %s', src_path, dest_path)


def parse_biosample(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE project biosample into an MCF file."""
  logging.info('> Parsing biosample file @ %s', src_path)
  contents = read_with_context(src_path)
  biosample_graph = Graph().parse(data=contents, format='json-ld')
  biosample_triples = collections.OrderedDict()

  # Add triples from the biosample JSON
  for s, p, o in biosample_graph:
    if ENCODE_BIOSAMPLE_PREFIX in s:
      add_triple(biosample_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(biosample_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! biosample file @ %s stored to %s', src_path,
               dest_path)


def parse_biosample_type(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE project biosample type into an MCF file."""
  logging.info('> Parsing biosample type file @ %s', src_path)

  contents = read_with_context(src_path)
  biosample_type_graph = Graph().parse(data=contents, format='json-ld')
  biosample_type_triples = collections.OrderedDict()

  # Add triples from the biosample_type JSON
  for s, p, o in biosample_type_graph:
    if ENCODE_BIOSAMPLE_TYPE_PREFIX in s:
      add_triple(biosample_type_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(biosample_type_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! biosample type file @ %s stored to %s', src_path,
               dest_path)


def parse_lab(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE project lab type into an MCF file."""
  logging.info('> Parsing lab file @ %s', src_path)

  contents = read_with_context(src_path)
  lab_graph = Graph().parse(data=contents, format='json-ld')
  lab_triples = collections.OrderedDict()

  # Add triples from the lab JSON
  for s, p, o in lab_graph:
    if ENCODE_LAB_PREFIX in s:
      add_triple(lab_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(lab_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! lab file @ %s stored to %s', src_path, dest_path)


def parse_library(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE project library type into an MCF file."""
  logging.info('> Parsing library file @ %s', src_path)

  contents = read_with_context(src_path)
  library_graph = Graph().parse(data=contents, format='json-ld')
  library_triples = collections.OrderedDict()

  # Add triples from the library JSON
  for s, p, o in library_graph:
    if ENCODE_LIBRARY_PREFIX in s:
      add_triple(library_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(library_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! library file @ %s stored to %s', src_path,
               dest_path)


def parse_user(src_path, dest_path, ext_refs, select):
  """Parses a given ENCODE project user type into an MCF file."""
  logging.info('> Parsing user file @ %s', src_path)

  contents = read_with_context(src_path)
  user_graph = Graph().parse(data=contents, format='json-ld')
  user_triples = collections.OrderedDict()

  # Add triples from the user JSON
  for s, p, o in user_graph:
    if ENCODE_USER_PREFIX in s:
      add_triple(user_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(user_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  write_mcf(schema_triples, dest_path)

  logging.info('> FINISHED! user file @ %s stored to %s', src_path, dest_path)


# ----------------------------- PARSE EXPERIMENTS -----------------------------


def parse_experiment_directories(data_root,
                                 dest_root,
                                 num_processes,
                                 experiment_dirs=None,
                                 select=None):
  """Parses all experiments in the list of target directory."""
  # Log some information on what's parsed
  logging.info('> Parsing experiment directories...')
  if experiment_dirs is not None:
    for exp_dir in experiment_dirs:
      logging.info('  - %s', exp_dir)
  else:
    logging.info('  - ALL!')

  ext_refs = get_external_references(data_root)

  # Get all experiment directories if experiment dirs not provided
  if not bool(experiment_dirs):
    experiment_dirs = []
    for d in gfile.ListDirectory(data_root):
      dir_path = os.path.join(data_root, d)
      if gfile.IsDirectory(dir_path) and d not in AUXILIARY_CATEGORY_MAP:
        experiment_dirs.append(d)

  # Parse each experiment directory
  proc_args = []
  for exp_dir in experiment_dirs:
    exp_root = os.path.join(data_root, exp_dir)
    exp_dest = os.path.join(dest_root, exp_dir)

    # Add to arguments if more than one process is to be created, otherwise
    # directly scrape the experiment.
    if num_processes > 1:
      proc_args.append((parse_experiment_directory, exp_dir, exp_root, exp_dest,
                        ext_refs, select))
    else:
      parse_experiment_directory(exp_dir, exp_root, exp_dest, ext_refs, select)

  # Helper for parsing aux files in parallel.
  def _parallel(arg_tuple):
    arg_tuple[0](arg_tuple[1], arg_tuple[2], arg_tuple[3], arg_tuple[4],
                 arg_tuple[5])

  # Run the parsers in parallel if specified
  if num_processes > 1:
    pool = multiprocessing.Pool(num_processes)
    pool.map(parse_experiment_directory, proc_args)


def parse_experiment_directory(exp_name, data_root, dest_root, ext_refs,
                               select):
  """Parses a single experiment directory."""
  logging.info('> Now parsing experiment %s @ %s', exp_name, data_root)

  # Create the paths
  src_path = os.path.join(data_root, '{}.json'.format(exp_name))
  dest_path = os.path.join(dest_root, '{}.mcf'.format(exp_name))

  # Create the MCF file for the experiment summary
  contents = read_with_context(src_path)
  experiment_graph = Graph().parse(data=contents, format='json-ld')
  experiment_triples = collections.OrderedDict()

  # Add triples from the experiment JSON
  for s, p, o in experiment_graph:
    if ENCODE_EXPERIMENT_PREFIX in s:
      add_triple(experiment_triples, s, p, o, select)

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(experiment_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  mkdirs_if_dne(dest_root)
  write_mcf(schema_triples, dest_path)
  logging.info('> FINISHED! parsing experiment %s @ %s saved to %s', exp_name,
               data_root, dest_path)

  # Create MCF files for the given BED files
  data_dirs = []
  for data_dir in gfile.ListDirectory(data_root):
    dir_path = os.path.join(data_root, data_dir)
    if gfile.IsDirectory(dir_path):
      data_dirs.append(data_dir)
  for data_file_dir in data_dirs:
    data_file_root = os.path.join(data_root, data_file_dir)
    data_file_dest = os.path.join(dest_root, data_file_dir)
    parse_data_file(data_file_dir, data_file_root, data_file_dest, ext_refs,
                    select)


def parse_data_file(data_file_name, data_root, dest_root, ext_refs, select):
  """Parses the data file in the given data_root."""
  logging.info('> Now parsing data file %s @ %s', data_file_name, data_root)

  # Create the paths
  src_path = os.path.join(data_root, '{}.json'.format(data_file_name))
  dest_path = os.path.join(dest_root, '{}.mcf'.format(data_file_name))

  # Create the MCF file for the data summary
  contents = read_with_context(src_path)
  data_graph = Graph().parse(data=contents, format='json-ld')
  data_triples = collections.OrderedDict()

  # Add triples from the data summary JSON and look for the file type
  data_file_type = None
  for s, p, o in data_graph:
    if ENCODE_FILE_PREFIX in s:
      add_triple(data_triples, s, p, o, select)
    if normalize(p) == ENCODE_FILE_TYPE_PROP and data_file_type is None:
      data_file_type = str(o)

  # If no file type provided, return immediately
  if data_file_type is None:
    logging.warning('> WARNING: No file type was found for file: %s', src_path)
    return

  # Verify, schematize references, and write the MCF file.
  verified_triples = verify_references(data_triples, ext_refs)
  _, schema_triples = encode_to_schema_triples(verified_triples)
  mkdirs_if_dne(dest_root)
  write_mcf(schema_triples, dest_path)
  logging.info('> FINISHED! parsing data file %s @ %s saved to %s',
               data_file_name, data_root, dest_path)

  # Parse the bed file
  # bed_path = os.path.join(data_root, '{}.bed'.format(data_file_name))
  # bed_dest = os.path.join(dest_root, '{}_lines.mcf'.format(data_file_name))
  # parse_bed_file(data_file_name, data_file_type, bed_path, bed_dest)


def parse_bed_file(data_file_name, data_file_type, bed_path, bed_dest):
  """Parses the given bed file into an MCF file.

    stores it in the given bed_dest path.
  """
  logging.info('> Now parsing bed file %s @ %s', data_file_name, bed_path)

  # Construct the column index map based on the given bed file type.
  column_index_map = collections.OrderedDict()
  column_index_map['chromosome'] = 0
  column_index_map['chromosomeStart'] = 1
  column_index_map['chromosomeEnd'] = 2
  if data_file_type == 'bed':
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
    column_index_map['chromosomeStrand'] = 5
  elif data_file_type == 'bed broadPeak':
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
    column_index_map['chromosomeStrand'] = 5
    column_index_map['signalValue'] = 6
    column_index_map['pValue'] = 7
    column_index_map['qValue'] = 8
  elif data_file_type == 'bed narrowPeak':
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
    column_index_map['chromosomeStrand'] = 5
    column_index_map['signalValue'] = 6
    column_index_map['pValue'] = 7
    column_index_map['qValue'] = 8
    column_index_map['peak'] = 9
  elif data_file_type == 'bed idr_peak':
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
  elif data_file_type == 'bed bed3':
    # NOTE: Add additional parsing if required in the future
    pass
  elif data_file_type == 'bed bed3+':
    # NOTE: Add additional parsing if required in the future
    pass
  elif data_file_type == 'bed bed6+':
    # TODO(antaresc): Figure out what the last two columns represent
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
    column_index_map['chromosomeStrand'] = 5
  elif data_file_type == 'bed bed9':
    # TODO(antaresc): Implement
    pass
  elif data_file_type == 'bed bed12':
    column_index_map['bedName'] = 3
    column_index_map['bedScore'] = 4
    column_index_map['chromosomeStrand'] = 5
    column_index_map['thickStart'] = 6
    column_index_map['thickEnd'] = 7
    column_index_map['itemRGB'] = 8
    column_index_map['blockCount'] = 9
    column_index_map['blockSizes'] = 10
    column_index_map['blockStarts'] = 11
  elif data_file_type == 'bed bedMethyl':
    # TODO(antaresc): Implement
    pass
  else:
    logging.warning('> WARNING: Unrecognized file type: path %s type "%s"',
                    bed_path, data_file_type)
    return

  # Buffer for schema triples
  schema_triples = collections.OrderedDict()
  lines_translated = 0

  # Create the schema triples according to the column index map.
  # NOTE: If no bedline label is provided, the row number is used to identify
  #       the bed line.
  with gfile.Open(bed_path, 'r') as f:
    for idx, line in enumerate(f):
      # Skip track lines. Add parsing track lines at a later date.
      if 'track' in line:
        continue

      # Get the node id
      bed_line = line.strip().split()
      if 'bedName' in column_index_map and bed_line[
          column_index_map['bedName']] != '.':
        bed_name = bed_line[column_index_map['bedName']]
        node_id = 'BedLine_{}_{}'.format(bed_name, data_file_name)
      else:
        node_id = 'BedLine_Line_{}_{}'.format(idx, data_file_name)

      # Create the triple map entry and add the entry
      bed_entry = collections.OrderedDict()
      stringify_props = [
          'chromosome', 'bedName', 'chromosomeStrand', 'itemRGB', 'blockSizes',
          'blockStarts'
      ]
      for prop, col_idx in column_index_map.items():
        value = bed_line[col_idx]

        # If the property is in the following list, then convert it to
        # a string.
        if prop in stringify_props:
          value = '"{}"'.format(value)
        bed_entry[prop] = [value]

      # Add reference to the original bed file and the type
      encode_bed_ref = '/files/{}/'.format(data_file_name)
      bed_entry['fromBedFile'] = [
          'l:{}'.format(encode_to_schema_ref(encode_bed_ref))
      ]
      bed_entry['typeOf'] = [DC_BED_LINE_TYPE]
      schema_triples[node_id] = bed_entry
      lines_translated += 1

      # Perform an intermittent write when the buffer reaches MAX_BUFFER_LENGTH
      # number of entries. This way, we don't store the entire MCF translation
      # of a 4G file AND write to CNS every iteration.
      if len(schema_triples) >= MAX_BUFFER_LENGTH:
        logging.info('> Flushing write buffer for %s.', data_file_name)
        write_mcf(schema_triples, bed_dest, mode='a')
        logging.info('> Total lines written for %s = %s', data_file_name,
                     lines_translated)
        schema_triples = collections.OrderedDict()

    # Write whatever is left over in the buffer
    write_mcf(schema_triples, bed_dest, mode='a')

  # Log completion of parsing
  logging.info('> FINISHED! parsing bed file %s @ %s saved to %s',
               data_file_name, bed_path, bed_dest)
  logging.info('> Final total lines written for %s = %s', data_file_name,
               lines_translated)


# ------------------------------- MAIN FUNCTION -------------------------------

# SOME FURTHER INSTRUCTIONS
# - Set the output root to be "/cns/jv-d/home/datcom/v3_mcf/encode/mcf/" when
#   generating the MCF files for ingestion

DEFAULT_INPUT_ROOT = '/cns/jv-d/home/datcom/encode_project/raw'
DEFAULT_OUTPUT_ROOT = '/cns/jv-d/home/datcom/encode_project/mcf'
DEFAULT_NUM_PROC = 1

# Maps the Auxiliary category to the function that parses its contents.
AUXILIARY_CATEGORY_MAP = {
    'awards': parse_award,
    'biosample_types': parse_biosample_type,
    'biosamples': parse_biosample,
    'labs': parse_lab,
    'libraries': parse_library,
    'users': parse_user
}

FLAGS = flags.FLAGS

# Flags
flags.DEFINE_boolean('parse_auxiliary', False,
                     'Toggle to true if targeting auxiliary files')
flags.DEFINE_string('input_root', DEFAULT_INPUT_ROOT,
                    'The root folder of including all the Encode Data.')
flags.DEFINE_string(
    'output_root', DEFAULT_OUTPUT_ROOT,
    'The root folder of where the Encode Data will be written.')
flags.DEFINE_integer(
    'parallel',
    DEFAULT_NUM_PROC,
    'The maximum number of parsing processes to spawn',
    lower_bound=1)
flags.DEFINE_list('experiment_dirs', None, 'A list of directories to scrape.')


def main(unused_argv):
  """A note on usage.

  When running this scraper, it needs to have two types of calls:
  - One where parse_auxiliary is toggled to true. This will parse all auxiliary
    schema files.
  - The rest of various experiment folders specified. These are the folders
    taking pattern "ENC*"
  """
  register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')
  mkdirs_if_dne(NEW_SCHEMA_ROOT)
  if FLAGS.parse_auxiliary:
    parse_auxiliary_directories(
        FLAGS.input_root,
        FLAGS.output_root,
        FLAGS.parallel,
        select=default_select)
  else:
    parse_experiment_directories(
        FLAGS.input_root,
        FLAGS.output_root,
        FLAGS.parallel,
        experiment_dirs=FLAGS.experiment_dirs,
        select=default_select)


if __name__ == '__main__':
  app.run(main)
  
