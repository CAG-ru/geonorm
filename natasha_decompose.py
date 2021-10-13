from natasha import (
    MorphVocab,
)

from .nat_new import (
    AddrExtractorConfig
)

import json
from yargy.tokenizer import MorphTokenizer

# добавлено чтобы корректно отрабатывала подгрузка конфига из директории с библиотекой
import pathlib

CURRENT_DIRECTORY = str(pathlib.Path(__file__).parent.resolve())

tokenizer = MorphTokenizer()

# todo: сделать единый класс с конфигами для библиотеки
with open(pathlib.Path(f'{CURRENT_DIRECTORY}/config.json'), 'r', encoding="utf-8") as fp:
    config = json.loads(fp.read().lower())


def prepare_address(item):
    house_title = [' д.', ',д.', ' д', ',д', ' Д', ',Д']
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    for house_item in house_title:
        if house_item in item and 'дом' not in item:

            ind0 = item.index(house_item)
            i = ind0 + len(house_item)
            is_next_number = False
            while len(item) > i and not is_next_number:

                if item[i] != ' ' and item[i] != '.':

                    if item[i] in digits:
                        is_next_number = True
                        break
                    else:
                        break
                i += 1

            if is_next_number:
                item = item[:ind0] + " дом " + item[ind0 + len(house_item):]
                break

    house_item = "корп"
    if 'корпус' not in item and house_item in item and item.index(house_item) > len(item) - 15:
        item = item.replace(house_item, ' корп ')

    house_items = ["р-н", 'район м.район.']
    for house_item in house_items:
        item = item.replace(house_item, 'район')

    house_no_num = ['б/н', 'Б/Н', ' бн ', 'б\\н', 'б/Н']
    for house_item in house_no_num:
        if house_item in item and item.index(house_item) > len(item) - 4:
            item = item.replace(house_item, ' 100001')

    item = item.replace(' и(при) ', ' ')
    item = item.replace('станция(и)', 'станция')
    item = item.replace('с н.п.', 'село')
    item = item.replace('г г.п.', 'г.')
    item = item.replace('пгт н.п.', 'пгт')
    item = item.replace('с/с', 'сельсовет')
    item = item.replace(' рп ', ' рабочий поселок ')
    item = item.replace(' ст ', ' станция ')
    item = item.replace(' здание ', ' дом ')
    item = item.replace(' тер ', ' территория ')
    item = item.replace(' тер. ', ' территория ')
    item = item.replace(' нп ', ' поселок ')
    item = item.replace(' нп. ', ' поселок ')
    item = item.replace(' посёлок ', ' поселок ')
    item = item.replace('район улицы', ' улица ')
    item = item.replace('район здания', ' здание ')

    return item


# костыль для городов федерального значения
def federal_city_fix(data, clear_settlement=True):
    if ('settlement' in data and
            data['settlement'].lower() in config['federal_city']):
        data['region'] = data["settlement"]
        data['region_type'] = data["settlement_type"]

        if clear_settlement:
            data['settlement'] = ''
            data['settlement_type'] = ''

    return data


def decompose(item, hide_empty=False):
    item = prepare_address(item)
    markup = list(address_extractor(item))

    house = ''
    obj = {}
    offset = 0
    not_decompose = item

    for field in config['rule']:
        obj[f'{field}'] = ''
        obj[f'{field}_type'] = ''

    for mark_item in markup:
        # распределение полей по справочнику

        for field in set(config['rule']):
            if mark_item.fact.type in config['rule'][field]:

                # для деревни внутри города.
                # если поле settlement уже заполнено, то переносим его в municipality, и пишем текущее в settlement
                if field == "settlement" and \
                        obj[field] != '' and \
                        obj['municipality'] == '':  # and obj['municipality'] != '':
                    obj['municipality'] = obj['settlement']
                    obj['municipality_type'] = obj['settlement_type']

                obj[f'{field}'] = mark_item.fact.value
                obj[f'{field}_type'] = mark_item.fact.type

                # фикс для городов федерального значения
                obj = federal_city_fix(obj)

                # обработка not decompose
                not_decompose = not_decompose[:mark_item.start - offset] + not_decompose[mark_item.stop - offset:]
                offset += mark_item.stop - mark_item.start

        # здесь немного кастомной обработки для домов
        for h_item in set(config['rule']['house']):
            if mark_item.fact.type == h_item:
                str_item = item[mark_item.start:mark_item.stop]
                str_item = str_item.replace(h_item, '')
                str_item = str_item.strip()
                if str_item == "100001":
                    str_item = "без номера"
                house += " " + h_item + " " + str_item

    # исправление для случаев когда поселение и регион идентичны
    if {'settlement', 'municipality'}.issubset(set(obj.keys())) and obj['settlement'] == obj['municipality']:
        obj['municipality'] = ''
        obj['municipality_type'] = ''

    if 'house_type' in obj:
        obj.pop('house_type')

    if house:
        obj['house'] = house.strip()

    if hide_empty:
        obj = {i: obj[i] for i in obj if obj[i]}

    obj['not_decompose'] = not_decompose.replace(',', '').strip()

    return obj


def get_tokens(from_string):
    # sign_words = ['район','город','село','деревня']
    sign_words = ['село', 'деревня']
    tokens = list(tokenizer(from_string))

    is_prts = False

    tmp_tokens = []
    for token in tokens:
        if token.type == "RU":
            try:
                a = token.forms[0].grams.values.copy()
                for x in a:
                    if x.isupper() and token.value not in sign_words:
                        tmp_tokens.append(x)
                        if x == "PRTS":
                            is_prts = True
                            # print(token,str)

            except:
                print("ERR", token)
        else:
            if token.type == "PUNCT":
                tmp_tokens.append(token.value)
            else:
                tmp_tokens.append(token.type)

    return tmp_tokens


morph_vocab = MorphVocab()
address_extractor = AddrExtractorConfig(morph_vocab, config['extractor_rule'])
