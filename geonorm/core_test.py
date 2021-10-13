import time
import pathlib
from pandarallel import pandarallel
from datetime import datetime
import pandas as pd
import subprocess
import os


from geonorm.geonormaliser_utils import decompose, _measure_quality
from geonorm.geonormaliser import Geonormaliser
from geonorm.geomatch import Geomatch

CURRENT_DIR = str(pathlib.Path('../../').parent.resolve())
print(CURRENT_DIR)

pandarallel.initialize(progress_bar=False, nb_workers=os.cpu_count()-1)
matcher = None


def load_df(file_name, columns=None):
    compression = None
    if '.zip' in file_name:
        compression = 'zip'
    df = pd.read_csv(
        pathlib.Path(f'{CURRENT_DIR}/data/{file_name}'),
        compression=compression,
        sep=';',
        decimal='.',
        dtype={'n': int},
        keep_default_na=True,
        usecols=columns
    ).fillna('')

    return df


def save_scores(scores):
    pd.DataFrame(scores).to_csv(
        pathlib.Path(f'{CURRENT_DIR}/data/scores.csv'),
        sep=';',
        decimal='.',
        index=False
    )


def get_git_revision_hash():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode()


def run_measure(X, y):
    # преведем к единому регистру перед сравнением
    X = X.apply(lambda x: x.astype(str).str.lower().str.strip().str.replace('ё', 'е'))
    y = y.apply(lambda x: x.astype(str).str.lower().str.strip().str.replace('ё', 'е'))

    return _measure_quality(X, y, difference=True)


def decompose_expand(row):
    return decompose(row[0])


def match_expand(row):
    return matcher(row.to_dict())


def get_score_data(alg, res, start_time, config, row_count=0):
    out = {
        'date': datetime.now().strftime("%d.%m.%Y"),
        'method': alg,
        'version': get_git_revision_hash(),
        'test_set_file': config['test_set_file'],
        'standard_df_file': config['standard_df_file'],
        'lvl': len(config['columns']),
        'time_sec': round(time.time() - start_time, 3),
        'test_samples': row_count,
    }

    for score in res[0]:
        key = 'score_accuracy'
        if 'accuracy' not in score:
            key = f'{score}_accuracy'
        out[key] = round(res[0][score], 3)

    return out


def report_score(score):
    text = f'' \
           f'тест метода {score["method"]} \n' \
           f'версия: {score["version"]} \n' \
           f'тест сет: {score["test_set_file"]} \n' \
           f'эталон:   {score["standard_df_file"]} \n' \
           f'количество уровней: {score["lvl"]} \n' \
           f'количество строк: {score["test_samples"]} \n' \
           f'Время выполнения: {score["time_sec"]} \n' \
           f'качество: {score["score_accuracy"]}\n'

    return text


def output_error_to_csv(result, test_sample_df, file_name, config):
    errors_df = result[1]
    errors_df.columns = ['_'.join(col) for col in errors_df.columns]

    if config['full_address_column'] and config['full_address_column'] in test_sample_df.columns:
        errors_df = errors_df.join(test_sample_df[[config['full_address_column']]], how='left')

    errors_df.to_csv(
        pathlib.Path(f'log/{file_name.replace(".csv", "")}_acc-{round(result[0]["accuracy_score"], 3)}.csv'),
        sep=';', decimal='.'
    )


def run_decompose(X, y, config):
    start_time = time.time()

    X_dec = X[[config['full_address_column']]].parallel_apply(decompose_expand, axis=1, result_type="expand").fillna('')
    result = run_measure(X_dec, y[config['columns']])
    score = get_score_data('decompose', result, start_time, config, len(X))
    print(report_score(score))

    # output_error_to_csv(result, X,  f"de_{config['test_set_file']}", config)

    return X_dec, score


def run_match(X, y, standard_df, config):
    global matcher
    matcher = Geomatch(standard_df[config['columns']], config['columns'], skip_dead_end_fields=1)
    start_time = time.time()
    X_match = X.parallel_apply(match_expand, axis=1, result_type="expand").fillna('')
    result = run_measure(X_match, y[config['columns']])
    score = get_score_data('geomatch', result, start_time, config, len(X))
    print(report_score(score))

    # output_error_to_csv(result, X, f"ma_{config['test_set_file']}", config)

    return score


def run_geonorm(X, y, standard_df, config):
    global matcher
    matcher = Geonormaliser(standard_db=standard_df[config['columns']], use_speller=True, use_levenstein=True, match_columns=config['columns'])
    start_time = time.time()
    X_match = X.parallel_apply(match_expand, axis=1, result_type="expand")
    result = run_measure(X_match, y[config['columns']])
    score = get_score_data('geonorm', result, start_time, config, len(X))
    print(report_score(score))

    # output_error_to_csv(result, X, f"ge_{config['test_set_file']}", config)

    return score