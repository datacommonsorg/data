# syntax=docker/dockerfile:1

# Copyright 2023 Google LLC
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

# build_type: local or cloud
ARG build_type=cloud

# build base image with all the dependencies installed
FROM python:3.12.8 as base
RUN apt-get update && apt-get install -y jq
ENV JAVA_HOME=/usr/local/openjdk-17
COPY --from=openjdk:17-slim $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN wget https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar
COPY requirements.txt .
RUN pip install -r requirements.txt

# build_type: local (copy local data repo)
FROM base as local
COPY --from=data . /data

# build_type: cloud (clone github data repo) 
FROM base as cloud
RUN git clone https://github.com/datacommonsorg/data.git

# build the final image
FROM ${build_type} as final
WORKDIR /data/import-automation/executor
ENTRYPOINT ["python", "main.py"]
