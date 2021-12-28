# Oil consumption and generation data - India

This directory has CSV, MCF and TMCF files to import oil consumption and generation data for India.

## File descriptions

[CSV file](./IndiaEnergy_Oil.csv) has five columns:
- Date (Observation Date)
- StateCode (Isocode for the state or country)
- value (StatVarObservation value)
- StatVar (Name of the Statistical Variable)
- unit (Measurement unit of the Statistical Variable)

[MCF file](./IndiaEnergy_Oil.mcf) has metacontent for the Statistical Variables in the csv file. [TMCF file](./IndiaEnergy_Oil.tmcf) has template metacontent to generate nodes from the csv file.

## List of Statistical Variables

StatVar column contains all the Statistical Variables available for Oil data. In general, a Statistical Variable name is based on the following pattern:
"{Periodicity}\_{MeasuredProperty}\_{EnergyCategory}\_{ConsumingSector}\_{EnergySource}". Consuming Sector is available only for consumption related Statistical Variables.

The list of all the StatVars available in this import are given below:
- Annual_Consumption_Fuel_OilGasExtraction_FuelOil
- Annual_Consumption_Fuel_Agriculture_FuelOil
- Annual_Consumption_Fuel_Manufacturing_FuelOil
- Annual_Consumption_Fuel_MiningAndQuarryingIndustry_FuelOil
- Annual_Consumption_Fuel_UN_UnspecifiedSector_FuelOil
- Annual_Consumption_Fuel_ElectricityGeneration_FuelOil
- Annual_Consumption_Fuel_CommerceAndPublicServices_FuelOil
- Annual_Consumption_Fuel_TransportIndustry_FuelOil
- Annual_Consumption_Fuel_Households_FuelOil
- Annual_Consumption_Fuel_IronSteel_FuelOil
- Annual_Consumption_Fuel_ChemicalPetrochemicalIndustry_FuelOil
- Annual_Consumption_Fuel_Industry_FuelOil
- Annual_Consumption_Fuel_NonEnergyIndustry_FuelOil
- Annual_Consumption_Fuel_OilRefineries_FuelOil
- Annual_Capacity_Fuel_LiquefiedPetroleumGas
- Annual_Capacity_Fuel_CrudeOil
- Annual_Capacity_Fuel_PetroleumLiquids
- Monthly_Imports_Fuel_LiquefiedPetroleumGas
- Monthly_Imports_Fuel_Naphtha
- Monthly_Imports_Fuel_EIA_Kerosene
- Monthly_Imports_Fuel_GasolineJetFuel
- Monthly_Imports_Fuel_DieselOil
- Monthly_Imports_Fuel_OilShaleAndTarSands
- Monthly_Imports_Fuel_PetroleumCoke
- Monthly_Imports_Fuel_UN_OtherOilProducts
- Monthly_Imports_Fuel_FuelOil
- Monthly_Imports_Fuel_MotorGasoline
- Monthly_Imports_Fuel_Lubricants


## Import procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_edm.IndiaEnergy_Oil.preprocess`

This will generate MCF, TMCF and cleaned data CSV files.