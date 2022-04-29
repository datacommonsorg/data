## To generate names for WHO stat vars
1. This script reads the who_properties.mcf and the who_gho_stat_vars.mcf files that are checked into the schema (and google3) repo. To copy these files over:
  ```
  WHO_PROPS_DIR=<directory-of-g4-client>/third_party/datacommons/schema/core
  WHO_SV_DIR=<directory-of-g4-client>/third_party/datacommons/schema/stat_vars

  cd scripts/who/gho/svNames
  cp $WHO_PROPS_DIR/who_properties.mcf .
  cp $WHO_SV_DIR/who_gho_stat_vars.mcf .
  ```
2. run the script: 
```
python3 who_gho_sv_name.py
```