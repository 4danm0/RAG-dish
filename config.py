# config.py
import os
from dotenv import load_dotenv

load_dotenv()

VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN') 
VK_API_VERSION = '5.131'

API_KEY = os.getenv('CLOUD_API_KEY')
API_BASE_URL = "https://foundation-models.api.cloud.ru/v1"
EMBEDDER_MODEL = "BAAI/bge-m3"

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat" 

QDRANT_PATH = 'qdrant_db_vk'
COLLECTION_NAME = 'vk_posts'

PUBLICS = [
    ('-32509740', 'Just Cook'),
    ('-165062392', 'Быстрые рецепты'),
    ('-35806378', 'Коллекция Рецептов'),
    ('-166012005', 'КУХНЯ'),
    ('-122428754', 'Простые рецепты')
]

MAX_POSTS_PER_GROUP = 15000 # максимальное количество постов, которые будут спарсены из одного паблика

# Настройки фильтрации
MIN_LIKES = 10 # минимальное количество лайков для поста, чтобы он был добавлен в базу
MIN_TEXT_LEN = 100
MAX_TEXT_LEN = 3500 # Слишком длинные тексты часто бывают спамом или подборками из 10 рецептов сразу

BAD_LINKS = [
    't.me/', 'vk.cc/', 'wildberries.ru', 'ozon.ru', 'aliexpress', 
    'wa.me/', 'taplink', 'vk.com/app', 'click', 'bit.ly'
]

# Жесткие стоп-слова (реклама, байт на активность, конкурсы)
STOP_PHRASES = [
    'erid', 'продолжение рецепта', 'подпишись', 'промокод', 
    'сделай репост', 'розыгрыш', 'пиши в директ', 'ссылка в шапке', 
    'бесплатно', 'подарок', 'лайктайм', 'в комментариях', 'переходи по ссылке',
    'спонсор', 'заказывала', 'артикул'
]

# Маркеры настоящего рецепта 
# (Длинные слова оставляем корнями, а к коротким добавляем пробелы или точки)
RECIPE_MARKERS = [
    'ингредиент', 'приготовление', 'рецепт', 'соль', 'порци', 'варить', 
    'жарить', 'запекать', 'духовк', 'нарезать', 'смешать', 
    ' г ', ' г.', ' кг ', ' кг.', ' мл ', ' мл.', 'ст.л', 'ч.л'
]