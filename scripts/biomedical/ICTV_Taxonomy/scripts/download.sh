'''
This file downloads the most recent version of the ICTV Master Species List and
Virus Metadata Resource and prepares it for processing
'''
#!/bin/bash

# make input directory
mkdir -p input; cd input

# download NCBI data
curl -o ICTV_Virus_Species_List.xlsx https://ictv.global/msl/current
curl -o ICTV_Virus_Metadata_Resource.xlsx https://ictv.global/vmr/current
