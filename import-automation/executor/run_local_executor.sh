# Copyright 2020 Google LLC
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

cd $(dirname $0)
python3 -m venv .env
. .env/bin/activate
pip3 install --disable-pip-version-check -q -r requirements.txt

# Setup files to run import executor locally
mkdir -p /tmp/import-tool
if [[ ! -f '/tmp/import-tool/import-tool.jar' ]]; then
    wget "https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar" \
      -O /tmp/import-tool/import-tool.jar
fi

python3 -m local_executor "$@"

deactivate
