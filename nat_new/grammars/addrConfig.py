from yargy import (
    rule,
    or_, and_
)
from yargy.interpretation import fact
from yargy.predicates import (
    eq, lte, gte, gram, type, tag,
    length_eq,
    in_, in_caseless, dictionary,
    normalized, caseless,
    is_title
)
from yargy.pipelines import morph_pipeline
from yargy.tokenizer import QUOTES

Index = fact(
    'Index',
    ['value']
)
Country = fact(
    'Country',
    ['name']
)
Region = fact(
    'Region',
    ['name', 'type']
)
Settlement = fact(
    'Settlement',
    ['name', 'type']
)
Street = fact(
    'Street',
    ['name', 'type']
)
Building = fact(
    'Building',
    ['number', 'type']
)
Room = fact(
    'Room',
    ['number', 'type']
)
AddrPart = fact(
    'AddrPart',
    ['value']
)


def value(key):
    @property
    def field(self):
        return getattr(self, key)
    return field


class Index(Index):
    type = 'индекс'


class Country(Country):
    type = 'страна'
    value = value('name')


class Region(Region):
    value = value('name')


class Settlement(Settlement):
    value = value('name')


class Street(Settlement):
    value = value('name')


class Building(Building):
    value = value('number')


class Room(Room):
    value = value('number')

class AddrPart(AddrPart):
    @property
    def obj(self):
        from natasha.obj import AddrPart
        part = self.value

        return AddrPart(part.value, part.type)


DASH = eq('-')
DOT = eq('.')

ADJS = gram('ADJS')
GRND = gram('GRND')
ADVB = gram('ADVB')
ADJF = gram('ADJF')
NOUN = gram('NOUN')
VERB = gram('VERB')
UNKN = gram('UNKN')
INT = type('INT')
TITLE = is_title()


ANUM = rule(
    INT,
    DASH.optional(),
    in_caseless({
        'я', 'й', 'е',
        'ое', 'ая', 'ий', 'ой'
    })
)


#########
#
#  STRANA
#
##########


# TODO
COUNTRY_VALUE = dictionary({
    'россия',
    'украина'
})

ABBR_COUNTRY_VALUE = in_caseless({
    'рф'
})

COUNTRY = or_(
    COUNTRY_VALUE,
    ABBR_COUNTRY_VALUE
).interpretation(
    Country.name
).interpretation(
    Country
)


#############
#
#  FED OKRUGA
#
############

def get_fed(cfg):

    FED_OKRUG_NAME = or_(
        rule(
            dictionary({
                'дальневосточный',
                'приволжский',
                'сибирский',
                'уральский',
                'центральный',
                'южный',
            })
        ),
        rule(
            caseless('северо'),
            DASH.optional(),
            dictionary({
                'западный',
                'кавказский'
            })
        )
    ).interpretation(
        Region.name
    )

    fed_items = or_(
        rule(
            normalized('федеральный'),
            normalized('округ')
        ),
        rule(caseless('фо'))
    )

    for item in cfg:
        fed_items.children.append(rule(caseless(item)))

    FED_OKRUG_WORDS = fed_items.interpretation(
        Region.type.const('федеральный округ')
    )

    FED_OKRUG = or_(rule(
        FED_OKRUG_WORDS,
        FED_OKRUG_NAME),
        rule(
            FED_OKRUG_NAME ,FED_OKRUG_WORDS),

    ).interpretation(
        Region
    )

    return  FED_OKRUG


#########
#
#   RESPUBLIKA
#
############

def get_resp(cfg):


    resp_items = or_(
        rule(caseless('респ'), DOT.optional()),
        rule(normalized('республика'))
    )

    for item in cfg:
        resp_items.children.append(rule(caseless(item)))

    RESPUBLIKA_WORDS = resp_items.interpretation(
        Region.type.const('республика')
    )

    RESPUBLIKA_ADJF = or_(
        rule(
            dictionary({
                'удмуртский',
                'чеченский',
                'чувашский',
            })
        ),
        rule(
            caseless('карачаево'),
            DASH.optional(),
            normalized('черкесский')
        ),
        rule(
            caseless('кабардино'),
            DASH.optional(),
            normalized('балкарский')
        )
    ).interpretation(
        Region.name
    )

    RESPUBLIKA_NAME = or_(
        rule(
            dictionary({
                'адыгея',
                'алтай',
                'башкортостан',
                'бурятия',
                'дагестан',
                'ингушетия',
                'калмыкия',
                'карелия',
                'коми',
                'крым',
                'мордовия',
                'татарстан',
                'тыва',
                'удмуртия',
                'удмуртская',
                'карачаево-черкесская',
                'кабардино-балкарская',
                'чеченская',
                'хакасия',
                'саха',
                'якутия',
                'чувашия'
            })
        ),
        rule(
            caseless('саха'), eq('('), caseless('якутия'), eq(')')  # Саха (Якутия) республика
        ),
        rule(caseless('марий'), caseless('эл')),
        rule(
            normalized('северный'), normalized('осетия'),
            rule('-', normalized('алания')).optional()
        )
    ).interpretation(
        Region.name
    )

    RESPUBLIKA_ABBR = in_caseless({
        'кбр',
        'кчр',
        'рт',  # Татарстан
    }).interpretation(
        Region.name  # TODO type
    )

    RESPUBLIKA = or_(
        rule(
            RESPUBLIKA_WORDS.optional(),
            RESPUBLIKA_ADJF,
            RESPUBLIKA_WORDS.optional()
        ),
        rule(
            RESPUBLIKA_WORDS.optional(),
            RESPUBLIKA_NAME,
            RESPUBLIKA_WORDS.optional()
        ),  # Саха (Якутия) республика
        rule(RESPUBLIKA_ABBR)
    ).interpretation(
        Region
    )

    return RESPUBLIKA


##########
#
#   KRAI
#
########

def get_krai(cfg):

    krai_items = or_(
        rule(normalized('край'))

    )

    for item in cfg:
        krai_items.children.append(rule(caseless(item)))

    KRAI_WORDS = krai_items.interpretation(
        Region.type.const('край')
    )

    KRAI_NAME = dictionary({
        'алтайский',
        'забайкальский',
        'камчатский',
        'краснодарский',
        'красноярский',
        'пермский',
        'приморский',
        'ставропольский',
        'хабаровский',
    }).interpretation(
        Region.name
    )

    KRAI = or_(
        rule(KRAI_NAME, KRAI_WORDS),
        rule(KRAI_WORDS, KRAI_NAME)
    ).interpretation(
        Region
    )

    return KRAI


############
#
#    OBLAST
#
############
def get_oblast(cfg):


    obl_items = or_(
        rule(normalized('область')),
        rule(
            caseless('обл'),
            DOT.optional()
        )
    )

    for item in cfg:
        obl_items.children.append(rule(caseless(item)))

    OBLAST_WORDS = obl_items.interpretation(
        Region.type.const('область')
    )

    OBLAST_NAME = dictionary({
        'амурский',
        'архангельский',
        'астраханский',
        'белгородский',
        'брянский',
        'владимирский',
        'волгоградский',
        'вологодский',
        'воронежский',
        'горьковский',
        'ивановский',
        'ивановский',
        'иркутский',
        'калининградский',
        'калужский',
        'камчатский',
        'кемеровский',
        'кировский',
        'костромской',
        'курганский',
        'курский',
        'ленинградский',
        'липецкий',
        'магаданский',
        'московский',
        'мурманский',
        'нижегородский',
        'новгородский',
        'новосибирский',
        'омский',
        'оренбургский',
        'орловский',
        'пензенский',
        'пермский',
        'псковский',
        'ростовский',
        'рязанский',
        'самарский',
        'саратовский',
        'сахалинский',
        'свердловский',
        'смоленский',
        'тамбовский',
        'тверской',
        'томский',
        'тульский',
        'тюменский',
        'ульяновский',
        'челябинский',
        'читинский',
        'ярославский',
    }).interpretation(
        Region.name
    )

    OBLAST = or_(rule(
        OBLAST_NAME,
        OBLAST_WORDS),
        rule(
            OBLAST_WORDS,
            OBLAST_NAME)
    ).interpretation(
        Region
    )

    return OBLAST


##########
#
#    AUTO OKRUG
#
#############


AUTO_OKRUG_NAME = or_(
    rule(
        dictionary({
            'чукотский',
            'эвенкийский',
            'корякский',
            'ненецкий',
            'таймырский',
            'агинский',
            'бурятский',
            'еврейский'
        })
    ),
    rule(caseless('коми'), '-', normalized('пермяцкий')),
    rule(caseless('долгано'), '-', normalized('ненецкий')),
    rule(caseless('ямало'), '-', normalized('ненецкий')),
).interpretation(
    Region.name
)

AUTO_OKRUG_WORDS = or_(
    rule(
        normalized('автономный'),
        normalized('округ')
    ),
    rule(caseless('ао'))
).interpretation(
    Region.type.const('автономный округ')
)


AUTO_OBLAST_WORDS = or_(
    rule(
        normalized('автономный'),
        normalized('область')
    ),  # Еврейская автономная область
    rule(caseless('ао'))
).interpretation(
    Region.type.const('автономная область')
)


HANTI = rule(
    caseless('ханты'), '-', normalized('мансийский')
).interpretation(
    Region.name
)

BURAT = rule(
    caseless('усть'), '-', normalized('ордынский'),
    normalized('бурятский')
).interpretation(
    Region.name
)
AUTO_OBLAST_WORDS
AUTO_OKRUG = or_(
    rule(
        AUTO_OKRUG_WORDS.optional(),
        AUTO_OKRUG_NAME,
        AUTO_OKRUG_WORDS.optional()
    ),  # дополнил правило для распосзнования автономный округ Ямало-Ненецкий
    rule(
        AUTO_OBLAST_WORDS.optional(),
        AUTO_OKRUG_NAME,
        AUTO_OBLAST_WORDS.optional()
    ),  # дополнил правило для распосзнования Еврейская автономная область
    or_(
        rule(
            HANTI,
            AUTO_OKRUG_WORDS,
            '-', normalized('югра')
        ),
        rule(
            caseless('хмао'),
        ).interpretation(Region.name),
        rule(
            caseless('хмао'),
            '-', caseless('югра')
        ).interpretation(Region.name),
    ),
    rule(
        BURAT,
        AUTO_OKRUG_WORDS
    )
).interpretation(
    Region
)


##########
#
#  RAION
#
###########


def get_raion(cfg):

    raion_items_morph = morph_pipeline([
        'жилой район',
    ])

    raion_items = or_(
        rule(raion_items_morph),
        rule(caseless('р'), '-', in_caseless({'он', 'н'})),
        rule(caseless('район')),
        rule(caseless('м.район.')),
        rule(caseless('м. район.'))
    )

    for item in cfg:
        raion_items.children.append(rule(caseless(item)))

    RAION_WORDS = raion_items.interpretation(
        Region.type.const('район')
    )

    RAION_SIMPLE_NAME = and_(
        ADJF,
        TITLE,
    )

    RAION_MODIFIERS = rule(
        in_caseless({
            'усть',
            'северо',
            'александрово',
            'гаврилово',
        }),
        DASH.optional(),
        TITLE
    )

    RAION_COMPLEX_NAME = rule(
        RAION_MODIFIERS,
        RAION_SIMPLE_NAME,
    )

    RAION_NAME = or_(
        rule(NOUN, NOUN.optional()),
        rule(NOUN, NOUN, NOUN.optional()),
        rule(ADJF, NOUN, DASH, ADJF),
        rule(NOUN, DASH, ADJF),
        rule(NOUN, DASH, NOUN),
        rule(UNKN, DASH, ADJF),
        rule(ADJS, DASH, ADJF),
        rule(ADJF, DASH, ADJF),
        rule(ADVB, DASH, ADJF),

        rule(ADJF ,ADJF),
        rule(RAION_SIMPLE_NAME),
        rule(RAION_SIMPLE_NAME ,'-' ,RAION_SIMPLE_NAME),
        RAION_COMPLEX_NAME
    ).interpretation(
        Region.name
    )

    RAION = or_(
        rule( RAION_WORDS ,RAION_NAME ,RAION_WORDS),
        rule( RAION_NAME ,RAION_WORDS),
        rule( RAION_WORDS ,RAION_NAME),

    ).interpretation(
        Region
    )

    return RAION


###########
#
#   GOROD
#
###########


# Top 200 Russia cities, cover 75% of population

COMPLEX = morph_pipeline([
    'санкт-петербург',
    'нижний новгород',
    'н.новгород',
    'ростов-на-дону',
    'набережные челны',
    'улан-удэ',
    'нижний тагил',
    'комсомольск-на-амуре',
    'йошкар-ола',
    'старый оскол',
    'великий новгород',
    'южно-сахалинск',
    'петропавловск-камчатский',
    'каменск-уральский',
    'орехово-зуево',
    'сергиев посад',
    'новый уренгой',
    'ленинск-кузнецкий',
    'великие луки',
    'каменск-шахтинский',
    'усть-илимск',
    'усолье-сибирский',
    'кирово-чепецк',
    'горно-алтайск',
])

SIMPLE = dictionary({
    'москва',
    'севастополь'
    'новосибирск',
    'екатеринбург',
    'казань',
    'самара',
    'омск',
    'челябинск',
    'уфа',
    'волгоград',
    'пермь',
    'красноярск',
    'воронеж',
    'саратов',
    'краснодар',
    'тольятти',
    'барнаул',
    'ижевск',
    'ульяновск',
    'владивосток',
    'ярославль',
    'иркутск',
    'тюмень',
    'махачкала',
    'хабаровск',
    'оренбург',
    'новокузнецк',
    'кемерово',
    'рязань',
    'томск',
    'астрахань',
    'пенза',
    'липецк',
    'тула',
    'киров',
    'чебоксары',
    'калининград',
    'брянск',
    'курск',
    'иваново',
    'магнитогорск',
    'тверь',
    'ставрополь',
    'симферополь',
    'белгород',
    'архангельск',
    'владимир',
    'сочи',
    'курган',
    'смоленск',
    'калуга',
    'чита',
    'орёл',
    'волжский',
    'череповец',
    'владикавказ',
    'мурманск',
    'сургут',
    'вологда',
    'саранск',
    'тамбов',
    'стерлитамак',
    'грозный',
    'якутск',
    'кострома',
    'петрозаводск',
    'таганрог',
    'нижневартовск',
    'братск',
    'новороссийск',
    'дзержинск',
    'шахта',
    'нальчик',
    'орск',
    'сыктывкар',
    'нижнекамск',
    'ангарск',
    'балашиха',
    'благовещенск',
    'прокопьевск',
    'химки',
    'псков',
    'бийск',
    'энгельс',
    'рыбинск',
    'балаково',
    'северодвинск',
    'армавир',
    'подольск',
    'королёв',
    'сызрань',
    'норильск',
    'златоуст',
    'мытищи',
    'люберцы',
    'волгодонск',
    'новочеркасск',
    'абакан',
    'находка',
    'уссурийск',
    'березники',
    'салават',
    'электросталь',
    'миасс',
    'первоуральск',
    'рубцовск',
    'альметьевск',
    'ковровый',
    'коломна',
    'керчь',
    'майкоп',
    'пятигорск',
    'одинцово',
    'копейск',
    'хасавюрт',
    'новомосковск',
    'кисловодск',
    'серпухов',
    'новочебоксарск',
    'нефтеюганск',
    'димитровград',
    'нефтекамск',
    'черкесск',
    'дербент',
    'камышин',
    'невинномысск',
    'красногорск',
    'мур',
    'батайск',
    'новошахтинск',
    'ноябрьск',
    'кызыл',
    'октябрьский',
    'ачинск',
    'северск',
    'новокуйбышевск',
    'елец',
    'евпатория',
    'арзамас',
    'обнинск',
    'каспийск',
    'элиста',
    'пушкино',
    'жуковский',
    'междуреченск',
    'сарапул',
    'ессентуки',
    'воткинск',
    'ногинск',
    'тобольск',
    'ухта',
    'серов',
    'бердск',
    'мичуринск',
    'киселёвск',
    'новотроицк',
    'зеленодольск',
    'соликамск',
    'раменский',
    'домодедово',
    'магадан',
    'глазов',
    'железногорск',
    'канск',
    'назрань',
    'гатчина',
    'саров',
    'новоуральск',
    'воскресенск',
    'долгопрудный',
    'бугульма',
    'кузнецк',
    'губкин',
    'кинешма',
    'ейск',
    'реутов',
    'железногорск',
    'чайковский',
    'азов',
    'бузулук',
    'озёрск',
    'балашов',
    'юрга',
    'кропоткин',
    'клин'
})

GOROD_ABBR = in_caseless({
    'спб',
    'мск'
    'нск'   # Новосибирск
})

GOROD_NAME = or_(
    rule(SIMPLE),
    rule(COMPLEX),
    rule(GOROD_ABBR)
).interpretation(
    Settlement.name
)

SIMPLE = and_(
    TITLE,
    or_(
        NOUN,
        ADJF,  # Железнодорожный, Юбилейный
    )
)

COMPLEX = or_(
    rule(
        SIMPLE,
        DASH.optional(),
        SIMPLE
    ),
    rule(
        TITLE,
        DASH.optional(),
        caseless('на'),
        DASH.optional(),
        TITLE
    ),
)

NAME = or_(
    rule(SIMPLE),
    COMPLEX
)

MAYBE_GOROD_NAME = or_(
    NAME,
    rule(
        NAME,
        DASH.optional(),
        INT
    ),  # Сольцы 3
    rule(
        NOUN,
        DASH.optional(),
        GRND
    )  # Усть-Катав
).interpretation(
    Settlement.name
)


def get_gorod(cfg):

    gorod_items = or_(
        rule(normalized('город')),
        rule(
            caseless('г'),
            DOT.optional()
        )
    )

    for item in cfg:
        gorod_items.children.append(rule(caseless(item)))

    GOROD_WORDS = gorod_items.interpretation(
        Settlement.type.const('город')
    )

    GOROD_WORDS_GP = or_(
        rule(
            caseless('г'),
            DOT.optional(),
            caseless('п'),
            DOT.optional()
        ),
        rule(
            caseless('г г.п.'),
        )
    ).interpretation(
        Settlement.type.const('город')
    )

    GOROD = or_(
        rule(GOROD_WORDS, MAYBE_GOROD_NAME),
        rule(GOROD_WORDS, MAYBE_GOROD_NAME, GOROD_WORDS_GP),
        rule(MAYBE_GOROD_NAME, GOROD_WORDS),
        rule(MAYBE_GOROD_NAME, GOROD_WORDS_GP),
        rule(
            GOROD_NAME,
            GOROD_WORDS
        ),
        rule(
            GOROD_WORDS,
            GOROD_NAME,
        ),
    ).interpretation(
        Settlement
    )

    return GOROD


##########
#
#  SETTLEMENT NAME
#
##########

SIMPLE = and_(
    or_(
        NOUN,  # Александровка, Заречье, Горки
        ADJS,  # Кузнецово
        ADJF,  # Никольское, Новая, Марьино
        UNKN,
        VERB,
        GRND,
    ),
    TITLE
)


COMPLEX = or_(
    rule('и(при) станция(и)', NOUN),
    rule('и(при) станция(и)', ADJF),
    rule('и(при) станция(и)', ADJS),

    rule(NOUN, ADJF),
    rule(NOUN, NOUN),
    rule(NOUN, DASH, ADJS),
    rule(NOUN, DASH, NOUN),

    rule(NOUN, ADJF, NOUN),
    rule(NOUN, UNKN, NOUN),
    rule(ADVB, DASH, ADJF, NOUN),
    rule(ADJF, NOUN.repeatable(max=5).optional()),  # село Центральной усадьбы племзавода имени Максима Горького

    rule(NOUN, DASH, ADJS),

    rule(ADVB, DASH, GRND),

    rule(
        SIMPLE,
        DASH.optional(),
        SIMPLE,
    ),
    rule(
        ADJF.repeatable(max=4),
        NOUN
    ),  # деревня Холодный ключ, деревня Татарский Сухой Изяк , деревня Русский Сухой Изяк
    rule(
        NOUN.repeatable(max=3),
    ),  # cело санатория имени Чехова
    rule(
        ADJF,
        TITLE,
        DASH.optional(),
        TITLE.optional(),
    ),  # деревня Нижние Виданы деревня Старый Кызыл-Яр
    rule(
        TITLE,
        DASH.optional(),
        TITLE.repeatable(max=3)
    ),  # деревня Нижние Виданы

)

NAME = or_(
    COMPLEX,
    rule(SIMPLE),

)

SETTLEMENT_NAME = or_(
    NAME,
    rule(NAME, '-', INT),
    rule(NAME, INT),
    rule(NAME, INT, NAME),
    rule(NAME, ANUM),

)

###########
#
#   SELO
#
#############

def get_selo(cfg):

    selo_items = or_(
        rule(
            caseless('с'),
            DOT.optional()
        ),
        rule(normalized('село'))
    )

    for item in cfg:
        selo_items.children.append(rule(caseless(item)))

    SELO_WORDS = selo_items.interpretation(
        Settlement.type.const('село')
    )

    SELO_NAME = rule(
        or_(
            SETTLEMENT_NAME,
            rule(TITLE)
        )
    ).interpretation(Settlement.name)

    SELO = or_(
        rule(SELO_WORDS, SELO_NAME),
        rule(SELO_NAME, SELO_WORDS),
    ).interpretation(
        Settlement
    )

    return SELO


###########
#
#   DEREVNYA
#
#############

def get_derevnya(cfg):

    der_items = or_(
        rule(
            caseless('д'),
            DOT.optional()
        ),
        rule(normalized('деревня'))
    )

    for item in cfg:
        der_items.children.append(rule(caseless(item)))

    # TODO: нужно более качественное правило для определения сельсовета
    SELSOVET = rule(
        eq('(').optional(),
        TITLE,
        'с',
        '/',
        'с',
        eq(')').optional()
    )

    DEREVNYA_WORDS = der_items.interpretation(
        Settlement.type.const('деревня')
    )

    DEREVNYA_NAME = rule(
        or_(
            SETTLEMENT_NAME,
            rule(TITLE)
        )
    ).interpretation(
        Settlement.name
    )

    DEREVNYA = rule(
        DEREVNYA_WORDS,
        DEREVNYA_NAME,
        SELSOVET.optional()
    ).interpretation(
        Settlement
    )

    return DEREVNYA


###########
#
#   POSELOK
#
#############


def get_poselok(cfg):

    poselok_items = or_(
        rule(
            in_caseless({'п', 'пос'}),
            DOT.optional()
        ),
        rule(
            in_caseless({'п '}),
            in_caseless({'н'}),
            DOT.optional(),
            in_caseless({'п'}),
            DOT.optional(),
        ),
        rule(
            caseless('р'),
            DOT.optional(),
            caseless('п'),
            DOT.optional()
        ),
        rule(
            normalized('рабочий'),
            normalized('посёлок')
        ),
        rule(
            normalized('дачный'),
            normalized('посёлок')
        ),
        rule(
            normalized('городской'),
            normalized('посёлок')
        ),
        rule(
            caseless('пгт'),
            DOT.optional()
        ),
        rule(
            caseless('пгт н.п.')
        ),
        rule(
            caseless('п'), DOT, caseless('г'), DOT, caseless('т'),
            DOT.optional()
        ),
        rule(
            normalized('посёлок'),
            normalized('городского'),
            normalized('типа'),
        ),
        rule(normalized('поселок'), normalized('станция')),
        rule(morph_pipeline(['поселок при железнодорожной станции'])),
        rule(normalized('сельское'), normalized('поселение')),

        rule(normalized('посёлок')),
        rule(normalized('поселение')),
    )

    for item in cfg:
        poselok_items.children.append(rule(caseless(item)))

    POSELOK_WORDS =poselok_items.interpretation(
        Settlement.type.const('посёлок')
    )

    POSELOK_NAME = rule(
        or_(
            SETTLEMENT_NAME,
            rule(TITLE)
        )
    ).interpretation(
        Settlement.name
    )

    POSELOK = or_(
        rule(POSELOK_WORDS, POSELOK_NAME),
        rule(POSELOK_NAME, POSELOK_WORDS),
    ).interpretation(
        Settlement
    )

    return POSELOK


##############
#
#   ADDR PERSON
#
############


ABBR = and_(
    length_eq(1),
    is_title()
)

PART = and_(
    TITLE,
    or_(
        gram('Name'),
        gram('Surn')
    )
)

MAYBE_FIO = or_(
    rule(TITLE, PART),
    rule(PART, TITLE),
    rule(ABBR, '.', TITLE),
    rule(ABBR, '.', ABBR, '.', TITLE),
    rule(TITLE, ABBR, '.', ABBR, '.')
)

POSITION_WORDS_ = or_(
    rule(
        dictionary({
            'мичман',
            'геолог',
            'подводник',
            'краевед',
            'снайпер',
            'штурман',
            'бригадир',
            'учитель',
            'политрук',
            'военком',
            'ветеран',
            'историк',
            'пулемётчик',
            'авиаконструктор',
            'адмирал',
            'академик',
            'актер',
            'актриса',
            'архитектор',
            'атаман',
            'врач',
            'воевода',
            'генерал',
            'губернатор',
            'хирург',
            'декабрист',
            'разведчик',
            'граф',
            'десантник',
            'конструктор',
            'скульптор',
            'писатель',
            'поэт',
            'капитан',
            'князь',
            'комиссар',
            'композитор',
            'космонавт',
            'купец',
            'лейтенант',
            'лётчик',
            'майор',
            'маршал',
            'матрос',
            'подполковник',
            'полковник',
            'профессор',
            'сержант',
            'старшина',
            'танкист',
            'художник',
            'герой',
            'княгиня',
            'строитель',
            'дружинник',
            'диктор',
            'прапорщик',
            'артиллерист',
            'графиня',
            'большевик',
            'патриарх',
            'сварщик',
            'офицер',
            'рыбак',
            'брат',
        })
    ),
    rule(normalized('генерал'), normalized('армия')),
    rule(normalized('герой'), normalized('россия')),
    rule(
        normalized('герой'),
        normalized('российский'), normalized('федерация')),
    rule(
        normalized('герой'),
        normalized('советский'), normalized('союз')
    ),
)

ABBR_POSITION_WORDS = rule(
    in_caseless({
        'адм',
        'ак',
        'акад',
    }),
    DOT.optional()
)

POSITION_WORDS = or_(
    POSITION_WORDS_,
    ABBR_POSITION_WORDS
)

MAYBE_PERSON = or_(
    MAYBE_FIO,
    rule(POSITION_WORDS, MAYBE_FIO),
    rule(POSITION_WORDS, TITLE)
)

###########
#
#   IMENI
#
##########


IMENI_WORDS = or_(
    rule(
        caseless('им'),
        DOT.optional()
    ),
    rule(caseless('имени'))
)

IMENI = or_(
    rule(
        IMENI_WORDS.optional(),
        MAYBE_PERSON
    ),
    rule(
        IMENI_WORDS,
        TITLE
    )
)

##########
#
#   LET
#
##########


LET_WORDS = or_(
    rule(caseless('лет')),
    rule(
        DASH.optional(),
        caseless('летия')
    )
)

LET_NAME = in_caseless({
    'влксм',
    'ссср',
    'алтая',
    'башкирии',
    'бурятии',
    'дагестана',
    'калмыкии',
    'колхоза',
    'комсомола',
    'космонавтики',
    'москвы',
    'октября',
    'пионерии',
    'победы',
    'приморья',
    'района',
    'совхоза',
    'совхозу',
    'татарстана',
    'тувы',
    'удмуртии',
    'улуса',
    'хакасии',
    'целины',
    'чувашии',
    'якутии',
})

LET = rule(
    INT,
    LET_WORDS,
    LET_NAME
)

##########
#
#    ADDR DATE
#
#############


MONTH_WORDS = dictionary({
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь',
})

DAY = and_(
    INT,
    gte(1),
    lte(31)
)

YEAR = and_(
    INT,
    gte(1),
    lte(2100)
)

YEAR_WORDS = normalized('год')

DATE = or_(
    rule(DAY, MONTH_WORDS),
    rule(YEAR, YEAR_WORDS)
)

#########
#
#   MODIFIER
#
############


MODIFIER_WORDS_ = rule(
    dictionary({
        'большой',
        'малый',
        'средний',

        'верхний',
        'центральный',
        'нижний',
        'северный',
        'дальний',

        'первый',
        'второй',

        'старый',
        'новый',

        'красный',
        'лесной',
        'тихий',
    }),
    DASH.optional()
)

ABBR_MODIFIER_WORDS = rule(
    in_caseless({
        'б', 'м', 'н'
    }),
    DOT.optional()
)

SHORT_MODIFIER_WORDS = rule(
    in_caseless({
        'больше',
        'мало',
        'средне',

        'верх',
        'верхне',
        'центрально',
        'нижне',
        'северо',
        'дальне',
        'восточно',
        'западно',

        'перво',
        'второ',

        'старо',
        'ново',

        'красно',
        'тихо',
        'горно',
    }),
    DASH.optional()
)

MODIFIER_WORDS = or_(
    MODIFIER_WORDS_,
    ABBR_MODIFIER_WORDS,
    SHORT_MODIFIER_WORDS,
)

##########
#
#   ADDR NAME
#
##########


ROD = gram('gent')

SIMPLE = and_(
    or_(
        ADJF,  # Школьная
        and_(NOUN, ROD),  # Ленина, Победы
    ),
    TITLE
)

COMPLEX = or_(
    rule(
        and_(ADJF, TITLE),
        NOUN
    ),
    rule(
        TITLE,
        DASH.optional(),
        TITLE
    ),
)

# TODO
EXCEPTION = dictionary({
    'арбат',
    'варварка'
})

MAYBE_NAME = or_(
    rule(SIMPLE),
    COMPLEX,
    rule(EXCEPTION)
)

NAME = or_(
    MAYBE_NAME,
    LET,
    DATE,
    IMENI
)

NAME = rule(
    MODIFIER_WORDS.optional(),
    NAME
)

ADDR_CRF = tag('I').repeatable()

NAME = or_(
    NAME,
    ANUM,
    rule(NAME, ANUM),
    rule(NAME, NAME),
    rule(ANUM, NAME),
    rule(INT, DASH.optional(), NAME),
    rule(NAME, DASH, INT),
    ADDR_CRF,
    rule(TITLE)
)

ADDR_NAME = or_(
    NAME,
    rule(
        INT, '-',
        INT, '-',
        INT
    ),
    rule(
        INT,
        '-',
        INT
    ),
    rule(
        INT,
        'км'
    ),
    rule(
        NAME,
        NAME
    ),
    rule(
        INT
    )
)


########
#
#    STREET
#
#########


def get_street(street_cfg):
    street_all_items = or_(
        rule(normalized('улица')),
        rule(normalized('улица')),
        rule(
            caseless('ул'),
            DOT.optional()
        )
    )

    for item in street_cfg:
        street_all_items.children.append(rule(caseless(item)))

    STREET_WORDS = street_all_items.interpretation(
        Street.type.const('улица')
    )

    STREET_NAME = ADDR_NAME.interpretation(
        Street.name
    )

    return or_(
        rule(STREET_WORDS, STREET_NAME),
        rule(STREET_NAME, STREET_WORDS)
    ).interpretation(
        Street
    )


##########
#
#    MKR
#
##########

def get_mkr(cfg):
    mrk_items = or_(
        rule(caseless('мкр')),
        rule(
            caseless('мкр'),
            DOT.optional()
        ),
        rule(normalized('микрорайон'))
    )

    for item in cfg:
        mrk_items.children.append(rule(caseless(item)))

    MKR_WORDS = mrk_items.interpretation(
        Street.type.const('микрорайон')
    )

    MKR_NAME = ADDR_NAME.interpretation(
        Street.name
    )

    MKR = or_(
        rule(MKR_WORDS, MKR_NAME),
        rule(MKR_NAME, MKR_WORDS)
    ).interpretation(
        Street
    )

    return MKR


##########
#
#    OTHER SETTLEMENT ITEMS (AUL, KISHLAK)
#
##########

def get_other_settl(cfg_item):
    cfg_item_name = cfg_item['name']
    cfg_item_data = cfg_item['data']
    snt_items = or_(rule(caseless(cfg_item_data[0])))

    i = 0
    for item in cfg_item_data:
        if i > 0:
            snt_items.children.append(rule(caseless(item)))
        i += 1

    SNT_WORDS = snt_items.interpretation(Settlement.type.const(cfg_item_name))

    SNT_NAME = ADDR_NAME.interpretation(Settlement.name)

    SNT = or_(
        rule(
            SNT_WORDS,
            SNT_NAME
        ),
    ).interpretation(Settlement)

    return SNT


##########
#
#    OTHER LOCAL (terr, snt)
#
##########

def get_other_local(cfg_item):
    cfg_item_name = cfg_item['name']
    cfg_item_data = cfg_item['data']
    snt_items = or_(rule(caseless(cfg_item_data[0])))

    i = 0
    for item in cfg_item_data:
        if i > 0:
            snt_items.children.append(rule(caseless(item)))
        i += 1

    SNT_WORDS = snt_items.interpretation(Settlement.type.const(cfg_item_name))

    SNT_NAME = ADDR_NAME.interpretation(Settlement.name)

    SNT = or_(
        rule(
            SNT_WORDS,
            SNT_NAME
        )
    ).interpretation(Settlement)

    return SNT


##########
#
#    OTHER STREET ITEMS (SNT, TER
#
##########

def get_other_street(cfg_item):
    cfg_item_name = cfg_item['name']
    cfg_item_data = cfg_item['data']
    snt_items = or_(rule(caseless(cfg_item_data[0])))

    i = 0
    for item in cfg_item_data:
        if i > 0:
            snt_items.children.append(rule(caseless(item)))
        i += 1

    SNT_WORDS = snt_items.interpretation(Street.type.const(cfg_item_name))

    SNT_NAME = ADDR_NAME.interpretation(Street.name)

    SNT = or_(rule(SNT_WORDS, SNT_NAME), rule(SNT_NAME, SNT_WORDS)).interpretation(Street)

    return SNT


##########
#
#    PROSELOK
#
##########

def get_proselok(cfg):
    pros_items = or_(
        rule(caseless('проселок')),

    )

    for item in cfg:
        pros_items.children.append(rule(caseless(item)))

    PROS_WORDS = pros_items.interpretation(
        Street.type.const('проселок')
    )

    PROS_NAME = ADDR_NAME.interpretation(
        Street.name
    )

    PROSELOK = or_(
        rule(PROS_WORDS, PROS_NAME),

    ).interpretation(
        Street
    )

    return PROSELOK


##########
#
#    PROSPEKT
#
##########


PROSPEKT_WORDS = or_(
    rule(
        in_caseless({'пр', 'просп'}),
        DOT.optional()
    ),
    rule(
        caseless('пр'),
        '-',
        in_caseless({'кт', 'т'}),
        DOT.optional()
    ),
    rule(normalized('проспект'))
).interpretation(
    Street.type.const('проспект')
)

PROSPEKT_NAME = ADDR_NAME.interpretation(
    Street.name
)

PROSPEKT = or_(
    rule(PROSPEKT_WORDS, PROSPEKT_NAME),
    rule(PROSPEKT_NAME, PROSPEKT_WORDS)
).interpretation(
    Street
)

############
#
#    PROEZD
#
#############


PROEZD_WORDS = or_(
    rule(caseless('пр'), DOT.optional()),
    rule(
        caseless('пр'),
        '-',
        in_caseless({'зд', 'д'}),
        DOT.optional()
    ),
    rule(normalized('проезд'))
).interpretation(
    Street.type.const('проезд')
)

PROEZD_NAME = ADDR_NAME.interpretation(
    Street.name
)

PROEZD = or_(
    rule(PROEZD_WORDS, PROEZD_NAME),
    rule(PROEZD_NAME, PROEZD_WORDS)
).interpretation(
    Street
)

###########
#
#   PEREULOK
#
##############


PEREULOK_WORDS = or_(
    rule(
        caseless('п'),
        DOT
    ),
    rule(
        caseless('пер'),
        DOT.optional()
    ),
    rule(normalized('переулок'))
).interpretation(
    Street.type.const('переулок')
)

PEREULOK_NAME = ADDR_NAME.interpretation(
    Street.name
)

PEREULOK = or_(
    rule(PEREULOK_WORDS, PEREULOK_NAME),
    rule(PEREULOK_NAME, PEREULOK_WORDS)
).interpretation(
    Street
)

########
#
#  PLOSHAD
#
##########


PLOSHAD_WORDS = or_(
    rule(
        caseless('пл'),
        DOT.optional()
    ),
    rule(normalized('площадь'))
).interpretation(
    Street.type.const('площадь')
)

PLOSHAD_NAME = ADDR_NAME.interpretation(
    Street.name
)

PLOSHAD = or_(
    rule(PLOSHAD_WORDS, PLOSHAD_NAME),
    rule(PLOSHAD_NAME, PLOSHAD_WORDS)
).interpretation(
    Street
)


############
#
#   SHOSSE
#
###########


# TODO
# Покровское 17 км.
# Сергеляхское 13 км
# Сергеляхское 14 км.


def get_shosse(cfg):
    SHOSSE_WORDS = or_(
        rule(
            caseless('ш'),
            DOT
        ),
        rule(normalized('шоссе')),

    ).interpretation(
        Street.type.const('шоссе')
    )

    SHOSSE_NAME = ADDR_NAME.interpretation(
        Street.name
    )

    SHOSSE = or_(
        rule(SHOSSE_WORDS, SHOSSE_NAME),
        rule(SHOSSE_NAME, SHOSSE_WORDS)
    ).interpretation(
        Street
    )

    return SHOSSE


########
#
#  NABEREG
#
##########


NABEREG_WORDS = or_(
    rule(
        caseless('наб'),
        DOT.optional()
    ),
    rule(normalized('набережная'))
).interpretation(
    Street.type.const('набережная')
)

NABEREG_NAME = ADDR_NAME.interpretation(
    Street.name
)

NABEREG = or_(
    rule(NABEREG_WORDS, NABEREG_NAME),
    rule(NABEREG_NAME, NABEREG_WORDS)
).interpretation(
    Street
)

########
#
#  BULVAR
#
##########


BULVAR_WORDS = or_(
    rule(
        caseless('б'),
        '-',
        caseless('р')
    ),
    rule(
        caseless('б'),
        DOT
    ),
    rule(
        caseless('бул'),
        DOT.optional()
    ),
    rule(normalized('бульвар'))
).interpretation(
    Street.type.const('бульвар')
)

BULVAR_NAME = ADDR_NAME.interpretation(
    Street.name
)

BULVAR = or_(
    rule(BULVAR_WORDS, BULVAR_NAME),
    rule(BULVAR_NAME, BULVAR_WORDS)
).interpretation(
    Street
)

##############
#
#   ADDR VALUE
#
#############


LETTER = in_caseless(set('абвгдежзиклмнопрстуфхшщэюя'))

QUOTE = in_(QUOTES)

LETTER = or_(
    rule(LETTER),
    rule(QUOTE, LETTER, QUOTE)
)

VALUE = rule(
    INT,
    LETTER.optional()
)

VALUE_STR = or_(rule(INT), rule(LETTER,),rule(LETTER,LETTER), rule(LETTER, '-', LETTER), rule(  INT, LETTER.optional()), rule('-',LETTER),
                rule(LETTER, INT), rule(INT, '_', LETTER), rule(INT, '-', LETTER),  rule(INT, '-', INT),rule(LETTER, '-', INT), rule(INT, '/', LETTER),
                rule(INT, LETTER.optional(), '/', INT, LETTER.optional()), rule(INT,LETTER.optional(), '/', INT, LETTER.optional(),'/', INT,LETTER.optional()),rule(LETTER,'/',INT))

SEP = in_(r'/\-')

VALUE = or_(
    rule(VALUE),
    rule(VALUE_STR),
    rule(VALUE, SEP, VALUE),
    rule(VALUE, SEP, LETTER)
)

ADDR_VALUE = rule(
    eq('№').optional(),
    VALUE
)

############
#
#    DOM
#
#############


DOM_WORDS = or_(
    rule(normalized('дом')),
    rule(
        caseless('д'),
        DOT
    )
).interpretation(
    Building.type.const('дом')
)

DOM_VALUE = ADDR_VALUE.interpretation(
    Building.number
)

DOM = rule(
    DOM_WORDS,
    DOM_VALUE
).interpretation(
    Building
)

###########
#
#  KORPUS
#
##########


korpus_all_items = or_(
    rule(in_caseless({'корп', 'кор', 'корпус'}), DOT.optional()), rule(normalized('корпус'))
)

ext_korp_words = []

for item in ext_korp_words:
    korpus_all_items.children.append(rule(caseless(item)))

KORPUS_WORDS = korpus_all_items.interpretation(
    Building.type.const('корпус')
)

KORPUS_VALUE = ADDR_VALUE.interpretation(
    Building.number
)

KORPUS = or_(
    rule(
        KORPUS_WORDS,
        KORPUS_VALUE
    ),
    rule(
        KORPUS_VALUE,
        KORPUS_WORDS
    )
).interpretation(
    Building
)

###########
#
#  LITERA
#
##########


LITERA_WORDS = or_(
    rule(
        caseless('лит'),
        DOT.optional()
    ),
    rule(normalized('литера')),

).interpretation(
    Building.type.const('литера')
)

LITERA_VALUE = ADDR_VALUE.interpretation(
    Building.number
)

LITERA = rule(
    LITERA_WORDS,
    VALUE_STR
).interpretation(
    Building
)

###########
#
#  STROENIE
#
##########


STROENIE_WORDS = or_(
    rule(
        caseless('стр'),
        DOT.optional()
    ),
    rule(normalized('строение')),

).interpretation(
    Building.type.const('строение')
)

STROENIE_VALUE = ADDR_VALUE.interpretation(
    Building.number
)

STROENIE = rule(
    STROENIE_WORDS,
    VALUE_STR
).interpretation(
    Building
)

###########
#
#  SOORUZH
#
##########


SOORUZH_WORDS = or_(
    rule(
        caseless('соор'),
        DOT.optional()
    ),
    rule(normalized('сооружение')),

).interpretation(
    Building.type.const('сооружение')
)

SOORUZH_VALUE = ADDR_VALUE.interpretation(
    Building.number
)

SOORUZH = rule(
    SOORUZH_WORDS,
    VALUE_STR
).interpretation(
    Building
)

###########
#
#   OFIS
#
#############


OFIS_WORDS = or_(
    rule(
        caseless('оф'),
        DOT.optional()
    ),
    rule(normalized('офис'))
).interpretation(
    Room.type.const('офис')
)

OFIS_VALUE = ADDR_VALUE.interpretation(
    Room.number
)

OFIS = rule(
    OFIS_WORDS,
    OFIS_VALUE
).interpretation(
    Room
)

###########
#
#   KVARTIRA
#
#############


KVARTIRA_WORDS = or_(
    rule(
        caseless('кв'),
        DOT.optional()
    ),
    rule(normalized('квартира'))
).interpretation(
    Room.type.const('квартира')
)

KVARTIRA_VALUE = ADDR_VALUE.interpretation(
    Room.number
)

KVARTIRA = rule(
    KVARTIRA_WORDS,
    KVARTIRA_VALUE
).interpretation(
    Room
)

###########
#
#   INDEX
#
#############


INDEX = and_(
    INT,
    gte(100000),
    lte(999999)
).interpretation(
    Index.value
).interpretation(
    Index
)


#############
#
#   ADDR PART
#
############


def get_addr_part(config):
    cfg_street = config['street'] if 'street' in config else []
    cfg_raion = config['raion'] if 'raion' in config else []
    cfg_poselok = config['poselok'] if 'poselok' in config else []
    cfg_gorod = config['gorod'] if 'gorod' in config else []
    cfg_oblast = config['oblast'] if 'oblast' in config else []
    cfg_fed = config['fedokr'] if 'fedokr' in config else []
    cfg_krai = config['krai'] if 'krai' in config else []
    cfg_derevnya = config['derevnya'] if 'derevnya' in config else []
    cfg_selo = config['selo'] if 'selo' in config else []
    cfg_resp = config['respublika'] if 'respublika' in config else []
    cfg_shosse = config['shosse'] if 'shosse' in config else []
    cfg_mkr = config['mkr'] if 'mkr' in config else []
    cfg_other_street = config['other_street'] if 'other_street' in config else []
    cfg_other_settlement = config['other_settlement'] if 'other_settlement' in config else []
    cfg_other_local = config['other_local'] if 'other_local' in config else []
    cfg_proselok = config['proselok'] if 'proselok' in config else []

    addr_cfg_array = or_(
        INDEX,
        COUNTRY,
        get_fed(cfg_fed),

        get_resp(cfg_resp),
        get_krai(cfg_krai),
        get_oblast(cfg_oblast),
        AUTO_OKRUG,
        get_raion(cfg_raion),


        get_gorod(cfg_gorod),
        get_derevnya(cfg_derevnya),
        get_poselok(cfg_poselok),
        get_selo(cfg_selo),

        get_street(cfg_street),
        get_mkr(cfg_mkr),
        get_proselok(cfg_proselok),
        PROSPEKT,
        PROEZD,
        PEREULOK,
        PLOSHAD,
        get_shosse(cfg_shosse),
        NABEREG,
        BULVAR,

        DOM,
        KORPUS,
        LITERA,
        STROENIE,
        SOORUZH,
        OFIS,
        KVARTIRA
    )

    if len(cfg_other_settlement) > 0:
        for item in cfg_other_settlement:
            addr_cfg_array.children.append(get_other_settl(item))

    if len(cfg_other_local) > 0:
        for item in cfg_other_local:
            addr_cfg_array.children.append(get_other_local(item))

    if len(cfg_other_street) > 0:
        for item in cfg_other_street:
            addr_cfg_array.children.append(get_other_street(item))

    ADDR_CFG = addr_cfg_array.interpretation(
        AddrPart.value
    ).interpretation(
        AddrPart
    )

    return ADDR_CFG
