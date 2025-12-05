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
"""Code cleaners (The Import Cleaner, The Dead Code Remover)."""

import os
from .vertex_client import VertexClient

class TheImportCleaner:
    """Identifies and removes unused imports using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def clean_imports(self, source_code):
        """Generates code with unused imports removed."""
        prompt = f"""
You are a senior Python engineer. Your task is to remove UNUSED imports from the following Python code.

**Rules:**
1. Remove only import statements that are not used in the code.
2. Do NOT change any other logic, comments, or docstrings.
3. Do NOT remove dead code (that is a separate task).
4. Return the FULL code with imports cleaned.
5. Do not wrap output in markdown.

**Code:**
{source_code}
"""
        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 8192},
            )
            return response.text.strip().replace("```python", "").replace("```", "")
        except Exception as e:
            print(f"Error cleaning imports: {e}")
            return None

    def run(self, target_path, apply_changes=False, limit=None):
        """Runs the import cleaner on a file or directory."""
        if os.path.isfile(target_path):
            self._process_file(target_path, apply_changes)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".py"):
                        self._process_file(os.path.join(root, file), apply_changes)

    def _process_file(self, file_path, apply_changes):
        print(f"Scanning {file_path} for unused imports...")
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        cleaned = self.clean_imports(source)
        if cleaned and cleaned.strip() != source.strip():
            if apply_changes:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)
                print(f"  Removed unused imports from {file_path}")
            else:
                print("  [Dry Run] Imports cleaned (preview):")
                print("\n".join(cleaned.splitlines()[:5]))
        else:
            print("  No unused imports found.")


class TheDeadCodeRemover:
    """Identifies and removes unreachable/dead code using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def remove_dead_code(self, source_code):
        """Generates code with dead code removed."""
        prompt = f"""
You are a senior Python engineer. Your task is to remove UNREACHABLE/DEAD code from the following Python file.

**Rules:**
1. Remove code that can never be executed (e.g., statements after a return/raise in the same block).
2. Do NOT remove unused imports (that is a separate task).
3. Do NOT change logic that is reachable.
4. Return the FULL cleaned code.
5. Do not wrap output in markdown.

**Code:**
{source_code}
"""
        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 8192},
            )
            return response.text.strip().replace("```python", "").replace("```", "")
        except Exception as e:
            print(f"Error removing dead code: {e}")
            return None

    def run(self, target_path, apply_changes=False, limit=None):
        """Runs the dead code remover on a file or directory."""
        if os.path.isfile(target_path):
            self._process_file(target_path, apply_changes)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".py"):
                        self._process_file(os.path.join(root, file), apply_changes)

    def _process_file(self, file_path, apply_changes):
        print(f"Scanning {file_path} for dead code...")
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        cleaned = self.remove_dead_code(source)
        if cleaned and cleaned.strip() != source.strip():
            if apply_changes:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)
                print(f"  Removed dead code from {file_path}")
            else:
                print("  [Dry Run] Dead code removed (preview):")
                # Show lines around where changes likely happened
                lines = cleaned.splitlines()
                mid = len(lines) // 2
                print("\n".join(lines[mid-5:mid+5]))
        else:
            print("  No dead code found.")
