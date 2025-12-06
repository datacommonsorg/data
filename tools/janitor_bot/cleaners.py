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

import json
from .vertex_client import VertexClient

class TheImportCleaner:
    """Identifies and removes unused imports using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def transform(self, source, file_path="unknown", limit=None):
        """Generates code with unused imports removed."""
        # limit is ignored for file-level cleaning
        prompt = f"""
You are a senior Python engineer. Your task is to remove UNUSED imports from the following Python code.

**Rules:**
1. Remove only import statements that are not used in the code.
2. Do NOT change any other logic, comments, or docstrings.
3. Do NOT remove dead code (that is a separate task).
4. Return a JSON object with a single key "code" containing the FULL modified source code.

**Required JSON Structure:**
{{
    "code": "import os\n\n..."
}}

**Code:**
{source}
"""
        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1, 
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                },
            )
            return json.loads(response.text).get("code")
        except Exception as e:
            print(f"Error cleaning imports: {e}")
            return None


class TheDeadCodeRemover:
    """Identifies and removes unreachable/dead code using Vertex AI."""

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def transform(self, source, file_path="unknown", limit=None):
        """Generates code with dead code removed."""
        prompt = f"""
You are a senior Python engineer. Your task is to remove UNREACHABLE/DEAD code from the following Python file.

**Rules:**
1. Remove code that can never be executed (e.g., statements after a return/raise in the same block).
2. Do NOT remove unused imports (that is a separate task).
3. Do NOT change logic that is reachable.
4. Return a JSON object with a single key "code" containing the FULL modified source code.

**Required JSON Structure:**
{{
    "code": "def func():\n    return 1\n"
}}

**Code:**
{source}
"""
        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1, 
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                },
            )
            return json.loads(response.text).get("code")
        except Exception as e:
            print(f"Error removing dead code: {e}")
            return None
