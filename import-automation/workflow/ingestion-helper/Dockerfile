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

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

WORKDIR /app

# Install protobuf compiler and curl
RUN apt-get update && apt-get install -y protobuf-compiler curl && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
COPY . .

# Install production dependencies using uv.
RUN uv pip install --system --no-cache .

# Fetch proto file from GitHub
RUN curl -o storage.proto https://raw.githubusercontent.com/datacommonsorg/import/master/pipeline/data/src/main/proto/storage.proto

# Generate proto descriptor set
RUN protoc --include_imports --descriptor_set_out=storage.pb storage.proto

# Run the functions framework
CMD ["functions-framework", "--target", "ingestion_helper"]
