# Coal consumption and generation data - India

This directory has CSV, MCF and TMCF files to import coal consumption and generation data for India.

## File descriptions

[CSV file](./IndiaEnergy_Coal.csv) has five columns:
- Date (Observation Date)
- StateCode (Isocode for the state or country)
- value (StatVarObservation value)
- StatVar (Name of the Statistical Variable)
- unit (Measurement unit of the Statistical Variable)

[MCF file](./IndiaEnergy_Coal.mcf) has metacontent for the Statistical Variables in the csv file. [TMCF file](./IndiaEnergy_Coal.tmcf) has template metacontent to generate nodes from the csv file.

## List of Statistical Variables

StatVar column contains all the Statistical Variables available for Coal data. In general, a Statistical Variable name is based on the following pattern:
"{Periodicity}\_{MeasuredProperty}\_{EnergyCategory}\_{ConsumingSector}\_{EnergySource}". Consuming Sector is available only for consumption related Statistical Variables.

The list of all the StatVars available in this import are given below:
- Annual_Consumption_Coal_ElectricityGeneration_CoalProducts
- Annual_Consumption_Coal_IronSteel_CoalProducts
- Annual_Consumption_Coal_PaperPulpPrintIndustry_CoalProducts
- Annual_Consumption_Coal_NonFerrousMetalsIndustry_CoalProducts
- Annual_Consumption_Coal_ConstructionIndustry_CoalProducts
- Annual_Consumption_Coal_ChemicalPetrochemicalIndustry_CoalProducts
- Annual_Consumption_Coal_TextileAndLeatherIndustry_CoalProducts
- Annual_Consumption_Coal_UN_UnspecifiedSector_CoalProducts
- Annual_Consumption_Coal_CoalMines_CoalProducts
- Annual_Consumption_Coal_CokeOvens_CoalProducts
- Annual_Consumption_Coal_Agriculture_CoalProducts
- Annual_Consumption_Coal_ElectricityGeneration_LigniteCoal
- Annual_Consumption_Coal_NonFerrousMetalsIndustry_LigniteCoal
- Annual_Consumption_Coal_ConstructionIndustry_LigniteCoal
- Annual_Consumption_Coal_IronSteel_LigniteCoal
- Annual_Consumption_Coal_ChemicalPetrochemicalIndustry_LigniteCoal
- Annual_Consumption_Coal_PaperPulpPrintIndustry_LigniteCoal
- Annual_Consumption_Coal_TextileAndLeatherIndustry_LigniteCoal
- Annual_Consumption_Coal_UN_UnspecifiedSector_LigniteCoal
- Annual_Consumption_Coal_Agriculture_LigniteCoal
- Annual_Imports_Coal_CokingCoal
- Annual_Imports_Coal_CoalProducts
- Annual_Imports_Coal_LigniteCoal
- Annual_Reserves_Coal_CoalProducts
- Annual_Reserves_Coal_CokingCoal
- Annual_Generation_Coal_CokingCoal
- Annual_Generation_Coal_CoalProducts
- Annual_Generation_Coal_LigniteCoal

## Import procedure

The below script will generate; mcf, tmcf and csv files.

`python -m india_edm.IndiaEnergy_Coal.preprocess`

This will generate MCF, TMCF and cleaned data CSV files.