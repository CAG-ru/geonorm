import pandas as pd
import pathlib
from .geonormaliser_utils import search_reference_address,\
                                 get_pull_methods, get_address_by_level,\
                                 get_optional_parametres, valid_result,\
                                 load_standard




class Geonormaliser:
    def __init__(self,
                 standard_db=False,
                 # порядок столбцов имеет значение т.к. определяет порядок фильтрации множеств
                 match_columns=['region', 'settlement', 'municipality'],
                 use_speller=True,
                 use_levenstein=False,
                 levenshtein_threshold=10
                 ):
        self.current_directory = str(pathlib.Path(__file__).parent.resolve())
        self.standard = load_standard(standard_db, self.current_directory)
        self.match_columns = match_columns
        self.levenshtein_threshold = levenshtein_threshold
        self.pull_methods = get_pull_methods(use_speller, use_levenstein)



    def _process_address(self, input_data):
        '''
            Функция нормализаует один адрес.
            Принимает на вход pd.Series, str или dict.
            Приводит к стандартизированной схеме dict.
            Генерирует параметры поиска.
            Получает результат поиска, валидирует его, отдает родительской функции. 
        '''
        address_by_level = get_address_by_level(input_data, self.match_columns)
        optional = get_optional_parametres(input_data, self.levenshtein_threshold)
        address_normalize, address_normalize_status = search_reference_address(
                                                            address_by_level, 
                                                            self.standard, 
                                                            self.pull_methods, 
                                                            optional)
        result = valid_result(address_normalize, address_normalize_status, self.standard)
        return result

    
    def _process_df(self, df):
        '''
            Функция запускает итерацию по dataframe.
            Принимает на вход dataframe, запускает итерацию через apply.
            Сортирует колонки полученного ответа и возвращает новый dataframe.
        '''
        result = df.apply(self._process_address, axis=1, result_type="expand")
        result_columns = result.columns.tolist()
        standard_columns = self.standard.columns.tolist()
        status_columns = list(set(result_columns) - set(standard_columns))
        standard_columns.extend(status_columns)
        result = result.reindex(columns=standard_columns)
        return result
    
    
    def _process_series(self, df_series):
        '''
            Функция запускает итерацию по pd.Series.
            Принимает на вход pd.Series, запускает итерацию через apply.
            Возвращает финальный результат.
        '''
        return pd.DataFrame(df_series.apply(self._process_address).values.tolist())
        
    
    def __call__(self, input_data):
        if isinstance(input_data, pd.DataFrame):
            return self._process_df(input_data)
        elif isinstance(input_data, pd.Series):
            return self._process_series(input_data)
        else:
            return self._process_address(input_data)