# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.12-slim

WORKDIR /app

# Install fast uv package installer and dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY import-automation/validator/requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r /app/requirements.txt

# Copy required tools and utilities directly from the data repo
COPY util/ /app/util/
COPY tools/statvar_importer/ /app/tools/statvar_importer/
COPY tools/import_differ/ /app/tools/import_differ/
COPY tools/import_validation/ /app/tools/import_validation/
COPY import-automation/validator/main.py /app/main.py
COPY import-automation/validator/validator_test.py /app/validator_test.py

ENV PYTHONPATH="/app:/app/util:/app/tools/import_differ:/app/tools/import_validation:/app/tools/statvar_importer"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "/app/main.py"]
