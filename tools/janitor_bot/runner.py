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
"""Bot Runner: Handles I/O, Safety Checks, and Application."""

import os
import sys
import tempfile
import py_compile
import shutil

class BotRunner:
    """Executes a Persona on files with safety checks."""

    def __init__(self, apply_changes=False, verify=True):
        self.apply_changes = apply_changes
        self.verify = verify

    def run(self, persona, target_path, limit=None):
        """Runs the persona on a file or directory."""
        if os.path.isfile(target_path):
            self._process_file(persona, target_path, limit)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".py"):
                        self._process_file(os.path.join(root, file), persona, limit)

    def _process_file(self, persona, file_path, limit):
        print(f"Scanning {file_path}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_source = f.read()
        except UnicodeDecodeError:
            print(f"  Skipping {file_path}: Not a text file.")
            return

        # 1. Transform (Persona Logic)
        # The persona should return the full modified source code, or None if no changes.
        try:
            new_source = persona.transform(original_source, file_path=file_path, limit=limit)
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            return

        if new_source is None or new_source.strip() == original_source.strip():
            # No changes needed
            return

        # 2. Verify (Safety Net)
        if self.verify:
            if not self._verify_syntax(new_source):
                print(f"  [SAFETY NET] Skipping {file_path}: Generated code failed syntax check.")
                return

        # 3. Apply or Preview
        if self.apply_changes:
            self._backup_and_write(file_path, new_source)
            print(f"  Applied changes to {file_path}")
        else:
            print(f"  [Dry Run] Changes detected for {file_path}. Preview:")
            self._print_diff(original_source, new_source)

    def _verify_syntax(self, source_code):
        """Checks for Python syntax errors."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
                tmp.write(source_code)
                tmp_path = tmp.name
            
            py_compile.compile(tmp_path, doraise=True)
            return True
        except py_compile.PyCompileError as e:
            print(f"    Syntax Error: {e}")
            # Try to extract line number from the error string or attributes
            # PyCompileError often wraps SyntaxError.
            # Let's print the relevant lines from the file.
            print("    [DEBUG] Context around error:")
            try:
                with open(tmp_path, 'r') as f:
                    lines = f.readlines()
                
                # e.args often contains the inner SyntaxError
                # Check for lineno in exception details if possible, otherwise print all
                # For simplicity in this CLI, print the whole file with line numbers if small, 
                # or just the error message which usually contains the line number.
                
                # Parse line number from string like "File '...', line 10"
                import re
                match = re.search(r"line (\d+)", str(e))
                if match:
                    lineno = int(match.group(1))
                    start = max(0, lineno - 5)
                    end = min(len(lines), lineno + 5)
                    for i in range(start, end):
                        marker = ">>" if i + 1 == lineno else "  "
                        print(f"    {marker} {i + 1}: {lines[i].rstrip()}")
                else:
                    print("    (Could not parse line number, printing last 20 lines)")
                    for i, line in enumerate(lines[-20:]):
                        print(f"    {len(lines)-20+i+1}: {line.rstrip()}")

            except Exception as debug_err:
                print(f"    Error reading temp file for debug: {debug_err}")

            return False
        except Exception as e:
            print(f"    Verification Error: {e}")
            return False
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _backup_and_write(self, file_path, content):
        """Writes new content. (Backup logic can be added here if needed, but git is usually enough)."""
        # For now, we rely on the Verify step to prevent bad writes. 
        # If we wanted a restore file, we could write .bak here.
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _print_diff(self, old, new):
        """Prints a simple unified diff preview."""
        import difflib
        diff = difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile="Original",
            tofile="Modified",
            lineterm=""
        )
        # Print full diff
        for line in diff:
            print(f"    {line}")
