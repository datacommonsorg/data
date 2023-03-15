# Gas consumption and generation data - India

This directory has CSV, MCF and TMCF files to import gas consumption and generation data for India.

## File descriptions

[CSV file](./IndiaEnergy_Gas.csv) has five columns:
- Date (Observation Date)
- StateCode (Isocode for the state or country)
- value (StatVarObservation value)
- StatVar (Name of the Statistical Variable)
- unit (Measurement unit of the Statistical Variable)

[MCF file](./IndiaEnergy_Gas.mcf) has metacontent for the Statistical Variables in the csv file. [TMCF file](./IndiaEnergy_Gas.tmcf) has template metacontent to generate nodes from the csv file.

## List of Statistical Variables

StatVar column contains all the Statistical Variables available for Gas data. In general, a Statistical Variable name is based on the following pattern:
"{Periodicity}\_{MeasuredProperty}\_{EnergyCategory}\_{ConsumingSector}\_{EnergySource}". Consuming Sector is available only for consumption related Statistical Variables.

The list of all the StatVars available in this import are given below:
- Annual_Consumption_Fuel_ElectricityGeneration_NaturalGas
- Annual_Consumption_Fuel_Industry_NaturalGas
- Annual_Consumption_Fuel_Manufacturing_NaturalGas
- Annual_Consumption_Fuel_CommerceAndPublicServices_NaturalGas
- Annual_Consumption_Fuel_FoodAndTobaccoIndustry_NaturalGas
- Annual_Consumption_Fuel_EnergyIndustryOwnUse_NaturalGas
- Annual_Consumption_Fuel_OilRefineries_NaturalGas
- Annual_Consumption_Fuel_UN_UnspecifiedSector_NaturalGas
- Annual_Consumption_Fuel_Agriculture_NaturalGas
- Annual_Consumption_Fuel_ChemicalPetrochemicalIndustry_NaturalGas
- Annual_Consumption_Fuel_IronSteel_NaturalGas
- Annual_Consumption_Fuel_OilGasExtraction_NaturalGas
- Annual_Consumption_Fuel_Households_NaturalGas
- Annual_Consumption_Fuel_TransportIndustry_NaturalGas
- Monthly_Generation_Fuel_NaturalGas
- Monthly_Generation_Fuel_EIA_CoalDerivedSynthesisGas
- Annual_Imports_Fuel_NaturalGasLiquids
- Annual_Generation_Fuel_NaturalGas


## Import procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_edm.IndiaEnergy_Gas.preprocess`

This will generate MCF, TMCF and cleaned data CSV files.