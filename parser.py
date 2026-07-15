# parser.py
import requests
import time
import re
import hashlib
from config import (VK_ACCESS_TOKEN, VK_API_VERSION, PUBLICS, MIN_LIKES, 
                    MAX_POSTS_PER_GROUP, MIN_TEXT_LEN, MAX_TEXT_LEN, 
                    BAD_LINKS, STOP_PHRASES, RECIPE_MARKERS)

def fetch_with_retry(url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"  [Сбой сети] Попытка {attempt + 1}. Ждем 5 сек...")
            time.sleep(5)
    return None

def is_valid_recipe(post):
    # 1. Базовые проверки VK
    if post.get('marked_as_ads', 0) == 1: return False
    if post.get('likes', {}).get('count', 0) < MIN_LIKES: return False
    
    text = post.get('text', '').strip()
    
    # 2. Проверка длины текста
    if not (MIN_TEXT_LEN <= len(text) <= MAX_TEXT_LEN): return False
        
    text_lower = text.lower()
    
    # 3. Проверка на внешние и рекламные ссылки
    if any(link in text_lower for link in BAD_LINKS): return False
        
    # 4. Проверка на стоп-слова (байт, конкурсы)
    if any(phrase in text_lower for phrase in STOP_PHRASES): return False
        
    # 5. Проверка "А точно ли это рецепт?"
    # Считаем, сколько кулинарных слов-маркеров есть в тексте
    markers_found = sum(1 for marker in RECIPE_MARKERS if marker in text_lower)
    if markers_found < 2: 
        return False
        
    # 6. Защита от спама хештегами (если хештегов больше 5 — это мусорный пост)
    hashtags_count = len(re.findall(r'#\w+', text))
    if hashtags_count > 5:
        return False
        
    return True

def get_text_fingerprint(text):
    # 1. Оставляем ТОЛЬКО чистые буквы алфавита (без цифр, пробелов, эмодзи и знаков)
    letters_only = re.sub(r'[^а-яёa-z]', '', text.lower())
    
    # 2. Вырезаем кусок из рецепта (со 30-й по 150-ю букву)
    # Это позволяет отбросить разные приветствия в начале и приписки в конце
    if len(letters_only) > 150:
        core_text = letters_only[30:150]
    else:
        core_text = letters_only
        
    return hashlib.md5(core_text.encode('utf-8')).hexdigest()

def clean_text_for_ai(text):
    text = re.sub(r'#\w+', '', text) 
    text = re.sub(r'[^\w\s\.,!?\-\:\(\)«»]', '', text) 
    return re.sub(r'\s+', ' ', text).strip()

def get_all_posts(max_posts_per_group=MAX_POSTS_PER_GROUP, progress_callback=None):
    all_documents = []
    chunk_size = 100 
    seen_fingerprints = set()
    
    for owner_id, tag in PUBLICS:
        print(f"\nНачинаем парсинг: {tag}...")
        
        # Оповещаем UI о старте работы с новым пабликом
        if progress_callback:
            progress_callback(
                tag=tag, 
                count=len(all_documents), 
                status_text="Подключаемся к VK API и получаем количество постов..."
            )
            
        url = 'https://api.vk.com/method/wall.get'
        
        init_params = {'owner_id': owner_id, 'count': 1, 'access_token': VK_ACCESS_TOKEN, 'v': VK_API_VERSION}
        init_response = fetch_with_retry(url, init_params)
        
        if not init_response or 'error' in init_response: continue
        total_posts = init_response['response']['count']
        if total_posts == 0: continue
            
        n_chunks = max(1, max_posts_per_group // chunk_size)
        jump = chunk_size if total_posts <= max_posts_per_group else total_posts // n_chunks
        actual_chunks = (total_posts + chunk_size - 1) // chunk_size if total_posts <= max_posts_per_group else n_chunks
            
        for i in range(actual_chunks - 1, -1, -1):
            offset = i * jump
            fetch_count = min(chunk_size, total_posts - offset) if offset + chunk_size > total_posts else chunk_size
            if fetch_count <= 0: continue
                
            # Оповещаем UI о скачивании очередной пачки
            if progress_callback:
                progress_callback(
                    tag=tag, 
                    count=len(all_documents), 
                    status_text=f"Скачиваем посты (смещение {offset}/{total_posts})..."
                )
                
            params = {'owner_id': owner_id, 'count': fetch_count, 'offset': offset, 'access_token': VK_ACCESS_TOKEN, 'v': VK_API_VERSION}
            response = fetch_with_retry(url, params)
            
            if not response or 'error' in response: continue
                
            for post in reversed(response['response']['items']):
                if not is_valid_recipe(post): continue
                    
                text = post.get('text', '').strip()
                cleaned_ai_text = clean_text_for_ai(text)
                
                fingerprint = get_text_fingerprint(cleaned_ai_text)
                if fingerprint in seen_fingerprints: continue 
                seen_fingerprints.add(fingerprint)
                
                # Безопасное извлечение фото (если его нет, останется пустая строка "")
                image_url = ""
                if 'attachments' in post:
                    for att in post['attachments']:
                        if att['type'] == 'photo':
                            sizes = att['photo']['sizes']
                            largest = sorted(sizes, key=lambda x: x['width']*x['height'], reverse=True)[0]
                            image_url = largest['url']
                            break
                
                post_id = post['id']
                real_owner_id = post.get('owner_id', owner_id)
                post_url = f"https://vk.com/wall{real_owner_id}_{post_id}"
                stable_id = int(hashlib.md5(post_url.encode()).hexdigest()[:15], 16)
                
                all_documents.append({
                    'id': stable_id,
                    'tag': tag,
                    'url': post_url,
                    'text': cleaned_ai_text,
                    'image_url': image_url
                })
                
                # Оповещаем UI о добавлении нового уникального рецепта
                if progress_callback:
                    progress_callback(
                        tag=tag, 
                        count=len(all_documents), 
                        status_text=f"Нашли уникальный рецепт! Всего в этой сессии: {len(all_documents)}"
                    )
                    
            time.sleep(0.4) 
            
    # Финальный статус
    if progress_callback:
        progress_callback(
            tag="Завершено!", 
            count=len(all_documents), 
            status_text=f"Успешно собрано {len(all_documents)} качественных рецептов."
        )
        
    print(f"\nСбор завершен! Уникальных, качественных постов: {len(all_documents)}")
    return all_documents