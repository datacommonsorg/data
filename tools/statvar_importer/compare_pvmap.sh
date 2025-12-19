#!/bin/bash
SCRIPT_DIR=${SCRIPT_DIR:-"$(realpath $0 | sed -e 's,statvar_importer/.*,statvar_importer,')"}
TMP_DIR="/usr/local/google/dc/tmp/statvar"
AGENTIC=${AGENTIC:-"0"}
STATVAR_METHOD=${STATVAR_METHOD:-"statvar"}
MODEL=${MODEL:-""}
STATVAR=${STATVAR:-"1"}

function echo_log {
  msg="[I $(date +%Y-%m-%d:%H%M%S)]: $@"
  echo -e "$msg" >> $LOG
  [[ "$QUIET" == "1" ]] || echo "$msg" >&2
}

function echo_err {
  msg="[E $(date +%Y-%m-%d:%H%M%S)]: $@"
  echo -e "$msg" >> $LOG
  [[ "$QUIET" == "1" ]] || echo "$msg" >&2
}

function echo_fatal {
  echo "[FATAL: $(date +%Y-%m-%d:%H%M%S)]: $@" >> $LOG
  echo "Logs in $LOG"
  exit 1
}

function parse_options {
  while (( $# > 0 )); do
    case $1 in
      -i) shift; IMPORT_NAME="$1";;
      -a) AGENTIC="1";;
      -pvm) shift; STATVAR_METHOD="$1";;
      -m) shift; MODEL="$1";;
      -ns) STATVAR="0";;
      -s) STATVAR="1";;
      -x) set -x;;
    esac
    shift
  done
  [[ -n "$MODEL" ]] && STATVAR_METHOD="$STATVAR_METHOD-$MODEL"
}

function gen_pvmap {
  local import="$1"; shift

  cwd="$PWD"
  cd "$SCRIPT_DIR"
  mkdir -p "$TMP_DIR"
  python -c "
import os
import sys

_SCRIPT_DIR = '$SCRIPT_DIR'
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.join(_DATA_DIR, 'util'))

from absl import flags;
from absl import logging;
logging.set_verbosity(2);

from counters import Counters
import statvar_imports_utils as s;

s._FLAGS.mark_as_parsed();

config=s.get_statvar_import_config('$import')
# Run statvar processor on import pvmap
logging.info(f'Running statvar for $import using import pvmap')
s.get_import_test_data('$import', config)
s.run_statvar_processor_test_data('$import', config)

if $STATVAR:
  # Generate pvmap using statvar
  logging.info(f'Generating pvmap for $import using $STATVAR_METHOD')
  config['genai_model'] = '$MODEL'
  config=s.generate_import_pvmap('$import', config, '$STATVAR_METHOD');
  s.run_statvar_processor_test_data('$import', config);


  # Get diff for statvar generated pvmap
  logging.info(f'Diffing pvmap from statvar for $import')
  s.get_pvmap_diff(config.get('pv_map'), config.get('${STATVAR_METHOD}_generated_pvmap'), os.path.join(config.get('import_dir', ''), 'tmp/${STATVAR_METHOD}/pvmap.diff'), {}, Counters(prefix='pvmap-${STATVAR_METHOD}-'));

  # Get diff for data_pvs
  logging.info(f'Diffing data pvs from ${STATVAR_METHOD} for $import')
  s.get_pvmap_diff(config.get('test_output_data_pvs'), config.get('${STATVAR_METHOD}_output_data_pvs'), os.path.join(config.get('import_dir', ''), 'tmp/${STATVAR_METHOD}/test_data_pvs.diff'), {}, Counters(prefix='data-pvs-${STATVAR_METHOD}-'));


if $AGENTIC:
  # Generate pvmap using agentic importer
  logging.info(f'Generating pvmap for $import using agentic importer')
  config=s.generate_import_pvmap('$import', config, 'agentic');
  s.run_statvar_processor_test_data('$import', config);
  config['agentic_generated_pvmap'] = os.path.join(config.get('import_dir'), 'tmp/agentic/output_pvmap.csv')

  # Run statvar processor on generated pvmap
  logging.info(f'Running statvar for $import using agentic pvmap')
  config['agentic_output_data_pvs'] = os.path.join(config.get('import_dir'), 'tmp/agentic/output/agentic_test_data_pvs.csv')
  s.run_statvar_processor_test_data('$import', config, {'pv_map': config.get('agentic_generated_pvmap'), 'input_data': config.get('test_data_input', ''), 'output_data_pvs':config.get('agentic_output_data_pvs')}, os.path.join(config.get('import_dir'), 'tmp', 'agentic', 'output'))

  # Get diff for agentic pvmap
  logging.info(f'Diffing pvmap from agentic for $import')
  s.get_pvmap_diff(config.get('pv_map'), config.get('agentic_generated_pvmap'), os.path.join(config.get('import_dir', ''), 'tmp/agentic/pvmap.diff'), {}, Counters(prefix='pvmap-agentic-'));

  # Get diff for data_pvs generated using agentic pvmap
  logging.info(f'Diffing data pvs from agentic for $import')
  s.get_pvmap_diff(config.get('test_output_data_pvs'), config.get('agentic_output_data_pvs'), os.path.join(config.get('import_dir', ''), 'tmp/agentic/test_data_pvs.diff'), {}, Counters(prefix='data-pvs-agentic-'));

" |& tee "$TMP_DIR/${STATVAR_METHOD}-pvmap-$import.log"
  cd "$cwd"
}

# Return if being sourced
(return 0 2>/dev/null) && return

parse_options "$@"

[[ -n "$IMPORT_NAME" ]] && gen_pvmap "$IMPORT_NAME"
