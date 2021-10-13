import json
import re
import pathlib


with open(str(pathlib.Path(__file__).parent.resolve()) + '/descriptors_config.json', 'r', encoding='utf-8') as fp:
    descriptors_to_remove = json.load(fp).get('descriptors_to_remove')


def remove_descriptors(key, level):
    if key in descriptors_to_remove:
        for descriptor in descriptors_to_remove[key]:
            level = level.replace('.', ' ')
            level = re.sub(r'(^|[^\w])' + descriptor + r'([^\w]|$)', r'\1' + '' + r'\2', level)
            level = level.strip()
    return level

