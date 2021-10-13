import pathlib
import numpy as np
import pandas as pd
from thefuzz import process
import re
import requests
from sklearn.metrics import accuracy_score
from .natasha_decompose import decompose
from .text_utils import remove_descriptors
import os


def download_standard(save_as='./standard.zip',
                      url='https://ds1.data-in.ru/Rosgidromet/Zagryaznenie_poverkhnostnih_vod_RF_176/Zagryaznenie_poverkhnostnih_vod_RF_176_23.09.21.zip?',
                      replace=False
                      ):
    """
    Загрузка актуального эталона в текущую директорию
    :param save_as: str
    :param url: str
    :param replace: bool
    :return: str
    """
    if os.path.isfile(save_as) and replace:
        os.remove(save_as)
    if not os.path.isfile(save_as):
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            with open(save_as, 'wb') as f:
                f.write(response.content)
            return str(pathlib.Path(f'{save_as}'))
        else:
            return False
    else:
        return save_as


'''
    Функции создания параметров поиска.
'''        
def load_standard(standard_db=None, current_directory='./'):
    if type(standard_db) is pd.core.frame.DataFrame:
        standard = standard_db.reset_index()
    elif type(standard_db) is str:
        standard = pd.read_csv(pathlib.Path(f'{current_directory}/{standard_db}'), compression='zip', delimiter=';')
    else:
        standard = pd.read_csv(pathlib.Path(f'{current_directory}/standard.zip'), compression='zip', delimiter=';')
    return standard


def get_address_by_level(input_data, match_columns):
    if isinstance(input_data, pd.Series):
        address_by_level = {}
        for field, level in input_data.items():
            if field in match_columns:
                address_by_level[field] = level
    elif isinstance(input_data, str):
        address_by_level = {}
        decompose_address = decompose(input_data)
        for field, level in decompose_address.items():
            if field in match_columns:
                address_by_level[field] = level
    else:
        address_by_level = {}
        for field, level in input_data.items():
            if field in match_columns:
                address_by_level[field] = level        
    return address_by_level


def get_pull_methods(use_speller, use_levenstein):
    pull_methods = [preprocessor, direct_method, speller_direct_method, speller_levenstein_direct_method]
    if not use_levenstein:
        pull_methods.remove(speller_levenstein_direct_method)
    if not use_speller:
        pull_methods.remove(speller_direct_method)
    return pull_methods


def get_optional_parametres(input_data, levenshtein_threshold):
    optional = {}
    optional['levenshtein_threshold'] = levenshtein_threshold
    if isinstance(input_data, str):
        optional['row_for_speller'] = input_data
    if isinstance(input_data, pd.Series):
        optional['use_remove_descriptors'] = True
    return optional


def valid_result(address_normalize, address_normalize_status, standard):
    if len(address_normalize) == 1:
        result = dict(address_normalize.to_dict('records')[0], **address_normalize_status)
    elif len(address_normalize) > 1:
        last_level_status = list(address_normalize_status.keys())[-1]
        if last_level_status != 'empty':
            address_normalize_status[last_level_status] = 'duplicates'
        result = dict(address_normalize.to_dict('records')[0], **address_normalize_status)
    else:
        result = dict({i: '' for i in standard.columns}, **address_normalize_status)
    return result



'''
    Функции методов
'''

def direct(key, level, standard):
    try:
        result = standard.query(f'{key} == "{level}"')
    except:
        level_correct = re.sub('"', '', level).strip()
        result = standard.query(f'{key} == "{level_correct}"')
    finally:
        return result


def speller(level, optional=None):
    warning_limit_text = 'Закончился лимит подключения, используется оригинальная строка'
    url = 'https://speller.yandex.net/services/spellservice.json/checkText?text={}'
    if 'row_for_speller' in optional:
        row = optional['row_for_speller']
        level_split = re.split('-| ', level)
        try:
            speller_response = requests.get(url.format(row)).json()
            for word in level_split:
                for hint in speller_response:
                    if word == hint['word']:
                        level = re.sub(word, hint['s'][0], level)
        except:
            print(warning_limit_text)
        finally:
            return level
    else:
        substring = level + ', улица'
        level_split = re.split('-| ', level)
        try:
            speller_response = requests.get(url.format(substring)).json()
            for word in level_split:
                for hint in speller_response:
                    if word == hint['word']:
                        level = re.sub(word, hint['s'][0], level)
        except:
            print(warning_limit_text)
        finally:
            return level


def levenstein(key, level, standard):
    level_list = standard[key].unique()
    level_levenstein_variant, rate = process.extractOne(level, level_list)
    return level_levenstein_variant, rate



'''
    Методы поиска
'''

def preprocessor(key, level, standard, optional=None):
    if level == '' or level == np.nan or level == None:
        status = 'empty'
    else:
        status = 'check_empty_passed'
    return standard, status


def direct_method(key, level, standard, optional=None):
    result = direct(key, level, standard)
    if result.shape[0] == 0:
        status = 'not_found'
        return standard, status
    else:
        status = 'direct'
        return result, status

    
def speller_direct_method(key, level, standard, optional=None):
    if 'use_remove_descriptors' in optional:
        level = remove_descriptors(key, level)
    level_name_speller = speller(level, optional)
    result = direct(key, level_name_speller, standard)
    if result.shape[0] == 0:
        status = 'not_found'
        return standard, status
    else:
        status = 'speller'
        return result, status

    
def speller_levenstein_direct_method(key, level, standard, optional=None):
    levenshtein_threshold = optional['levenshtein_threshold']
    if 'use_remove_descriptors' in optional:
        level = remove_descriptors(key, level)
    level_name_speller = speller(level, optional)
    level_name_levenstein, rate = levenstein(key, level_name_speller, standard)
    if rate >= levenshtein_threshold:
        result = direct(key, level_name_levenstein, standard)
        status = rate
        return result, status
    else:
        status = 'threshold'
        return standard, status



def search_reference_address(address_by_level, standard, pull_methods, optional):
    '''
        Функция ищет эталон по уровням входящего адреса.
        Принимает dict, возвращает срез эталона и словарь со статусами.
    '''
    address_by_level_status = {}
    for key, level in address_by_level.items():
        for method in pull_methods:
            result, status = method(key, level, standard, optional)
            if status in ['not_found','check_empty_passed']:
                continue
            else:
                address_by_level_status[key + '_status'] = status
                standard = result
                break
    return result, address_by_level_status
  


def _measure_quality(X, y, difference=False, columns=False):
    '''
        Проверяет датафрейм X на точное соответствие датафрейму y по списку колонок columns.
        Возвращает sklearn.accuracy_score словарем {'sub': 0.87, 'district': 0.94, ... }.
        Ключ accuracy_score в словаре указывает на долю полностью совпавших строк в датафреймах.
        Для difference = True доп-о возвращает не совпавшие строки методом pd.compare().
        В колонке valid содержимое y, в колонке actual — X.
    '''
    assert X.shape[0] == y.shape[0], 'Количество объектов в датафреймах различается'
    if not columns:
        columns = y.columns
    out = {}
    for c in columns:
        if c in X.columns:
            out.update({c: accuracy_score(y[c], X[c])})

    diff = y[columns].compare(X[columns], keep_equal=False, keep_shape=False)
    out.update({'accuracy_score': 1 - len(diff) / len(y)})

    if difference == False:
        return out
    else:
        return out, diff.rename(columns={'self': 'valid', 'other': 'actual'}, level=-1)
