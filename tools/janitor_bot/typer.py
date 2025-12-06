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

from .vertex_client import VertexClient

class TheTyper:
    """Adds type hints to Python code using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def transform(self, source, file_path="unknown", limit=None):
        """Generates code with type hints added."""
        # limit is currently ignored for Typer (full file rewrite)
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
{source}
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