# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Checks that Python files don't register absl flags when they're imported.

absl keeps one flag registry per process. A flag defined at module level is
registered as soon as the file is imported, for example by a test or by another
script. If two imported files define a flag with the same name, the import
fails with DuplicateFlagError. Define flags in a function instead, and call it
only when the file runs as a script:

    def _define_flags():
        flags.DEFINE_string('output_dir', 'out', 'Output folder.')

    if __name__ == '__main__':
        _define_flags()
        app.run(main)

A file fails the check if any of these run when the file is imported:
  - flags.DEFINE_*() calls,
  - other absl.flags functions that need the flag to be defined first, such as
    flags.mark_flag_as_required() or flags.register_validator(), or
  - calls to a function that defines flags, such as _define_flags().

Code runs on import if it's at module level, including inside module-level
if/try/with/for blocks and class bodies. Code inside functions or under
`if __name__ == '__main__':` doesn't.

Usage (from the repo root):
  python3 tools/lint/absl_flags_lint.py           # Check the whole repo.
  python3 tools/lint/absl_flags_lint.py a.py dir  # Check files or folders.
"""

import ast
import os
import re
import sys
from typing import NamedTuple

# absl.flags functions, other than DEFINE*, that need the flags they refer to
# to be defined first. They have to move into the function that defines the
# flags.
REGISTRY_FUNCTIONS = frozenset({
    'adopt_module_key_flags',
    'declare_key_flag',
    'mark_bool_flags_as_mutual_exclusive',
    'mark_flag_as_required',
    'mark_flags_as_mutual_exclusive',
    'mark_flags_as_required',
    'multi_flags_validator',
    'override_value',
    'register_multi_flags_validator',
    'register_validator',
    'set_default',
    'validator',
})

# Conventional names for functions that define flags, such as _define_flags()
# or define_common_flags(). A call to one of these on import fails the check,
# even if the function is defined in another file.
_DEFINE_FLAGS_FUNCTION_RE = re.compile(r'_?define(_\w+)?_flags')

# Directory names skipped anywhere in the tree.
EXCLUDED_DIRS = frozenset({
    '.git',
    # Python virtual environments. CI creates /workspace/.env.
    '.env',
    '.venv',
    'venv',
    'node_modules',
    '__pycache__',
    '.ruff_cache',
    # Local outputs and virtualenv folders, ignored by .gitignore.
    'scratch',
    'tmp',
    'lib',
    'bin',
})

# Files that still register flags on import, relative to the repo root. They're
# skipped until they're fixed. When you fix a file, remove it from this list:
# the check fails if a listed file no longer registers flags on import, or no
# longer exists.
#
# Don't add files to this list. Define the flags in a function instead (see
# the module docstring).
EXCLUDED_FILES = frozenset({
    'import-automation/executor/schedule_update_import.py',
    'import-automation/executor/scripts/generate_provisional_nodes.py',
    'import-automation/validator/main.py',
    'scripts/biomedical/NCBI_Taxonomy/scripts/format_ncbi_taxonomy.py',
    'scripts/biomedical/proteinInteractionEBI/parse_ebi.py',
    'scripts/biomedical/proteinInteractionMINT/parse_mint.py',
    'scripts/census_county_business_patterns/censuscountybusinesspatterns_test.py',
    'scripts/census_county_business_patterns/main.py',
    'scripts/earthengine/common_flags.py',
    'scripts/earthengine/earthengine_image.py',
    'scripts/earthengine/events_pipeline.py',
    'scripts/earthengine/process_events.py',
    'scripts/earthengine/raster_to_csv.py',
    'scripts/eurostat/health_determinants/common/denominator_mcf_generator.py',
    'scripts/eurostat/health_determinants/common/euro_stat.py',
    'scripts/eurostat/regional_statistics_by_nuts/life_expectancy/preprocess.py',
    'scripts/fires/firms/process.py',
    'scripts/floods/generate_floods_events.py',
    'scripts/noaa_gfs/dc_bq_ingest.py',
    'scripts/noaa_gfs/download_noaa_gfs_grib.py',
    'scripts/noaa_gfs/grib_statvar_processor.py',
    'scripts/un/energy/download.py',
    'scripts/us_bea/states_gdp/import_data.py',
    'scripts/us_bea/states_gdp/import_industry_data_and_gen_mcf.py',
    'scripts/us_bjs/nps/import_data.py',
    'scripts/us_cdc/heat_related_illness/clean_data.py',
    'scripts/us_census/acs5yr/subject_tables/common/acs_spec_generator.py',
    'scripts/us_census/acs5yr/subject_tables/common/acs_spec_validator.py',
    'scripts/us_census/acs5yr/subject_tables/common/column_map_validator.py',
    'scripts/us_census/acs5yr/subject_tables/common/common_util.py',
    'scripts/us_census/acs5yr/subject_tables/common/helper_functions.py',
    'scripts/us_census/api_utils/census_api_config_fetcher.py',
    'scripts/us_census/api_utils/census_api_helpers.py',
    'scripts/us_census/api_utils/url_list_compiler.py',
    'scripts/us_census/enhanced_tmcf/process_mappings.py',
    'scripts/us_education/california_school_performance/download.py',
    'scripts/us_education/california_school_performance/process.py',
    'scripts/us_eia/opendata/process.py',
    'scripts/us_epa/airqualityindex/air_quality_aggregate.py',
    'scripts/us_fed/treasury_constant_maturity_rates/generate_csv_and_mcf.py',
    'scripts/us_hud/income/process.py',
    'scripts/us_nces/demographics/download.py',
    'scripts/us_usda/quickstats/process.py',
    'scripts/world_bank/wdi/worldbank.py',
    'statvar_imports/australia_statistics/download_script.py',
    'statvar_imports/australia_statistics/process.py',
    'statvar_imports/database_on_indian_economy/india_rbi_state_statistics/rbi_download.py',
    'statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/download.py',
    'statvar_imports/indonesia_census/demographics/download.py',
    'statvar_imports/japan_census/download_script.py',
    'statvar_imports/sweden_census/demographic/download_demographic.py',
    'statvar_imports/sweden_census/health/download_health.py',
    'statvar_imports/undata/download.py',
    'statvar_imports/us_urban_school/ap_ib_gt_enrollment/download_ap_ib_gt.py',
    'statvar_imports/us_urban_school/maths_and_science_enrollment/download.py',
    'tools/import_differ/import_differ.py',
    'tools/import_validation/validator_goldens.py',
    'tools/sdmx_import/sdmx_cli.py',
    'tools/statvar_importer/config_flags.py',
    'tools/statvar_importer/data_sampler.py',
    'tools/statvar_importer/filter_data_outliers.py',
    'tools/statvar_importer/json_to_csv.py',
    'tools/statvar_importer/mcf_diff.py',
    'tools/statvar_importer/mcf_file_util.py',
    'tools/statvar_importer/mcf_filter.py',
    'tools/statvar_importer/place/place_resolver.py',
    'tools/statvar_importer/place/wiki_place_resolver.py',
    'tools/statvar_importer/process_http_server.py',
    'tools/statvar_importer/process_spreadsheet.py',
    'tools/statvar_importer/schema/data_annotator.py',
    'tools/statvar_importer/schema/genai_helper.py',
    'tools/statvar_importer/schema/llm_pvmap_generator.py',
    'tools/statvar_importer/schema/llm_statvar_name_generator.py',
    'tools/statvar_importer/schema/schema_checker.py',
    'tools/statvar_importer/schema/schema_generator.py',
    'tools/statvar_importer/schema/schema_matcher.py',
    'tools/statvar_importer/schema/schema_reconciler.py',
    'tools/statvar_importer/schema/schema_resolver.py',
    'tools/statvar_importer/schema/schema_spell_checker.py',
    'tools/statvar_importer/semantic_matcher.py',
    'util/counters.py',
    'util/file_sharder.py',
    'util/log_util.py',
})

_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Kinds of flag-related calls, returned by _call_kind().
_DEFINES_FLAG = 'defines a flag'
_NEEDS_FLAG = 'needs a defined flag'
_CALLS_DEFINER = 'calls a function that defines flags'


class Violation(NamedTuple):
    """A flag-related call that runs when a file is imported."""
    line: int
    message: str


class _FlagsNames(NamedTuple):
    """Names a module uses to refer to absl.flags."""
    # Dotted names bound to the absl.flags module, such as 'flags'.
    modules: frozenset
    # Maps names imported with `from absl.flags import ...` to the absl.flags
    # function they refer to.
    functions: dict


def _find_flags_names(tree):
    """Returns the names a module uses to refer to absl.flags."""
    modules = {'absl.flags'}
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'absl.flags' and alias.asname:
                    modules.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            for alias in node.names:
                if node.module == 'absl' and alias.name == 'flags':
                    modules.add(alias.asname or alias.name)
                elif node.module == 'absl.flags':
                    functions[alias.asname or alias.name] = alias.name
    return _FlagsNames(frozenset(modules), functions)


def _dotted_name(node):
    """Returns 'a.b.c' for a chain of names like a.b.c, or None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


def _call_kind(call, flags_names, defining_functions):
    """Returns how a call affects the flag registry, or None if it doesn't.

    Args:
      call: An ast.Call node.
      flags_names: The _FlagsNames of the module that contains the call.
      defining_functions: Names of the module's functions that define flags.
    """
    func = call.func
    if isinstance(func, ast.Name):
        local_name = func.id
        # Use the absl.flags name for `from absl.flags import x as y`.
        name = flags_names.functions.get(local_name, local_name)
        from_flags = local_name in flags_names.functions
    elif isinstance(func, ast.Attribute):
        local_name = None
        name = func.attr
        from_flags = _dotted_name(func.value) in flags_names.modules
    else:
        return None

    if name.startswith('DEFINE_') or (name == 'DEFINE' and from_flags):
        return _DEFINES_FLAG
    if from_flags and name in REGISTRY_FUNCTIONS:
        return _NEEDS_FLAG
    if (local_name in defining_functions or
            _DEFINE_FLAGS_FUNCTION_RE.fullmatch(name)):
        return _CALLS_DEFINER
    return None


def _find_defining_functions(tree, flags_names):
    """Returns the names of the functions in a module that define flags.

    A function defines flags if its body makes a flag-related call (see
    _call_kind), including a call to another function in the module that
    defines flags.
    """
    calls_by_function = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = calls_by_function.setdefault(node.name, [])
            for statement in node.body:
                calls.extend(
                    n for n in ast.walk(statement) if isinstance(n, ast.Call))

    defining_functions = set()
    changed = True
    while changed:
        changed = False
        for name, calls in calls_by_function.items():
            if name in defining_functions:
                continue
            if any(
                    _call_kind(call, flags_names, defining_functions)
                    for call in calls):
                defining_functions.add(name)
                changed = True
    return defining_functions


def _is_main_guard(test):
    """Returns whether an `if` test is `__name__ == '__main__'`."""
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and
            isinstance(test.ops[0], ast.Eq)):
        return False
    operands = (test.left, test.comparators[0])
    names = {n.id for n in operands if isinstance(n, ast.Name)}
    values = {n.value for n in operands if isinstance(n, ast.Constant)}
    return '__name__' in names and '__main__' in values


class _ImportTimeCallFinder(ast.NodeVisitor):
    """Collects the calls in a module that run when the module is imported."""

    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Decorators and default argument values run when the function is
        # defined. The body runs only when the function is called.
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        self.visit(node.args)

    def visit_If(self, node):
        if _is_main_guard(node.test):
            # The body runs only when the file runs as a script, but an `else`
            # branch runs on import.
            for statement in node.orelse:
                self.visit(statement)
        else:
            self.generic_visit(node)


def _describe_call(call):
    """Returns a short description of a call, like flags.DEFINE_string('x')."""
    func = ast.unparse(call.func)
    if not call.args and not call.keywords:
        return f'{func}()'
    first = call.args[0] if call.args else None
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return f'{func}({first.value!r})'
    return f'{func}(...)'


def lint_source(source, filename='<unknown>'):
    """Returns the flag-related calls that run when a module is imported.

    Args:
      source: The module's source code, as str or bytes.
      filename: File name to use in syntax errors.

    Returns:
      A list of Violations, sorted by line.

    Raises:
      SyntaxError, ValueError: If the source can't be parsed.
    """
    tree = ast.parse(source, filename=filename)
    flags_names = _find_flags_names(tree)
    defining_functions = _find_defining_functions(tree, flags_names)
    finder = _ImportTimeCallFinder()
    finder.visit(tree)

    violations = []
    for call in finder.calls:
        kind = _call_kind(call, flags_names, defining_functions)
        if kind is None:
            continue
        message = f'{_describe_call(call)} runs on import'
        if kind == _CALLS_DEFINER:
            message += ' and defines flags'
        violations.append(Violation(call.lineno, message + '.'))
    return sorted(violations)


def lint_file(path):
    """Returns the Violations in a Python file. See lint_source()."""
    with open(path, 'rb') as f:
        source = f.read()
    # Every flag-related call needs one of these strings in the file: a
    # DEFINE_*() call, an absl.flags import, or a function named like
    # define_*_flags(). Skipping files without them avoids parsing most of
    # the repo.
    if b'DEFINE_' not in source and b'flags' not in source:
        return []
    return lint_source(source, filename=path)


def _list_python_files(paths):
    """Yields Python files under the given paths, skipping EXCLUDED_DIRS."""
    for path in paths:
        if os.path.isfile(path):
            candidates = [path]
        else:
            candidates = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = sorted(
                    d for d in dirnames if d not in EXCLUDED_DIRS)
                candidates.extend(
                    os.path.join(dirpath, name) for name in sorted(filenames))
        for candidate in candidates:
            if candidate.endswith('.py'):
                yield candidate


def _is_under(path, roots):
    """Returns whether a path is one of the roots or inside one of them."""
    path = os.path.abspath(path)
    for root in roots:
        root = os.path.abspath(root)
        if path == root or path.startswith(root.rstrip(os.sep) + os.sep):
            return True
    return False


def run(paths, repo_root=_REPO_ROOT, excluded_files=EXCLUDED_FILES):
    """Checks Python files and prints the problems found.

    Args:
      paths: Files or directories to check.
      repo_root: Directory that excluded_files entries are relative to.
      excluded_files: Repo-relative paths of files to skip. An entry fails the
        check if the file no longer registers flags on import or doesn't
        exist (if it's under one of the paths).

    Returns:
      The exit code: 0 if everything passes, 1 otherwise.
    """
    missing = [path for path in paths if not os.path.exists(path)]
    if missing:
        for path in missing:
            print(f'{path}: no such file or directory', file=sys.stderr)
        return 1

    num_checked = 0
    num_failed = 0
    num_skipped = 0
    found_violations = False
    stale_entries = []
    seen_entries = set()
    for path in _list_python_files(paths):
        rel_path = os.path.relpath(path, repo_root).replace(os.sep, '/')
        is_excluded = rel_path in excluded_files
        if is_excluded:
            seen_entries.add(rel_path)
        try:
            violations = lint_file(path)
        except (OSError, SyntaxError, ValueError) as e:
            num_failed += 1
            print(f'{rel_path}: cannot check file: {e}')
            continue
        if is_excluded:
            if violations:
                num_skipped += 1
            else:
                stale_entries.append(
                    f'{rel_path}: listed in EXCLUDED_FILES, but no longer '
                    'registers flags on import.')
            continue
        num_checked += 1
        if violations:
            num_failed += 1
            found_violations = True
            for violation in violations:
                print(f'{rel_path}:{violation.line}: {violation.message}')

    for rel_path in sorted(excluded_files - seen_entries):
        if _is_under(os.path.join(repo_root, rel_path), paths):
            stale_entries.append(
                f"{rel_path}: listed in EXCLUDED_FILES, but the file wasn't "
                'found.')

    for message in stale_entries:
        print(message)
    print(f'Checked {num_checked} Python files, {num_failed} failed, '
          f'{num_skipped} skipped (in EXCLUDED_FILES).')
    if found_violations:
        print(
            'ERROR: Define absl flags only when a script runs, not when it '
            'is imported. Move the calls listed above into a function, such '
            "as _define_flags(), and call it under `if __name__ == "
            "'__main__':`. See tools/lint/README.md.",
            file=sys.stderr)
    if stale_entries:
        print(
            'ERROR: Remove the files listed above from EXCLUDED_FILES in '
            'tools/lint/absl_flags_lint.py.',
            file=sys.stderr)
    return 1 if num_failed or stale_entries else 0


def main(argv):
    return run(argv[1:] or [_REPO_ROOT])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
