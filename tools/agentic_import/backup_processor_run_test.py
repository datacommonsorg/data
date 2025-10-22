#!/usr/bin/env python3

import tempfile
import unittest
import uuid
from pathlib import Path

from tools.agentic_import import backup_processor_run


class BackupProcessorRunTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.working_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_backup(self, paths, max_dir_files=30) -> Path:
        run_id = f'gemini_test_{uuid.uuid4().hex}'
        return backup_processor_run.execute_backup(
            working_dir=self.working_dir,
            gemini_run_id=run_id,
            path_specs=list(paths),
            max_dir_files=max_dir_files,
        )

    def _read_manifest(self, backup_dir: Path) -> str:
        manifest_path = backup_dir / 'backup_manifest.txt'
        with open(manifest_path, 'r') as manifest_file:
            return manifest_file.read()

    def test_copies_requested_files(self):
        first = self.working_dir / 'a.txt'
        second = self.working_dir / 'b.txt'
        first.write_text('first')
        second.write_text('second')

        backup_dir = self._run_backup(['a.txt', 'b.txt'])

        self.assertTrue((backup_dir / 'a.txt').exists())
        self.assertTrue((backup_dir / 'b.txt').exists())
        manifest = self._read_manifest(backup_dir)
        self.assertIn('a.txt', manifest)
        self.assertIn('b.txt', manifest)
        self.assertNotIn('Skipped (missing or blocked):', manifest)

    def test_missing_file_reported(self):
        present = self.working_dir / 'present.txt'
        present.write_text('content')

        backup_dir = self._run_backup(['missing.txt', 'present.txt'])

        self.assertTrue((backup_dir / 'present.txt').exists())
        manifest = self._read_manifest(backup_dir)
        self.assertIn('present.txt', manifest)
        self.assertIn('missing.txt', manifest)
        self.assertIn('Skipped (missing or blocked):', manifest)

    def test_directory_skipped_when_over_cap(self):
        big_dir = self.working_dir / 'bigdir'
        big_dir.mkdir()
        for index in range(31):
            (big_dir / f'file_{index}.txt').write_text('x')

        backup_dir = self._run_backup(['bigdir'])

        self.assertFalse((backup_dir / 'bigdir').exists())
        manifest = self._read_manifest(backup_dir)
        self.assertIn('bigdir', manifest)

    def test_directory_copied_when_under_cap(self):
        small_dir = self.working_dir / 'smalldir'
        small_dir.mkdir()
        for index in range(3):
            (small_dir / f'item_{index}.txt').write_text('data')

        backup_dir = self._run_backup(['smalldir'])

        copied_dir = backup_dir / 'smalldir'
        self.assertTrue(copied_dir.is_dir())
        for index in range(3):
            self.assertTrue((copied_dir / f'item_{index}.txt').exists())

    def test_circular_reference_skipped(self):
        datacommons = self.working_dir / '.datacommons'
        datacommons.mkdir(parents=True, exist_ok=True)
        (datacommons / 'test.txt').write_text('content')

        backup_dir = self._run_backup(['.datacommons'])

        self.assertFalse((backup_dir / '.datacommons').exists())
        manifest = self._read_manifest(backup_dir)
        self.assertIn('SKIP .datacommons', manifest)
        self.assertNotIn('OK .datacommons', manifest)


if __name__ == '__main__':
    unittest.main()
