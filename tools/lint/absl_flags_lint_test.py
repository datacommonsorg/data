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

import contextlib
import io
import os
import tempfile
import textwrap
import unittest

from tools.lint import absl_flags_lint


def _lint(source):
    """Lints dedented source code. The first line of code is line 1."""
    return absl_flags_lint.lint_source(textwrap.dedent(source).lstrip('\n'))


class LintSourceTest(unittest.TestCase):

    def test_define_at_module_level_fails(self):
        violations = _lint("""
            from absl import flags

            flags.DEFINE_string('output_dir', 'out', 'Output folder.')
            """)
        self.assertEqual(
            violations,
            [(3, "flags.DEFINE_string('output_dir') runs on import.")])

    def test_define_in_function_passes(self):
        violations = _lint("""
            from absl import flags

            def _define_flags():
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')
            """)
        self.assertEqual(violations, [])

    def test_define_under_main_guard_passes(self):
        violations = _lint("""
            from absl import flags

            if __name__ == '__main__':
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')

            if '__main__' == __name__:
                flags.DEFINE_string('input_path', None, 'Input CSV.')
            """)
        self.assertEqual(violations, [])

    def test_define_in_else_of_main_guard_fails(self):
        violations = _lint("""
            from absl import flags

            if __name__ == '__main__':
                pass
            else:
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')
            """)
        self.assertEqual(
            violations,
            [(6, "flags.DEFINE_string('output_dir') runs on import.")])

    def test_define_in_module_level_if_block_fails(self):
        violations = _lint("""
            from absl import flags

            if 'output_dir' not in flags.FLAGS:
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')
            """)
        self.assertEqual(
            violations,
            [(4, "flags.DEFINE_string('output_dir') runs on import.")])

    def test_define_in_class_body_fails(self):
        violations = _lint("""
            from absl import flags

            class Config:
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')

                def add_input_flag(self):
                    flags.DEFINE_string('input_path', None, 'Input CSV.')
            """)
        self.assertEqual(
            violations,
            [(4, "flags.DEFINE_string('output_dir') runs on import.")])

    def test_flag_holder_at_module_level_fails(self):
        violations = _lint("""
            from absl import flags

            _OUTPUT_DIR = flags.DEFINE_string('output_dir', 'out', 'Output.')
            """)
        self.assertEqual(
            violations,
            [(3, "flags.DEFINE_string('output_dir') runs on import.")])

    def test_define_with_other_import_styles_fails(self):
        violations = _lint("""
            import absl.flags
            from absl import flags as absl_flags
            from absl.flags import DEFINE_boolean
            from absl.flags import DEFINE_float as define_float

            absl.flags.DEFINE_string('output_dir', 'out', 'Output folder.')
            absl_flags.DEFINE_integer('limit', 10, 'Row limit.')
            DEFINE_boolean('dry_run', False, 'Skip writing output.')
            define_float('ratio', 0.5, 'Sample ratio.')
            """)
        self.assertEqual(violations, [
            (6, "absl.flags.DEFINE_string('output_dir') runs on import."),
            (7, "absl_flags.DEFINE_integer('limit') runs on import."),
            (8, "DEFINE_boolean('dry_run') runs on import."),
            (9, "define_float('ratio') runs on import."),
        ])

    def test_generic_define_fails(self):
        violations = _lint("""
            from absl import flags

            flags.DEFINE(flags.ArgumentParser(), 'output_dir', 'out', 'Out.')
            """)
        self.assertEqual(violations, [(3, 'flags.DEFINE(...) runs on import.')])

    def test_mark_flag_as_required_at_module_level_fails(self):
        violations = _lint("""
            from absl import flags

            def _define_flags():
                flags.DEFINE_string('import_name', None, 'Import to run.')

            flags.mark_flag_as_required('import_name')
            """)
        self.assertEqual(
            violations,
            [(6, "flags.mark_flag_as_required('import_name') runs on import.")])

    def test_mark_flag_as_required_in_define_function_passes(self):
        violations = _lint("""
            from absl import flags

            def _define_flags():
                flags.DEFINE_string('import_name', None, 'Import to run.')
                flags.mark_flag_as_required('import_name')

            if __name__ == '__main__':
                _define_flags()
            """)
        self.assertEqual(violations, [])

    def test_validator_decorator_at_module_level_fails(self):
        violations = _lint("""
            from absl import flags

            @flags.validator('port', message='Port must be positive.')
            def _check_port(value):
                return value > 0
            """)
        self.assertEqual(violations,
                         [(3, "flags.validator('port') runs on import.")])

    def test_registry_function_imported_from_absl_flags_fails(self):
        violations = _lint("""
            from absl.flags import mark_flag_as_required

            mark_flag_as_required('import_name')
            """)
        self.assertEqual(
            violations,
            [(3, "mark_flag_as_required('import_name') runs on import.")])

    def test_same_names_from_other_modules_pass(self):
        violations = _lint("""
            import config
            import macros
            from schema import validator

            config.set_default('output_dir', 'out')
            macros.DEFINE('VERSION', 2)
            validator('statvar')
            """)
        self.assertEqual(violations, [])

    def test_calling_define_function_at_module_level_fails(self):
        violations = _lint("""
            from absl import flags

            def _define_flags():
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')

            _define_flags()
            """)
        self.assertEqual(
            violations,
            [(6, '_define_flags() runs on import and defines flags.')])

    def test_calling_function_that_defines_flags_indirectly_fails(self):
        violations = _lint("""
            from absl import flags

            def _add_output_flags():
                flags.DEFINE_string('output_dir', 'out', 'Output folder.')

            def _setup():
                _add_output_flags()

            _setup()
            """)
        self.assertEqual(violations,
                         [(9, '_setup() runs on import and defines flags.')])

    def test_calling_define_flags_function_from_other_module_fails(self):
        violations = _lint("""
            import common_flags

            common_flags.define_flags()
            """)
        self.assertEqual(violations, [
            (3, 'common_flags.define_flags() runs on import and defines flags.')
        ])

    def test_other_module_level_code_passes(self):
        violations = _lint("""
            from absl import flags
            from absl import logging

            FLAGS = flags.FLAGS
            logging.set_verbosity(logging.INFO)

            def _load_config():
                return {}

            _CONFIG = _load_config()
            """)
        self.assertEqual(violations, [])

    def test_syntax_error_raises(self):
        with self.assertRaises(SyntaxError):
            _lint('def broken(:\n')


# A file that defines a flag on line 3, at module level.
_BAD_SOURCE = """\
from absl import flags

flags.DEFINE_string('output_dir', 'out', 'Output folder.')
"""

_GOOD_SOURCE = """\
from absl import flags


def _define_flags():
    flags.DEFINE_string('output_dir', 'out', 'Output folder.')
"""


class RunTest(unittest.TestCase):

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.root = self._tmp_dir.name

    def _write(self, rel_path, content):
        path = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def _run(self, excluded_files=(), paths=None):
        """Checks the temp repo. Returns (exit code, stdout, stderr)."""
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            exit_code = absl_flags_lint.run(
                paths or [self.root],
                repo_root=self.root,
                excluded_files=frozenset(excluded_files))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_passes_when_no_file_registers_flags_on_import(self):
        self._write('pkg/good.py', _GOOD_SOURCE)

        exit_code, stdout, _ = self._run()

        self.assertEqual(exit_code, 0)
        self.assertIn('Checked 1 Python files, 0 failed, 0 skipped', stdout)

    def test_reports_flags_registered_on_import(self):
        self._write('pkg/bad.py', _BAD_SOURCE)

        exit_code, stdout, stderr = self._run()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "pkg/bad.py:3: flags.DEFINE_string('output_dir') runs on import.",
            stdout)
        self.assertIn('See tools/lint/README.md', stderr)

    def test_checks_only_given_paths(self):
        good_file = self._write('pkg/good.py', _GOOD_SOURCE)
        self._write('other/bad.py', _BAD_SOURCE)

        exit_code, stdout, _ = self._run(paths=[good_file])

        self.assertEqual(exit_code, 0)
        self.assertIn('Checked 1 Python files', stdout)

    def test_skips_excluded_dirs(self):
        self._write('.env/lib/python3.12/site-packages/pkg/module.py',
                    _BAD_SOURCE)
        self._write('pkg/scratch/experiment.py', _BAD_SOURCE)
        self._write('pkg/good.py', _GOOD_SOURCE)

        exit_code, stdout, _ = self._run()

        self.assertEqual(exit_code, 0)
        self.assertIn('Checked 1 Python files', stdout)

    def test_skips_files_in_excluded_files(self):
        self._write('pkg/bad.py', _BAD_SOURCE)

        exit_code, stdout, _ = self._run(excluded_files={'pkg/bad.py'})

        self.assertEqual(exit_code, 0)
        self.assertIn('Checked 0 Python files, 0 failed, 1 skipped', stdout)

    def test_fails_when_excluded_file_no_longer_registers_flags(self):
        self._write('pkg/fixed.py', _GOOD_SOURCE)

        exit_code, stdout, stderr = self._run(excluded_files={'pkg/fixed.py'})

        self.assertEqual(exit_code, 1)
        self.assertIn(
            'pkg/fixed.py: listed in EXCLUDED_FILES, but no longer registers '
            'flags on import.', stdout)
        self.assertIn('Remove the files listed above from EXCLUDED_FILES',
                      stderr)

    def test_fails_when_excluded_file_does_not_exist(self):
        self._write('pkg/good.py', _GOOD_SOURCE)

        exit_code, stdout, _ = self._run(excluded_files={'pkg/deleted.py'})

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "pkg/deleted.py: listed in EXCLUDED_FILES, but the file wasn't "
            'found.', stdout)

    def test_ignores_excluded_files_outside_given_paths(self):
        self._write('pkg/good.py', _GOOD_SOURCE)

        exit_code, _, _ = self._run(excluded_files={'other/deleted.py'},
                                    paths=[os.path.join(self.root, 'pkg')])

        self.assertEqual(exit_code, 0)

    def test_fails_when_file_cannot_be_parsed(self):
        # Mentions flags, so the file isn't skipped before parsing.
        self._write('pkg/broken.py', 'from absl import flags\ndef broken(:\n')

        exit_code, stdout, stderr = self._run()

        self.assertEqual(exit_code, 1)
        self.assertIn('pkg/broken.py: cannot check file:', stdout)
        self.assertNotIn('Define absl flags', stderr)

    def test_fails_when_path_does_not_exist(self):
        missing = os.path.join(self.root, 'does_not_exist.py')

        exit_code, _, stderr = self._run(paths=[missing])

        self.assertEqual(exit_code, 1)
        self.assertIn(f'{missing}: no such file or directory', stderr)


if __name__ == '__main__':
    unittest.main()
