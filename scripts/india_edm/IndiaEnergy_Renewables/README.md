# Renewable electricity consumption and generation data - India

This directory has CSV, MCF and TMCF files to import renewable electricity consumption and generation data for India.

## File descriptions

[CSV file](./IndiaEnergy_Renewables.csv) has five columns:
- Date (Observation Date)
- StateCode (Isocode for the state or country)
- value (StatVarObservation value)
- StatVar (Name of the Statistical Variable)
- unit (Measurement unit of the Statistical Variable)

[MCF file](./IndiaEnergy_Renewables.mcf) has metacontent for the Statistical Variables in the csv file. [TMCF file](./IndiaEnergy_Renewables.tmcf) has template metacontent to generate nodes from the csv file.

## List of Statistical Variables

StatVar column contains all the Statistical Variables available for Renewable Electricity data. In general, a Statistical Variable name is based on the following pattern:
"{Periodicity}\_{MeasuredProperty}\_{EnergyCategory}\_{ConsumingSector}\_{EnergySource}". Consuming Sector is available only for consumption related Statistical Variables.

The list of all the StatVars available in this import are given below:
- Annual_Generation_Electricity_Coal
- Annual_Generation_Electricity_PumpedHydro
- Annual_Generation_Electricity_Bagasse
- Annual_Generation_Electricity_Solar
- Annual_Generation_Electricity_RenewableEnergy
- Annual_Generation_Electricity_Wind
- Annual_Generation_Electricity_DieselOil
- Annual_Generation_Electricity_NaturalGas
- Annual_Generation_Electricity_NonRenewableWaste
- Annual_Generation_Electricity_Nuclear
- Annual_Generation_Electricity_LigniteCoal
- Annual_Generation_Electricity_Naphtha
- Annual_Capacity_Electricity_PumpedHydro
- Annual_Capacity_Electricity_Solar
- Annual_Capacity_Electricity_Wind
- Annual_Capacity_Electricity_Bagasse
- Annual_Capacity_Electricity_NonRenewableWaste
- Annual_Potential_Electricity_OtherBiomass
- Annual_Potential_Electricity_PumpedHydro
- Annual_Potential_Electricity_Solar
- Annual_Potential_Electricity_NonRenewableWaste
- Annual_Potential_Electricity_Wind
- Annual_Potential_Electricity_Bagasse


## Import procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_edm.IndiaEnergy_Renewables.preprocess`

This will generate MCF, TMCF and cleaned data CSV files.