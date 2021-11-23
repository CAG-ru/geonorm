# geonorm

Геонормализатор — это инструмент, который приводит адреса и топонимы к стандартному виду, пригодному для привязки к административным геоданным и другим датасетам из государственных информационных систем (ФИАС, Росстат и т.п.). 

Задача геонормализации решается следующим образом:
* Декомпозиция (разбивка) текстовой адресной строки методом *decompose*, то есть получение из адресной строки отдельных адресных элементов.
* Нормализация (привязка, мэтчинг) ранее декомпозированного адреса к эталону (эталонному датасету). Здесь возможно использование двух встроенных классов-мэтчеров.

## Установка

```shell
pip install git+https://github.com/CAG-ru/geonorm
```

загрузка эталонного датасета с data-in.ru в текущую директорию.
```shell
from geonormaliser_utils import get_standard
get_standard(fname='standard', path='./', replace=False)
```

загружаем эталон в переменную и фильтруем по интересуюшему региону(Челябинская Область), это позволит ускорить метчинг
```shell
standard_df = pd.read_csv('standard.zip', compression='zip', delimiter=';')
standard_df = standard_df[standard_df['region']=='Челябинская']
```

## Декомпозиция
Метод *decompose* применяется к текстовой адресной строке и возвращает словарь в котором адрес разбит поэлементно *[region, municipality, settlement, location, street, house]*.
Ключ *not_decompose* в результате указывает на нераспознанные фрагменты адресной строки.

```shell
from geonorm.geonormaliser_utils import decompose #Импорт метода

#Применение метода к строке
S = decompose('Челябинская Область, г. Челябинск, проспект Ленина') 

#Применение метода к серии
X_dec = X['address'].apply(decompose)

#X - pd.Series со строками вида 'обл. Иркутская, г. Братск, жилрайон. Гидростроитель, ул. Байкальская, д. 70'
#X_dec - набор словарей вида {'region': 'Иркутская', 'region_type': 'область', 'municipality': '', 'municipality_type': '',
#'settlement': 'Братск', 'settlement_type': 'город', 'street': 'Байкальская', 'street_type': 'улица', 'house': 'дом 70',
#'location': '', 'location_type': '', 'not_decompose': 'жилрайон. Гидростроитель'}
```

## Нормализация
Методы мэтчинга применяются к датафрейму или словарю с ранее декомпозированным адресом *[region, municipality, settlement, location, street, house]*. Пользователю доступны два независимых класса-мэтчера:
1. Geonormaliser - в основе композитный метод с использованием трех подходов: 
    * точное соответствие подстроки;
    * yandex-speller + точное соответствие, если не сработал первый метод;
    * FuzzyWuzy для случаев когда предыдущие методы не справились.
2. Geomatch - в основе посимвольный *tf-idf* и поиск ближайшего соседа по косинусному расстоянию.

Для нормализации требуется эталонный датасет определённой структуры (см. ниже, по умолчанию используется встроенный малый эталон).

### Импорт Geomatch
```shell
from geonorm.geomatch import Geomatch
#Инициализация мэтчера
matcher = Geomatch(standard_db=standard_df,
                  match_columns=['region', 'settlement', 'municipality'])
#Применение метода
X_norm = matcher(X_dec)
#X_norm - аналогичный датафрейм с нормализованными данными и дополнительной информацией
```

| | |
| ---------- | -- |
| Parameters | **standard_db : *pd.DataFrame()*** - эталонный датафрейм |
|            | **skip_dead_end_fields : *int, default 1*** - количество тупиковых адресных элементов поиска которые можно проигнорировать
|            | **match_columns : *list, default ['region', 'municipality', 'setlement']*** - адресные элементы поиска, порядок колонок имеет значение т.к. определяет порядок фильтрации множеств
| Methods    | **\_\_call\_\_()** |
|            | ***pd.DataFrame(), dict*** - в зависимости от типа переменной поступающей на вход возвращает либо датафрейм нормализованных адресов, либо нормализованный справочник |


### Импорт Geonormaliser
```shell
from geonorm.geonormaliser import Geonormaliser
#Инициализация мэтчера
matcher = Geonormaliser(standard_db=standard_df, 
                      use_speller=True,
                      use_levenstein=True,
                      match_columns=['region', 'settlement', 'municipality'])
                      #standard_db - эталон
                      #match_columns - адресные элементы поиска
                      #порядок колонок имеет значение т.к. определяет порядок фильтрации множеств
#Применение метода             
X_norm = matcher(X_dec)
#X - pd.DataFrame или набор словарей вида {'region': 'Иркутская', 'municipality': '', 'settlement': 'Братск'}
#X_norm - аналогичный датафрейм с нормализованными данными и дополнительной информацией
```

| | |
| ---------- | -- |
| Parameters | **standard_db : *pd.DataFrame()*** - эталонный датафрейм |
|            | **match_columns : *list, default ['region', 'municipality', 'setlement']*** - адресные элементы поиска, порядок колонок имеет значение т.к. определяет порядок фильтрации множеств |
|            | **use_speller: *bool, default True*** - использовать Яндекс Спеллер для поиска или нет |
|            | **use_levenstein: *bool, default True*** - использовать или нет расстояние Левенштейна |
|            | **levenshtein_threshold: *int, deafault 10*** - если похожесть найденного с помощью расстояния Левенштейна уровня адреса меньше, чем levenshtein_threshold, то найденный вариант отбрасывается |
| Methods    | **\_\_call\_\_()** |
|            | ***pd.DataFrame(), pd.Series, dict*** - в зависимости от типа переменной поступающей на вход возвращает либо датафрейм нормализованных адресов, либо нормализованный справочник |


### Возможности параллелизации
Возможен вариант использования библиотеки pandarallel на этапе распараллеливания метода apply.
```shell
from geonorm.geomatch import Geomatch
from geonorm.geonormaliser_utils import decompose
from pandarallel import pandarallel #Инициализация библиотеки
pandarallel.initialize(progress_bar=False, nb_workers=os.cpu_count())

def decompose_expand(row): #Декомпозиция адресной строки
    return decompose(row[0])

X_dec = X[['address']].parallel_apply(decompose_expand, axis=1, result_type="expand").fillna('')

def match_expand(row): #Мэтчинг
    return matcher(row)
    
matcher = Geomatch(standard_db=standard_df, match_columns=['region', 'settlement', 'municipality'])
X_norm = X.parallel_apply(match_expand, axis=1, result_type="expand").fillna('')
```

## Тестирование 

Для оценки работы были подготовлены тест-сеты, размещенные в папке `data`.
Пользователь может самостоятельно протестировать инструмент. Для этого можно запустить `run_tests.py`, используя следующую команду:

```shell
python run_tests.py
```

### Тесты декомпозиции
| Тестируемый метод | Тестовый датасет | Время выполнения, с | Качество* |
| :---------------: | :--------------: | :-----------------: | :-------: |
| decompose, 5 уровней | test_lvl6.csv | 105.4 | 0.738 |

\* Метрика качества - общая точность, считается, как доля строк полностью совпавших с тестовым датафреймом. Зависит от числа атрибутов, включаемых в сравнение.

### Тесты нормализации
| Метод, тестовый датасет | Эталонный датасет | Время выполнения, с | Качество* |
| :---------------------: | :---------------: | :-----------------: | :-------: |
| Geomatch, test_lvl3.csv, 3 уровня  | 14/10/2021 | 44.8 | 0.927 |
| Geonorm, test_lvl3.csv, 3 уровня   | 14/10/2021 | 304.5 | 0.895 |
| Geomatch, test_lvl6.csv, 5 уровней | 14/10/2021 | 326.6 | 0.810 |
| Geonorm, test_lvl6.csv, 5 уровня   | 14/10/2021 | 666.4 | 0.805 |

\* Метрика качества - общая точность, считается, как доля строк полностью совпавших с тестовым датафреймом. Зависит от числа атрибутов, включаемых в сравнение.

## Контакты разработчиков

[Центр перспективных управленческих решений](https://cpur.ru/), проект [«Инфраструктура научно-исследовательских данных»](https://data-in.ru/)

* Николай Давыдов, [n.davydov@data-in.ru]
* Максим Веденьков, [m.vedenkov@data-in.ru]
* Константин Глонин, [k.glonin@data-in.ru]
* Данила Валько, [d.valko@data-in.ru]
