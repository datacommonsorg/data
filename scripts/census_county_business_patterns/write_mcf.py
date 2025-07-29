# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""MCF generation code for County Business Program."""

import collections

# from google3.pyglib import stringutil


def new_observation(name,
                    observed_node_name,
                    observation_date,
                    measured_property,
                    measured_value,
                    unit=None):
    """Return a list of predicate, object tupes for the observation.

  Args:
    name: observation node name.
    observed_node_name: name of the observed node.
    observation_date: date in YYYY-MM-DD format
    measured_property: property being measured
    measured_value: value of the measurement
    unit: unit of measurement, if supplied.

  Returns:
    A list of (property, value) tuples for the node
  """
    return_list = [('Node', name), ('typeOf', 'dcs:Observation'),
                   ('observedNode', 'l:{}'.format(observed_node_name)),
                   ('observationDate', '"{}"'.format(observation_date)),
                   ('measuredProperty', 'dcs:{}'.format(measured_property)),
                   ('measuredValue', measured_value),
                   ('measurementMethod', 'dcs:CensusCBPSurvey')]
    if unit:
        return_list.append(('unit', '"{}"'.format(unit)))
    return return_list


def write_mcf(d, f):
    """Given an ordered dict, write it to file f."""
    for k, v in d.items():
        f.write('{}: {}\n'.format(k, v))
    f.write('\n')


def write_mcf_pop_obs(pop_est, obs_est, emp_nf, pop_emp, obs_emp, ap_nf,
                      obs_payroll, out_f):
    """Write MCF nodes for population and observations."""
    count_obs = 0
    count_pops = 0
    # Write out the populations and observations if the noise flag is not 'D'
    # Number of establishments is considered public information.
    write_mcf(pop_est, out_f)
    write_mcf(obs_est, out_f)
    count_obs += 1
    count_pops += 1

    if emp_nf != 'D':
        write_mcf(pop_emp, out_f)
        write_mcf(obs_emp, out_f)
        count_obs += 1
        count_pops += 1

    if ap_nf != 'D':
        write_mcf(obs_payroll, out_f)
        count_obs += 1
    return count_pops, count_obs


def mcf_for(geoid, yyyy, naics, est, emp, ap):
    """Return the populations and observations for est, employees and payroll."""
    geoid_for_name = str(geoid).replace('/', '_')
    id_list = [yyyy, geoid_for_name]
    if naics:
        id_list.append('naics')
        id_list.append(naics)
    pop_est_name = 'pop_' + '_'.join(id_list) + '_est'
    pop_est_list = [
        ('Node', pop_est_name),
        ('location', 'dcid:{}'.format(geoid)),
        # Population type is taken from cl/242025362
        ('populationType', 'dcs:USCEstablishment'),
        ('typeOf', 'dcs:StatisticalPopulation'),
    ]
    if naics:
        pop_est_list.append(('naics', 'dcs:NAICS/{}'.format(naics)))
    pop_est = collections.OrderedDict(pop_est_list)

    obs_est_name = 'obs_' + '_'.join(id_list) + '_est'

    # annual_payroll
    obs_ap_list = new_observation(name=obs_est_name + '_annual_payroll',
                                  observed_node_name=pop_est_name,
                                  observation_date=yyyy,
                                  measured_property='wagesAnnual',
                                  measured_value=ap,
                                  unit='USDollar')

    obs_ap = collections.OrderedDict(obs_ap_list)

    # Establishments
    obs_est_list = new_observation(name=obs_est_name + '_count',
                                   observed_node_name=pop_est_name,
                                   observation_date=yyyy,
                                   measured_property='Count',
                                   measured_value=est)

    obs_est = collections.OrderedDict(obs_est_list)

    # Employees
    pop_emp_name = 'pop_' + '_'.join(id_list) + '_emp'
    pop_emp_list = [
        ('Node', pop_emp_name),
        ('location', 'dcid:{}'.format(geoid)),
        ('populationType', 'dcs:USCWorker'),
        ('typeOf', 'dcs:StatisticalPopulation'),
    ]
    pop_emp = collections.OrderedDict(pop_emp_list)

    obs_emp_name = 'obs_' + '_'.join(id_list) + '_emp'

    obs_emp_list = new_observation(name=obs_emp_name + '_count',
                                   observed_node_name=pop_emp_name,
                                   observation_date=yyyy,
                                   measured_property='Count',
                                   measured_value=emp)

    obs_emp = collections.OrderedDict(obs_emp_list)

    return pop_est, obs_est, pop_emp, obs_emp, obs_ap
