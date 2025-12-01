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
"""
Author: Samantha Piekos
Date: 02/26/2024
Name: download
Description: This file downloads the most recent version of the ICTV Master 
Species List and Virus Metadata Resource and prepares it for processing.
"""

#!/bin/bash


# make input directory
mkdir -p input; cd input

# download NCBI data
curl -o ICTV_Virus_Species_List.xlsx https://ictv.global/msl/current
curl -o ICTV_Virus_Metadata_Resource.xlsx https://ictv.global/vmr/current
