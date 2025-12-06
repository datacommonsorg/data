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
"""The Librarian persona."""

import ast
from .vertex_client import VertexClient

class TheLibrarian:
    """The Librarian persona for Janitor Bot.

    Identifies functions missing docstrings and generates them using Vertex AI.
    """

    def __init__(self, project_id, location, model_name):
        self.client = VertexClient(project_id, location, model_name)

    def generate_docstring(self, code_snippet, function_name):
        """Generates a Google-style docstring for a given function."""
        prompt = f"""
You are a senior Google software engineer. Your task is to write a comprehensive Google-style docstring for the following Python function.

**CRITICAL INSTRUCTION:**
You MUST include 'Args:', 'Returns:', and 'Examples:' sections. Do not skip them.

**Required Format:**
Summary line.

Detailed description of the function logic...

Args:
    arg_name (type): Description...

Returns:
    type: Description...

Raises:
    ErrorType: Description... (if applicable)

Examples:
    >>> function_call()
    result

**Function Name:** {function_name}
**Code:**
{code_snippet}
"""
        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 8192
                },
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating docstring for {function_name}: {e}")
            return None

    def _format_docstring(self, raw_docstring, indentation):
        """Formats the generated docstring with correct indentation."""
        docstring = raw_docstring.replace("```python", "").replace("```",
                                                                   "").strip()
        if not docstring.startswith('"""'):
            docstring = '"""' + docstring
        if not docstring.endswith('"""'):
            docstring = docstring + '"""'

        docstring_lines = docstring.splitlines()
        indented_docstring = [indentation + line for line in docstring_lines]
        return "\n".join(indented_docstring)

    def transform(self, source, file_path="unknown", limit=None):
        """Transforms source code by adding docstrings.

        Args:
            source (str): Original source code.
            file_path (str): File path for logging.
            limit (int): Max functions to process.

        Returns:
            str: Modified source code, or None if no changes.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"Skipping {file_path}: SyntaxError")
            return None

        functions_to_document = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    functions_to_document.append(node)

        if not functions_to_document:
            return None

        print(
            f"Found {len(functions_to_document)} functions missing "
            f"docstrings in {file_path}"
        )

        # Process bottom-up to keep line numbers valid during insertion
        functions_to_document.sort(key=lambda x: x.lineno, reverse=True)

        modified_lines = source.splitlines()
        changes_made = False
        count = 0

        for node in functions_to_document:
            if limit is not None and count >= limit:
                break

            try:
                func_source = ast.get_source_segment(source, node)
            except AttributeError:
                continue

            if not func_source:
                continue

            print(f"  Generating docstring for '{node.name}'...")
            raw_docstring = self.generate_docstring(func_source, node.name)

            if raw_docstring:
                indentation = " " * (node.body[0].col_offset)
                formatted_docstring = self._format_docstring(
                    raw_docstring, indentation)

                # Insert into modified_lines
                insert_line_index = node.body[0].lineno - 1
                modified_lines.insert(insert_line_index, formatted_docstring)
                changes_made = True
                count += 1

        if changes_made:
            return "\n".join(modified_lines)
        return None