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
import os
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

    def process_file(self, file_path, apply_changes=False, limit=None):
        """Scans a file for missing docstrings and optionally applies fixes."""
        print(f"Scanning {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"Skipping {file_path}: SyntaxError")
            return

        functions_to_document = []

        # Traverse AST to find functions without docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    functions_to_document.append(node)

        if not functions_to_document:
            return

        print(
            f"Found {len(functions_to_document)} functions missing "
            f"docstrings in {file_path}"
        )

        # Reverse order to apply changes from bottom to top
        functions_to_document.sort(key=lambda x: x.lineno, reverse=True)

        modified_lines = source.splitlines()

        count = 0
        for node in functions_to_document:
            if limit is not None and count >= limit:
                break

            try:
                func_source = ast.get_source_segment(source, node)
            except AttributeError:
                print("  Skipping: Cannot extract source segment.")
                continue

            if not func_source:
                continue

            print(f"  generating docstring for '{node.name}'...")
            raw_docstring = self.generate_docstring(func_source, node.name)

            if raw_docstring:
                indentation = " " * (node.body[0].col_offset)
                formatted_docstring = self._format_docstring(
                    raw_docstring, indentation)

                if apply_changes:
                    insert_line_index = node.body[0].lineno - 1
                    modified_lines.insert(insert_line_index,
                                          formatted_docstring)
                    print(f"  Applied docstring for {node.name}")
                else:
                    print(f"  [Dry Run] Generated:\n{formatted_docstring}")
                
                count += 1

        if apply_changes and count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(modified_lines))
            print(f"Saved changes to {file_path}")

    def run(self, target_path, apply_changes=False, limit=None):
        """Runs the docstring generation process on a file or directory."""
        if os.path.isfile(target_path):
            self.process_file(target_path, apply_changes, limit)
        else:
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".py"):
                        self.process_file(os.path.join(root, file), apply_changes, limit)
