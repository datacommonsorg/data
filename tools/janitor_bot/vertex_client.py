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
"""Vertex AI initialization logic."""

import sys
import vertexai
from vertexai.generative_models import GenerativeModel

class VertexClient:
    """Wrapper for Vertex AI interactions."""

    def __init__(self, project_id, location, model_name):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.model = self._init_vertex_ai()

    def _init_vertex_ai(self):
        try:
            vertexai.init(project=self.project_id, location=self.location)
            return GenerativeModel(self.model_name)
        except Exception as e:
            print(f"Error initializing Vertex AI: {e}")
            sys.exit(1)
