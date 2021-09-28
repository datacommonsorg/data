def get_mcf(series_lst):
    '''
    gets mcf by splitting description and using fstrings
    '''
    nodes = []
    #don't  use df; automate
    with open("output\World_bank_hnp_population.mcf", 'w', encoding = 'utf-8') as file:
        print(end = '')
        mcf = ''
        for current_series in series_lst:
            print('\n'+current_series)
            statvars = ['Node', 'typeOf', 'description', 'populationType',
                      'measuredProperty', 'gender', 'statType', 'age']
            node, age, gender = '', '', ''
            age = current_series[9:11]
            gender = ''
            if 'MA' in current_series:
                gender = 'Male'
            else:
                gender = 'Female'
            node = f'Count_Persons_{(int(age))}Years_{gender}'
            desc = f'Age population, age {age}, {gender.lower()}, interpolated'
            nodes.append(node)
            values = [node, 'dcs:StatisticalVariable', f'"{desc}"',
                    'dcs:Person', 'dcs:count', f'dcs:{gender}',
                    'dcs:measuredValue', f'[Years {age}]']
            req_len = len(statvars)
            for i in range(req_len):
                mcf = mcf + f'{statvars[i]}: {values[i]}\n'
            mcf = mcf + '\n'

        file.write(mcf)
series  = [f"SP.POP.AG{age:02d}.{gender}.IN" for age in range(AGES)
           for gender in ['FE', 'MA']]
get_mcf(series)
