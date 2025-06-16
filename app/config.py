import logging
from pydantic_settings import BaseSettings
from logging.config import dictConfig
from dotenv import load_dotenv
import os


# Загружаем переменные из .env
load_dotenv()

class Settings(BaseSettings):
    gdrive_file_ids: dict = {
        "config.json": os.getenv("GDRIVE_CONFIG_FILE_ID"),
        "model.safetensors": os.getenv("GDRIVE_MODEL_FILE_ID"),
        "preprocessor_config.json": os.getenv("GDRIVE_PREPROCESSOR_FILE_ID"),
        "metadata.json": os.getenv("GDRIVE_METADATA_FILE_ID")
    }

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")

    mushroom_descriptions: dict = {
        'Stropharia aeruginosa': '🟢 Строфария сине-зелёная (Съедобен)',
        'Hericium coralloides': '🟢 Ежовик коралловидный (Съедобен)',
        'Coprinellus micaceus': '🔴 Навозник мерцающий (Несъедобен)',
        'Cerioporus squamosus': '🟢 Трутовик чешуйчатый (Съедобен)',
        'Fomes fomentarius': '🟢 Трутовик настоящий (Съедобен)',
        'Gyromitra gigas': '🔴 Строчок гигантский (Несъедобен)',
        'Cantharellus cibarius': '🟢 Лисичка обыкновенная (Съедобен)',
        'Boletus reticulatus': '🟢 Боровик сетчатый (Съедобен)',
        'Phallus impudicus': '🟢 Весёлка обыкновенная (Съедобен)',
        'Calocera viscosa': '🟢 Калоцера клейкая (Съедобен)',
        'Flammulina velutipes': '🟢 Опёнок зимний (Съедобен)',
        'Lactarius deliciosus': '🟢 Рыжик настоящий (Съедобен)',
        'Physcia adscendens': '🔴 Фисция восходящая (Несъедобен)',
        'Cladonia rangiferina': '🔴 Кладония оленья (Несъедобен)',
        'Leccinum albostipitatum': '🟢 Подосиновик белоножковый (Съедобен)',
        'Xanthoria parietina': '🔴 Ксантория настенная (Несъедобен)',
        'Lactarius turpis': '🟡 Груздь чёрный (Условно-съедобен)',
        'Hypogymnia physodes': '🔴 Гипогимния вздутая (Несъедобен)',
        'Leccinum scabrum': '🟢 Подберёзовик обыкновенный (Съедобен)',
        'Paxillus involutus': '🔴 Свинушка тонкая (Несъедобен)',
        'Phellinus tremulae': '🔴 Ложный осиновый трутовик (Несъедобен)',
        'Leccinum aurantiacum': '🟢 Подосиновик красный (Съедобен)',
        'Trametes hirsuta': '🔴 Траметес жёстковолосистый (Несъедобен)',
        'Panellus stipticus': '🟡 Панеллюс вяжущий (Условно-съедобен)',
        'Chondrostereum purpureum': '🔴 Хондростереум пурпурный (Несъедобен)',
        'Gyromitra infula': '🔴 Строчок осенний (Несъедобен)',
        'Amanita muscaria': '🔴 Мухомор красный (Несъедобен)',
        'Trametes ochracea': '🔴 Траметес охряный (Несъедобен)',
        'Ganoderma applanatum': '🔴 Трутовик плоский (Несъедобен)',
        'Fomitopsis betulina': '🔴 Трутовик берёзовый (Несъедобен)',
        'Clitocybe nebularis': '🟡 Говорушка дымчатая (Условно-съедобен)',
        'Cladonia fimbriata': '🔴 Кладония бахромчатая (Несъедобен)',
        'Pleurotus ostreatus': '🟢 Вёшенка обыкновенная (Съедобен)',
        'Tremella mesenterica': '🟢 Дрожалка оранжевая (Съедобен)',
        'Stereum hirsutum': '🔴 Стереум жестковолосый (Несъедобен)',
        'Phlebia radiata': '🟢 Флебия радиальная (Съедобен)',
        'Kuehneromyces mutabilis': '🟢 Опёнок летний (Съедобен)',
        'Coltricia perennis': '🔴 Сухлянка двухлетняя (Несъедобен)',
        'Hygrophoropsis aurantiaca': '🟢 Ложная лисичка (Съедобен)',
        'Coprinellus disseminatus': '🔴 Навозник рассеянный (Несъедобен)',
        'Cladonia stellaris': '🔴 Кладония звездчатая (Несъедобен)',
        'Suillus grevillei': '🟢 Маслёнок лиственничный (Съедобен)',
        'Boletus edulis': '🟢 Белый гриб (Съедобен)',
        'Crucibulum laeve': '🔴 Бокальчик гладкий (Несъедобен)',
        'Hypholoma lateritium': '🟢 Ложноопёнок кирпично-красный (Съедобен)',
        'Lepista nuda': '🟡 Рядовка фиолетовая (Условно-съедобен)',
        'Daedaleopsis confragosa': '🟢 Дедалеопсис бугристый (Съедобен)',
        'Lycoperdon perlatum': '🟡 Дождевик шиповатый (Условно-съедобен)',
        'Daedaleopsis tricolor': '🔴 Дедалеопсис трёхцветный (Несъедобен)',
        'Chlorociboria aeruginascens': '🔴 Хлороцибория сине-зеленоватая (Несъедобен)',
        'Suillus granulatus': '🟢 Маслёнок зернистый (Съедобен)',
        'Peltigera praetextata': '🔴 Пельтигера окаймлённая (Несъедобен)',
        'Lobaria pulmonaria': '🔴 Лобария лёгочная (Несъедобен)',
        'Inonotus obliquus': '🔴 Трутовик скошенный (Несъедобен)',
        'Lactarius torminosus': '🟡 Волнушка розовая (Условно-съедобен)',
        'Fomitopsis pinicola': '🟢 Трутовик окаймлённый (Съедобен)',
        'Pholiota aurivella': '🟢 Чешуйчатка золотистая (Съедобен)',
        'Amanita pantherina': '🟡 Мухомор пантерный (Условно-съедобен)',
        'Coprinopsis atramentaria': '🟡 Навозник серый (Условно-съедобен)',
        'Evernia prunastri': '🔴 Эверния сливовая (Несъедобен)',
        'Hypholoma fasciculare': '🔴 Ложноопёнок серно-жёлтый (Несъедобен)',
        'Amanita rubescens': '🟡 Мухомор серо-розовый (Условно-съедобен)',
        'Merulius tremellosus': '🔴 Флебия дрожащая (Несъедобен)',
        'Vulpicida pinastri': '🔴 Вульпицида сосновая (Несъедобен)',
        'Parmelia sulcata': '🔴 Пармелия бороздчатая (Несъедобен)',
        'Cetraria islandica': '🟢 Цетрария исландская (Съедобен)',
        'Laetiporus sulphureus': '🟢 Трутовик серно-жёлтый (Съедобен)',
        'Pholiota squarrosa': '🟢 Чешуйчатка обыкновенная (Съедобен)',
        'Trametes versicolor': '🔴 Траметес разноцветный (Несъедобен)',
        'Amanita citrina': '🔴 Мухомор поганковидный (Несъедобен)',
        'Armillaria borealis': '🟢 Опёнок северный (Съедобен)',
        'Macrolepiota procera': '🟢 Гриб-зонтик пёстрый (Съедобен)',
        'Peltigera aphthosa': '🔴 Пельтигера пупырчатая (Несъедобен)',
        'Gyromitra esculenta': '🔴 Строчок обыкновенный (Несъедобен)',
        'Platismatia glauca': '🔴 Платизматия сизая (Несъедобен)',
        'Imleria badia': '🟢 Польский гриб (Съедобен)',
        'Sarcoscypha austriaca': '🟢 Саркосцифа австрийская (Съедобен)',
        'Coprinus comatus': '🟡 Навозник белый (Условно-съедобен)',
        'Trichaptum biforme': '🔴 Трихаптум двоякий (Несъедобен)',
        'Leccinum versipelle': '🟢 Подосиновик жёлто-бурый (Съедобен)',
        'Pleurotus pulmonarius': '🟢 Вёшенка лёгочная (Съедобен)',
        'Suillus luteus': '🟢 Маслёнок обыкновенный (Съедобен)',
        'Pseudevernia furfuracea': '🔴 Псевдеверния зернистая (Несъедобен)',
        'Phellinus igniarius': '🔴 Трутовик ложный (Несъедобен)',
        'Nectria cinnabarina': '🔴 Нектрия киноварно-красная (Несъедобен)',
        'Schizophyllum commune': '🟢 Щелелистник обыкновенный (Съедобен)',
        'Tricholomopsis rutilans': '🟡 Рядовка жёлто-красная (Условно-съедобен)',
        'Bjerkandera adusta': '🔴 Бьеркандера опалённая (Несъедобен)'
    }

    class Config:
        protected_namespaces = ('settings_',)


# Настройка логирования
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["default"],
            "level": "DEBUG", # INFO или DEBUG
            "propagate": False
        },
        "gdown": {
            "handlers": ["default"],
            "level": "WARNING"
        }
    }
}

dictConfig(LOG_CONFIG)
logger = logging.getLogger("app")

settings = Settings()