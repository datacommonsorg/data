## Brazil Rural Development Program Data Import

This import contains statistical data related to various populations benefiting from Brazil's Rural Development Program at the country, state, and municipal levels.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

To get the necessary data files, you'll need to manually download them from the Program to Promote Rural Productive Activities data explorer.

Go to the website: `https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php`

Select the "Program to Promote Rural Productive Activities" category.

Manually download the required data files.

Place all downloaded files into the `input_files` folder.

This import will comes under semi automatic auto refresh.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. There are two ways to do this:

**Option A: Use the `run.sh` script**

The `run.sh` script automates the processing of all the downloaded files.

**Run the following command:**

```bash
sh run.sh
```

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

  * **Families\_RuralDevelopmentProgram\_Gender\_Brazil.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_Gender_Brazil.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_Gender_Brazil_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_Gender_Brazil_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
    ```

  * **Families\_RuralDevelopmentProgram\_Gender\_Municipality.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_Gender_Municipality.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_Gender_Municipality_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_Gender_Municipality_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **Families\_RuralDevelopmentProgram\_Gender\_State.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_Gender_State.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_Gender_State_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_Gender_State_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **Families\_RuralDevelopmentProgram\_SpecificPopulation\_Brazil.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_SpecificPopulation_Brazil.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_SpecificPopulation_Brazil_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_SpecificPopulation_Brazil_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
    ```

  * **Families\_RuralDevelopmentProgram\_SpecificPopulation\_Municipality.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_SpecificPopulation_Municipality.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_SpecificPopulation_Municipality_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_SpecificPopulation_Municipality_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **Families\_RuralDevelopmentProgram\_SpecificPopulation\_State.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/Families_RuralDevelopmentProgram_SpecificPopulation_State.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/Families_RuralDevelopmentProgram_SpecificPopulation_State_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/Families_RuralDevelopmentProgram_SpecificPopulation_State_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_brazil.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_brazil\_yearly.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_yearly.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_yearly_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_brazil_yearly_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_latest\_Municipality.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_Municipality.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_Municipality_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_Municipality_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_latest\_State.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_State.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_State_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_latest_State_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_State.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_State.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_State_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_State_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **FinancialResources\_Beneficiary\_RuralDevelopmentProgram\_yearly\_Municipality.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_yearly_Municipality.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/FinancialResources_Beneficiary_RuralDevelopmentProgram_yearly_Municipality_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/FinancialResources_Beneficiary_RuralDevelopmentProgram_yearly_Municipality_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **TotalFamilies\_Rural\_Development\_Program\_Brazil.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/TotalFamilies_Rural_Development_Program_Brazil.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/TotalFamilies_Rural_Development_Program_Brazil_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/TotalFamilies_Rural_Development_Program_Brazil_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
    ```

  * **TotalFamilies\_Rural\_Development\_Program\_Municipality.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/TotalFamilies_Rural_Development_Program_Municipality.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/TotalFamilies_Rural_Development_Program_Municipality_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/TotalFamilies_Rural_Development_Program_Municipality_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

  * **TotalFamilies\_Rural\_Development\_Program\_State.csv**

    ```bash
    python3 stat_var_processor.py \
    --input_data=gs://unresolved_mcf/country/brazil/VISDATA/Benefits_RuralDevelopmentProgram/latest/input_files/TotalFamilies_Rural_Development_Program_State.csv \
    --pv_map=../../statvar_imports/brazil_visdata/brazil_rural_development_program/TotalFamilies_Rural_Development_Program_State_pvmap.csv \
    --config_file=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_metadata.csv \
    --output_path=../../statvar_imports/brazil_visdata/brazil_rural_development_program/output_files/TotalFamilies_Rural_Development_Program_State_output \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --places_resolved_csv=../../statvar_imports/brazil_visdata/brazil_rural_development_program/brazil_places_resolver.csv
    ```

-----

### 📝 Notes

  * Place names are resolved to their Wikidata IDs and stored separately in the `place_resolver` sheet.
  * The `existing_statvar_mcf` flag is a required argument for the processing script.
