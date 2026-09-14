"""Constants used across wdi."""

from string import Template

POPS_FILE = 'pops_file'

START_YEAR_COLUMN = 4
YEAR_RANGE_START = 1960
YEAR_RANGE_END = 2023

INDICATOR_NAME = 'Indicator Name'
COUNTRY_CODE = 'Country Code'

CO2_EMISSIONS = 'CO2 emissions (metric tons per capita)'

POP_CO2_EMISSIONS_MCF_TEMPL = Template("""
Node: Pop_CO2_Emissions_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:Emissions
emittedThing: dcs:CarbonDioxide
location: dcid:$location
""")

OBS_CO2_EMISSIONS_MCF_TEMPL = Template("""
Node: Obs_CO2_Emissions_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_CO2_Emissions_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementDenominator: dcs:PerCapita
unit: dcs:MetricTon
""")

ELEC_CONSUMPTION = 'Electric power consumption (kWh per capita)'

POP_ELEC_CONSUMPTION_MCF_TEMPL = Template("""
Node: Pop_Consumption_Electricity_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:Consumption
consumedThing: dcs:Electricity
location: dcid:$location
""")

OBS_ELEC_CONSUMPTION_MCF_TEMPL = Template("""
Node: Obs_Consumption_Electricity_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Consumption_Electricity_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementDenominator: dcs:PerCapita
unit: dcs:KilowattHour
""")

ENERGY_USE = 'Energy use (kg of oil equivalent per capita)'

POP_ENERGY_USE_MCF_TEMPL = Template("""
Node: Pop_Energy_Use_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:Consumption
consumedThing: dcs:Energy
location: dcid:$location
""")

OBS_ENERGY_USE_MCF_TEMPL = Template("""
Node: Obs_Energy_Use_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Energy_Use_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementDenominator: dcs:PerCapita
unit: dcs:KilogramOfOilEquivalent
""")

GDP_NOMINAL = 'GDP (current US$)'

POP_GDP_NOMINAL_MCF_TEMPL = Template("""
Node: Pop_GDP_Nominal_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:EconomicActivity
activitySource: dcs:GrossDomesticProduction
location: dcid:$location
""")

OBS_GDP_NOMINAL_MCF_TEMPL = Template("""
Node: Obs_GDP_Nominal_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_GDP_Nominal_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementQualifier: dcs:Nominal
unit: dcs:USDollar
""")

GDP_GROWTH_RATE = 'GDP growth (annual %)'

POP_GDP_GROWTH_RATE_MCF_TEMPL = Template("""
Node: Pop_GDP_Growth_Rate_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:EconomicActivity
activitySource: dcs:GrossDomesticProduction
location: dcid:$location
""")

OBS_GDP_GROWTH_RATE_TEMPL = Template("""
Node: Obs_GDP_Growth_Rate_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_GDP_Growth_Rate_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
growthRate: $measured_value
""")

GDP_NOM_PER_CAPITA = 'GDP per capita (current US$)'

# Use POP_GDP_NOMINAL_MCF_TEMPL as POP template so that only one pop node
# will be generated.

OBS_GDP_NOM_PER_CAPITA_TEMPL = Template("""
Node: Obs_GDP_Nom_Per_Capita_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_GDP_Nominal_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementQualifier: dcs:Nominal
measurementDenominator: dcs:PerCapita
unit: dcs:USDollar
""")

GNI_IN_PPP = 'GNI, PPP (current international $)'

POP_GNI_IN_PPP_MCF_TEMPL = Template("""
Node: Pop_GNI_In_PPP_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: dcs:EconomicActivity
activitySource: dcs:GrossNationalIncome
location: dcid:$location
""")

OBS_GNI_IN_PPP_MCF_TEMPL = Template("""
Node: Obs_GNI_In_PPP_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_GNI_In_PPP_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementQualifier: dcs:PurchasingPowerParity
unit: dcs:InternationalDollar
""")

GNI_PPP_PER_CAPITA = 'GNI per capita, PPP (current international $)'

# Use POP_GNI_IN_PPP_MCF_TEMPL as POP template so that only one pop node will
# be generated.

OBS_GNI_PPP_PER_CAPITA_MCF_TEMPL = Template("""
Node: Obs_GNI_PPP_Per_Capita_Amount_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_GNI_In_PPP_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:amount
measuredValue: $measured_value
measurementQualifier: dcs:PurchasingPowerParity
measurementDenominator: dcs:PerCapita
unit: dcs:InternationalDollar
""")

INTER_USER_PERC = 'Individuals using the Internet (% of population)'

POP_INTER_USER_PERC_MCF_TEMPL = Template("""
Node: Pop_Inter_User_Perc_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: schema:Person
isInternetUser: schema:True
location: dcid:$location
""")

OBS_INTER_USER_PERC_MCF_TEMPL = Template("""
Node: Obs_Inter_User_Perc_Count_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Inter_User_Perc_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:count
measuredValue: $measured_value
measurementDenominator: dcs:PerCapita
scalingFactor: 100
""")

LIFE_EXPECTANCY = 'Life expectancy at birth, total (years)'

POP_LIFE_EXPECTANCY_MCF_TEMPL = Template("""
Node: Pop_Life_Expectancy_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: dcid:$location
""")

OBS_LIFE_EXPECTANCY_MCF_TEMPL = Template("""
Node: Obs_Life_Expectancy_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Life_Expectancy_$location_abbr
observationDate: "$observation_date"
measuredProperty: dcs:lifeExpectancy
measuredValue: $measured_value
unit: dcs:Year
""")

FERTILITY_RATE = 'Fertility rate, total (births per woman)'

POP_FERTILITY_RATE_MCF_TEMPL = Template("""
Node: Pop_Fertility_Rate_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: schema:Person
gender: schema:Female
location: dcid:$location
""")

OBS_FERTILITY_RATE_MCF_TEMPL = Template("""
Node: Obs_Fertility_Rate_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Fertility_Rate_$location_abbr
observationDate: "$observation_date"
measuredProperty: dcs:fertilityRate
measuredValue: $measured_value
""")

POPULATION = 'Population, total'

POP_POPULATION_MCF_TEMPL = Template("""
Node: Pop_Population_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: dcid:$location
""")

OBS_POPULATION_MCF_TEMPL = Template("""
Node: Obs_Population_Count_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Population_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:count
measuredValue: $measured_value
""")

POPU_GROWTH_RATE = 'Population growth (annual %)'

POP_POPU_GROWTH_RATE_MCF_TEMPL = Template("""
Node: Pop_Popu_Growth_Rate_$location_abbr
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: dcid:$location
""")

OBS_POPU_GROWTH_RATE_MCF_TEMPL = Template("""
Node: Obs_Popu_Growth_Rate_Count_${location_abbr}_$observation_date
typeOf: schema:Observation
observedNode: l:Pop_Popu_Growth_Rate_$location_abbr
observationDate: "$observation_date"
observationPeriod: "P1Y"
measuredProperty: dcs:count
growthRate: $measured_value
""")

INDICATOR_TEMP_MAP = {
    CO2_EMISSIONS: (POP_CO2_EMISSIONS_MCF_TEMPL, OBS_CO2_EMISSIONS_MCF_TEMPL),
    ELEC_CONSUMPTION:
        (POP_ELEC_CONSUMPTION_MCF_TEMPL, OBS_ELEC_CONSUMPTION_MCF_TEMPL),
    ENERGY_USE: (POP_ENERGY_USE_MCF_TEMPL, OBS_ENERGY_USE_MCF_TEMPL),
    GDP_NOMINAL: (POP_GDP_NOMINAL_MCF_TEMPL, OBS_GDP_NOMINAL_MCF_TEMPL),
    GDP_GROWTH_RATE: (POP_GDP_GROWTH_RATE_MCF_TEMPL, OBS_GDP_GROWTH_RATE_TEMPL),
    GDP_NOM_PER_CAPITA:
        (POP_GDP_NOMINAL_MCF_TEMPL, OBS_GDP_NOM_PER_CAPITA_TEMPL),
    GNI_IN_PPP: (POP_GNI_IN_PPP_MCF_TEMPL, OBS_GNI_IN_PPP_MCF_TEMPL),
    GNI_PPP_PER_CAPITA:
        (POP_GNI_IN_PPP_MCF_TEMPL, OBS_GNI_PPP_PER_CAPITA_MCF_TEMPL),
    INTER_USER_PERC:
        (POP_INTER_USER_PERC_MCF_TEMPL, OBS_INTER_USER_PERC_MCF_TEMPL),
    LIFE_EXPECTANCY:
        (POP_LIFE_EXPECTANCY_MCF_TEMPL, OBS_LIFE_EXPECTANCY_MCF_TEMPL),
    FERTILITY_RATE:
        (POP_FERTILITY_RATE_MCF_TEMPL, OBS_FERTILITY_RATE_MCF_TEMPL),
    POPULATION: (POP_POPULATION_MCF_TEMPL, OBS_POPULATION_MCF_TEMPL),
    POPU_GROWTH_RATE:
        (POP_POPU_GROWTH_RATE_MCF_TEMPL, OBS_POPU_GROWTH_RATE_MCF_TEMPL),
}
