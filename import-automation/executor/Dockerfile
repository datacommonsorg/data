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

ARG build_type=cloud

FROM python:3.12.8 as base
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/local/openjdk-17
COPY --from=openjdk:17-slim $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN wget https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base as local
COPY --from=data . /data

FROM base as cloud
RUN git clone https://github.com/datacommonsorg/data.git

FROM ${build_type} as final
WORKDIR /data/import-automation/executor
ENTRYPOINT ["python", "main.py"]
