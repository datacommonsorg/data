# Column headers to property:value mappings for US Flood FIMA  insurance claims.
# Full list of columns in:
# https://docs.google.com/spreadsheets/d/1rQ1vZK9UM9iD7pv_q6PIv22rhCGWs43lmyYGQ4Ostpg/edit#gid=28889498
{
   'censusTract' : {
       'observationAbout': 'dcid:geoId/{TractFipsCode}',
       # Pick census tract fips codes with atleast 11 digits.
       '#Regex': '(?P<TractFipsCode>[0-9]{11,})',
   },
   'countyCode' : {
       'observationAbout': 'dcid:geoId/{CountyFipsCode}',
       # Pick county fips codes with atleast 5 digits.
       '#Regex': '(?P<CountyFipsCode>^[0-9]{5}$)',
   },
   'state' : {
       # 2 letter state code is converted to dcid using us_state_codes.py
       'observationAbout': ['{Data}', 'dcid:country/USA' ],
   },
   'dateOfLoss': {
       'observationDate': '{YearMonth}',
       # Pick Year and month from date
       '#Regex': '(?P<YearMonth>^[0-9]{4}-[0-9]{2})',
       'naturalHazardType': 'FloodEvent',
       'populationType': 'dcs:NaturalHazardInsurance',
   },
   'yearOfLoss' : {
       'observationDate': '{Number}',
       'naturalHazardType': 'FloodEvent',
       'populationType': 'dcs:NaturalHazardInsurance',
   },
   'ratedFloodZone' : {
       'floodZoneType': 'FEMAFloodZone{Data}',
   },
   'amountPaidOnBuildingClaim': {
       # StatVar PVs
       'measuredProperty': 'dcs:settlementAmount',
       'insuredThing': 'dcs:BuildingStructure',
       # SVObs PVs
       'value': '{Number}',
       'unit': 'dcs:USDollar',
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/NFIPInsuranceClaims',
   },
   'amountPaidOnContentsClaim': {
       # StatVar PVs
       'measuredProperty': 'dcs:settlementAmount',
       'insuredThing': 'dcs:BuildingContents',
       # SVObs PVs
       'value': '{Number}',
       'unit': 'dcs:USDollar',
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/NFIPInsuranceClaims',
   },
   'policyCount': {
       # StatVar PVs
       'measuredProperty': 'dcs:countOfClaims',
       'insuredThing': 'dcs:BuildingStructureAndContents',
       # SVObs PVs
       'value': 1,
       # Aggregations
       '#Aggregate': 'sum',
       'measurementMethod': 'dcs:dcAggregate/NFIPInsuranceClaims',
   },
}
