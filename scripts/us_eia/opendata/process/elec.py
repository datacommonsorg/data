
import re

def extract_place_statvar(series_id, stats):
  if series_id.startswith('ELEC.PLANT.'):
    stats['error_unimplemented_plant_series'] += 1
    return (None, None)

  # ELEC.{MEASURE}.{ENERGY_SOURCE}-{PLACE}-{PRODUCER_SECTOR}.{PERIOD}
  m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^-]+)-([^.]+)\.([AQM])$", series_id)
  if m:
    measure = m.group(1)
    energy_source = m.group(2)
    place = m.group(3)
    producing_sector = m.group(4)
    period = m.group(5)
    sv_id = f"ELEC.{measure}.{energy_source}-{producing_sector}.{period}"
  else:
    # ELEC.{MEASURE}.{PLACE}-{CONSUMER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", series_id)
    if not m:
      stats['error_unparsable_series'] += 1
      return (None, None)

    measure = m.group(1)
    place = m.group(2)
    consuming_sector = m.group(3)
    period = m.group(4)
    sv_id = f"ELEC.{measure}.{consuming_sector}.{period}"
  return (place, sv_id)


##
## Maps for Schema
##

_PERIOD_MAP = {
    'A': 'Annual',
    'M': 'Monthly',
    'Q': 'Quarterly',
}

_CONSUMING_SECTOR = {
    'COM': 'Commercial',
    'IND': 'Industrial',
    'OTH': 'OtherSector',
    'RES': 'Residential',
    'TRA': 'Transportation',
    'ALL': 'ALL',
}

_PRODUCING_SECTOR = {
    '1': 'ElectricUtility',
    '8': 'Residential',
    '96': 'Commercial',
    '97': 'Industrial',
    '98': 'ElectricPower',
    '99': 'ALL',  # Special handled ALL
    # TODO(shanth): Add the rest
}

_ENERGY_SOURCE = {
    'COL': 'Coal',
    'COW': 'Coal',
    'GEO': 'Geothermal',
    'NG': 'NaturalGas',
    'NUC': 'Nuclear',
    'TSN': 'Solar',
    'WND': 'Wind',
    'ALL': 'ALL'
    # TODO(shanth): Add the rest
}

_MEASURE_MAP = {
    'GEN': [
        'Generation_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:generation',
    ],
    'SALES': [
        'RetailSales_Electricity',
        'populationType: dcs:Electricity',
        'measuredProperty: dcs:retailSales',
    ],
    'CONS_TOT': [
        'Consumption_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:consumption',
        'usedFor: dcs:ElectricityGeneration',
    ],
    'COST': [
        'Cost_Fuel_ForElectricityGeneration',
        'populationType: dcs:Fuel',
        'measuredProperty: dcs:cost',
        'usedFor: dcs:ElectricityGeneration',
    ],
    # TODO(shanth): Add the rest
}

_UNIT_MAP = {
    'GEN': ('MegaWattHour', '1000'),
    'SALES': ('KiloWattHour', '1000000'),
    'CONS_TOT': ('Mcf', '1000'),
    'COST': ('USDollarPerMcf', ''),
    # TODO(shanth): Add the rest
}

def generate_statvar_schema(raw_sv, rows, sv_map, stats):
  # ELEC.{MEASURE}.{ENERGY_SOURCE}-{PRODUCER_SECTOR}.{PERIOD}
  m = re.match(r"^ELEC\.([^.]+)\.([^-]+)-([^.]+)\.([AQM])$", raw_sv)
  if m:
    measure = m.group(1)
    energy_source = m.group(2)
    producing_sector = m.group(3)
    period = m.group(4)
    consuming_sector = ''
  else:
    # ELEC.{MEASURE}.{CONSUMER_SECTOR}.{PERIOD}
    m = re.match(r"^ELEC\.([^.]+)\.([^.]+)\.([AQM])$", raw_sv)
    if not m:
      stats['error_unparsable_raw_statvar'] += 1
      return False
    measure = m.group(1)
    consuming_sector = m.group(2)
    period = m.group(3)
    energy_source = ''
    producing_sector = ''

  sv_id_parts = [_PERIOD_MAP[period]]
  sv_pvs = [
      'typeOf: dcs:StatisticalVariable',
      # TODO(shanth): use new property in next iteration
      f"measurementQualifier: dcs:{_PERIOD_MAP[period]}",
      f"statType: dcs:measuredValue",
  ]

  # Get popType and mprop based on measure.
  measure_pvs = _MEASURE_MAP.get(measure, None)
  if not measure_pvs:
    stats['error_missing_measure'] += 1
    return False
  sv_id_parts.append(measure_pvs[0])
  sv_pvs.extend(measure_pvs[1:])

  if energy_source:
    es = _ENERGY_SOURCE.get(energy_source, None)
    if not es:
      stats['error_missing_energy_source'] += 1
      return False
    if es != 'ALL':
      sv_id_parts.append(es)
      if '_Fuel_' in measure_pvs[0]:
        sv_pvs.append(f"fuelType: dcs:{es}")
      else:
        sv_pvs.append(f"energySource: dcs:{es}")

  if producing_sector:
    ps = _PRODUCING_SECTOR.get(producing_sector, None)
    if not ps:
      stats['error_missing_producing_sector'] += 1
      return False
    if ps != 'ALL':
      sv_id_parts.append(ps)
      if '_Fuel_' in measure_pvs[0]:
        sv_pvs.append(f"electricityProducingSector: dcs:{ps}")
      else:
        sv_pvs.append(f"producingSector: dcs:{ps}")

  if consuming_sector:
    cs = _CONSUMING_SECTOR.get(consuming_sector, None)
    if not cs:
      stats['error_missing_consuming_sector'] += 1
      return False
    if cs != 'ALL':
      sv_id_parts.append(cs)
      sv_pvs.append(f"consumingSector: dcs:{cs}")

  (unit, sfactor) = _UNIT_MAP.get(measure, (None, None))
  if not unit and not sfactor:
    stats['error_missing_unit'] += 1
    return False

  sv_id = '_'.join(sv_id_parts)

  # Update the rows with new StatVar ID value and additional properties.
  for row in rows:
    row['stat_var'] = f"dcid:{sv_id}"
    if unit:
      row['unit'] = f"dcid:{unit}"
    if sfactor:
      row['scaling_factor'] = sfactor

  if sv_id not in sv_map:
    node = f"Node: dcid:{sv_id}"
    sv_map[sv_id] = '\n'.join([node] + sv_pvs)

  return True

