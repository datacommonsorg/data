# Copyright 2024 Google LLC
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

# Author: Pradeep Kumar Krishnaswamy
# Date: 18-Apr-2024

#!/bin/bash

mkdir -p input; cd input

# download the newest ncbi taxdump file and uncompress it
curl -o ncbi_taxdump.tar.Z https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.Z
uncompress ncbi_taxdump.tar.Z
tar -xvf ncbi_taxdump.tar
rm ncbi_taxdump.tar

# download the newest ncbi taxcat file and uncompress it
curl -o ncbi_taxcat.tar.gz https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxcat.tar.gz
tar -xvzf ncbi_taxcat.tar.gz
rm ncbi_taxcat.tar.gz
