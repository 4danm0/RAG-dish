# config.py

import os
from dotenv import load_dotenv

load_dotenv()

VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN') 
VK_API_VERSION = '5.131'

PUBLICS = [
    ('-32509740', 'Just Cook'),
    ('-165062392', 'Быстрые рецепты'),
    ('-35806378', 'Коллекция Рецептов'),
    ('-166012005', 'КУХНЯ'),
    ('-122428754', 'Простые рецепты')
]

MIN_LIKES = 10 # минимальное количество лайков для поста, чтобы он был добавлен в базу
MAX_POSTS_PER_GROUP = 100 # максимальное количество постов, которые будут спарсены из одного паблика

API_KEY = os.getenv('CLOUD_API_KEY')
API_BASE_URL = "https://foundation-models.api.cloud.ru/v1"
EMBEDDER_MODEL = "BAAI/bge-m3"

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat" 

QDRANT_PATH = 'qdrant_db_vk'
COLLECTION_NAME = 'vk_posts'