#!/usr/bin/env python3

# Copyright 2025 Google LLC
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
"""Unit tests for the SDMX state handler."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.append(_SCRIPT_DIR)

from state_handler import StateHandler  # pylint: disable=import-error


class StateHandlerTest(unittest.TestCase):

    def test_missing_file_creates_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "demo.state.json")
            handler = StateHandler(state_path=path, dataset_prefix="demo")

            state = handler.get_state()

            self.assertTrue(os.path.exists(path))
            self.assertEqual(state.run_id, "demo")
            self.assertEqual(state.steps, {})

            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
            self.assertEqual(data["run_id"], "demo")
            self.assertEqual(data["steps"], {})

    def test_corrupt_file_creates_backup_and_resets_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "demo.state.json")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("{not-json}")

            handler = StateHandler(state_path=path, dataset_prefix="demo")
            state = handler.get_state()

            backups = [
                name for name in os.listdir(tmpdir)
                if name.startswith("demo.state.json.bad.")
            ]
            self.assertEqual(state.steps, {})
            self.assertGreaterEqual(len(backups), 1)

            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
            self.assertEqual(data["steps"], {})


if __name__ == "__main__":
    unittest.main()
