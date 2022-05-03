## To generate names for WHO stat vars
1. This script reads the who_properties.mcf and the who_gho_stat_vars.mcf files that are checked into the schema (and google3) repo. To copy these files over:

    a. fork and clone [datacommons schema github repository](https://github.com/datacommonsorg/schema)

    b. run:
      ```
      WHO_PROPS_DIR=<directory-of-forked-and-cloned-datacommons-schema-repository>/core
      WHO_SV_DIR=<directory-of-g4-client>/datacommons/import/mcf/resolved_mcf/raw_stat_vars/who_gho

      cd scripts/who/gho/svNames
      cp $WHO_PROPS_DIR/who_properties.mcf .
      cp $WHO_SV_DIR/who_gho_stat_vars.mcf .
      ```
2. run the script: 
```
python3 who_gho_sv_name.py
```