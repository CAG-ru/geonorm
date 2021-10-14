from geonorm.core_test import *
from geonorm.geonormaliser_utils import get_standard

configs = [
    {
        'test_set_file': 'test_lvl6.csv',
        'source': [1, 2],
        'full_address_column': 'address',
        'standard_df_file': 'standard.zip',
        'columns': ['region', 'municipality', 'settlement', 'location', 'street']
    },
    {
        'test_set_file': 'test_lvl3.csv',
        'source': [3],
        'full_address_column': 'address',
        'standard_df_file': 'standard.zip',
        'rename': {'subject_name': 'sub', 'region_name': 'district', 'settlement_name': 'settlement'},
        'columns': ['region', 'municipality', 'settlement'],
        'skip_decompose': True
    }, 
    {
        'test_set_file': 'test_lvl6.csv',
        'source': [1],
        'full_address_column': 'address',
        'standard_df_file': 'standard.zip',
        'columns': ['region', 'municipality', 'settlement', 'location', 'street']
    },
    {
        'test_set_file': 'test_lvl6.csv',
        'source': [2],
        'full_address_column': 'address',
        'standard_df_file': 'standard.zip',
        'columns': ['region', 'municipality', 'settlement', 'location', 'street']
    },

]

get_standard('standard', '../data/', replace=False)
prev_standard_df_file = None
scores = []
for config in configs:
    test_set = load_df(config['test_set_file'])
    test_sample = None
    if 'source' in config:
        for i in config['source']:
            test_sample = pd.concat([test_sample, test_set[test_set['source'] == i]])
    else:
        test_sample = test_set.reset_index(drop=True)

    if prev_standard_df_file != config['standard_df_file']:
        standard_df = load_df(config['standard_df_file']).drop_duplicates()
        prev_standard_df_file = config['standard_df_file']

    if 'std_filter' in config and len(config['std_filter']) > 0:
        for std_filter in config['std_filter']:
            if std_filter['col'] in standard_df.columns:
                if std_filter['eq']:
                    standard_df = standard_df[standard_df[std_filter['col']] == std_filter['val']]
                else:
                    standard_df = standard_df[standard_df[std_filter['col']] != std_filter['val']]
                prev_standard_df_file = None

    # отфильтруем отсутствующие в эталоне строки
    if 'in_standard' in test_sample:
        test_sample = test_sample[test_sample['in_standard'] == 1]
    
    # отфильтруем странные адреса
    if 'wierd' in test_sample:
        test_sample = test_sample[test_sample['wierd'] != 1]

    # отфильтруем мертвые поселения
    if 'is_dead' in test_sample:
        test_sample = test_sample[test_sample['is_dead'] != 1]

    X = test_sample
    if 'rename' in config:
        X = X[config['rename'].keys()].rename(config['rename'], axis=1)
    
    y = test_sample[config['columns']]

    if 'skip_decompose' in config and config['skip_decompose']:
        X_dec = X
    else:
        X_dec, score = run_decompose(X, y, config)
        X_dec[config['full_address_column']] = X[config['full_address_column']]
        scores.append(score)

    scores.append(run_match(X_dec, y, standard_df, config))
    scores.append(run_geonorm(X_dec, y, standard_df, config))

# save_scores(scores)