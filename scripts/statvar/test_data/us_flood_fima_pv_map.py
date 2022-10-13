# Column headers to property:value mappings for US Flood FIMA  insurance claims.
# Full list of columns in:
# https://docs.google.com/spreadsheets/d/1rQ1vZK9UM9iD7pv_q6PIv22rhCGWs43lmyYGQ4Ostpg/edit#gid=28889498
{
   'countyCode' : {
       'observationAbout': 'dcid:geoId/{Number}',
   },
   'yearOfLoss' : {
       'observationDate': '{Number}',
   },
   'floodZone' : {
       # Schemaless statvar PV
       'floodZoneType': 'FloodZone{Data}',
   },
   'amountPaidOnBuildingClaim': {
       # StatVar PVs
       'populationType': 'dcs:CivicStructure',
       # Schemaless StatVar PVs.
       # Will be commented out in MCF as the values are not defined in schema.
       'measurementQualifier' : 'dcs:Annual',
       'measuredProperty': 'dcs:insuranceAmountPaid',
       'insuranceClaimType': 'dcs:BuildingClaim',
       'disasterType': 'Flood',
       # SVObs PVs
       'value': '{Number}',
       'unit': 'dcs:USDollar',
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/FIMAInsuranceClaims',
   },
   'amountPaidOnContentsClaim': {
       # StatVar PVs
       'populationType': 'dcs:CivicStructure',
       'measurementQualifier' : 'dcs:Annual',
       # Schemaless StatVar PVs.
       # Will be commented out in MCF as the values are not defined in schema.
       'measuredProperty': 'dcs:insuranceAmountPaid',
       'insuranceClaimType': 'dcs:ContentsClaim',
       'disasterType': 'Flood',
       # SVObs PVs
       'value': '{Number}',
       'unit': 'dcs:USDollar',
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/FIMAInsuranceClaims',
   },
   'id': {
       # StatVar PVs
       'measurementQualifier' : 'dcs:Annual',
       'measuredProperty': 'dcs:count',
       'populationType': 'dcs:CivicStructure',
       # Schemaless StatVar PVs
       # Will be commented out in MCF as the values are not defined in schema.
       'disasterType': 'Flood',
       'insuranceClaimType': 'dcs:BuildingClaim',
       # SVObs PVs
       'value': 1,
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/FIMAInsuranceClaims',
   },
}
