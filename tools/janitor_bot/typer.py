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
"""The Typer persona."""

import os
from .vertex_client import VertexClient

class TheTyper:
    """Adds type hints to Python code using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def add_type_hints(self, source_code):
        """Generates code with type hints added."""
        prompt = f"""
You are a senior Python engineer. Your task is to add PEP 484 type hints to the following Python code.

**Rules:**
1. Add type hints to function arguments and return values.
2. Infer types based on the function logic and usage.
3. If specific types are ambiguous, use `Any` or `Optional` as appropriate.
4. Ensure necessary imports (e.g., `from typing import List, Dict, Any, Optional`) are added at the top if missing.
5. Do NOT change any other logic, comments, or docstrings.
6. Return the FULL code with type hints.
7. Do not wrap output in markdown.

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
            print(f"Error adding type hints: {e}")
            return None

    def run(self, target_path, apply_changes=False, limit=None):
        """Runs the typer on a file or directory."""
        if os.path.isfile(target_path):
            self._process_file(target_path, apply_changes)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".py"):
                        self._process_file(os.path.join(root, file), apply_changes)

    def _process_file(self, file_path, apply_changes):
        print(f"Scanning {file_path} for missing type hints...")
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        typed_code = self.add_type_hints(source)
        if typed_code and typed_code.strip() != source.strip():
            if apply_changes:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(typed_code)
                print(f"  Added type hints to {file_path}")
            else:
                print("  [Dry Run] Type hints added (preview):")
                print("\n".join(typed_code.splitlines()[:10]))
        else:
            print("  No changes made (types might already be present or error occurred).")
