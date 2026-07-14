# parser.py

import requests
import time
import re
import hashlib
from config import VK_ACCESS_TOKEN, VK_API_VERSION, PUBLICS, MIN_LIKES, MAX_POSTS_PER_GROUP

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
    if post.get('marked_as_ads', 0) == 1: return False
    if post.get('likes', {}).get('count', 0) < MIN_LIKES: return False
    
    text = post.get('text', '').strip()
    if len(text) < 150: return False
        
    text_lower = text.lower()
    bad_links = ['t.me/', 'vk.cc/', 'wildberries.ru', 'ozon.ru', 'aliexpress']
    if any(link in text_lower for link in bad_links): return False
        
    stop_phrases = ['erid', 'продолжение рецепта', 'полный рецепт', 'подпишись', 'промокод', 'сделай репост']
    if any(phrase in text_lower for phrase in stop_phrases): return False
        
    return True

def get_text_fingerprint(text):
    cleaned_text = re.sub(r'\W+', '', text.lower())
    return hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()

def clean_text_for_ai(text):
    text = re.sub(r'#\w+', '', text) 
    text = re.sub(r'[^\w\s\.,!?\-\:\(\)«»]', '', text) 
    return re.sub(r'\s+', ' ', text).strip()

def get_all_posts(max_posts_per_group=MAX_POSTS_PER_GROUP):
    all_documents = []
    chunk_size = 100 
    seen_fingerprints = set()
    
    for owner_id, tag in PUBLICS:
        print(f"\nНачинаем парсинг: {tag}...")
        url = 'https://api.vk.com/method/wall.get'
        
        init_params = {'owner_id': owner_id, 'count': 1, 'access_token': VK_ACCESS_TOKEN, 'v': VK_API_VERSION}
        init_response = fetch_with_retry(url, init_params)
        
        if not init_response or 'error' in init_response: continue
        total_posts = init_response['response']['count']
        if total_posts == 0: continue
            
        n_chunks = max_posts_per_group // chunk_size
        jump = chunk_size if total_posts <= max_posts_per_group else total_posts // n_chunks
        actual_chunks = (total_posts + chunk_size - 1) // chunk_size if total_posts <= max_posts_per_group else n_chunks
            
        for i in range(actual_chunks - 1, -1, -1):
            offset = i * jump
            fetch_count = min(chunk_size, total_posts - offset) if offset + chunk_size > total_posts else chunk_size
            if fetch_count <= 0: continue
                
            params = {'owner_id': owner_id, 'count': fetch_count, 'offset': offset, 'access_token': VK_ACCESS_TOKEN, 'v': VK_API_VERSION}
            response = fetch_with_retry(url, params)
            
            if not response or 'error' in response: continue
                
            for post in reversed(response['response']['items']):
                if not is_valid_recipe(post): continue
                    
                text = post.get('text', '').strip()
                fingerprint = get_text_fingerprint(text)
                if fingerprint in seen_fingerprints: continue 
                seen_fingerprints.add(fingerprint)
                
                image_url = ""
                if 'attachments' in post:
                    for att in post['attachments']:
                        if att['type'] == 'photo':
                            sizes = att['photo']['sizes']
                            largest = sorted(sizes, key=lambda x: x['width']*x['height'], reverse=True)[0]
                            image_url = largest['url']
                            break
                
                post_url = f"https://vk.com/wall{owner_id}_{post['id']}"
                
                stable_id = int(hashlib.md5(post_url.encode()).hexdigest()[:15], 16)
                
                all_documents.append({
                    'id': stable_id,
                    'tag': tag,
                    'url': post_url,
                    'text': clean_text_for_ai(text),
                    'image_url': image_url
                })
            time.sleep(0.4) 
    print(f"\nСбор завершен! Уникальных постов: {len(all_documents)}")
    return all_documents