def get_mcf(series_lst):
    '''
    gets mcf by splitting description and using fstrings
    '''
    nodes = []
    with open("World_bank_hnp_population.mcf", 'w', encoding = 'utf-8') as file:
        mcf = ''
        for current_series in series_lst:
            print('\n'+current_series)
            node, age, gender = '', '', ''
            age = current_series[9:11]
            gender = ''
            if 'MA' in current_series:
                gender = 'Male'
            else:
                gender = 'Female'
            property_dict = {'typeOf': 'dcs:StatisticalVariable',
                     'description': f'Age population, {gender}, Age {age}, interpolated',
                     'populationType': 'dcs:Person', 'measuredProperty':
                     'dcs:count','gender': 'dcs:{gender}',
                     'statType': 'dcs:measuredValue', 'age': '[Years {age}]'}
            node = get_statvars(gender, age)
            desc = f'Age population, age {age}, {gender.lower()}, interpolated'
            nodes.append(node)
            property_dict['node'] = node
            
            for i in range(len(poperty_dict.keys())):
                mcf = mcf + f'{property_dict.keys[i]}:'
                + ' {property_dict[property_dict.keys()[i]}\n'
        file.write(mcf)

series  = [f"SP.POP.AG{age:02d}.{gender}.IN" for age in range(AGES)
           for gender in ['FE', 'MA']]
get_mcf(series)
