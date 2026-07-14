# searcher.py

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
from config import QDRANT_PATH, COLLECTION_NAME, EMBEDDER_MODEL, API_KEY, API_BASE_URL, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

def search_documents(query, limit=3, tag_filter=None):
    client_api = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    
    response = client_api.embeddings.create(model=EMBEDDER_MODEL, input=[query])
    query_vector = response.data[0].embedding
    
    client_qdrant = QdrantClient(path=QDRANT_PATH)
    
    q_filter = None
    if tag_filter:
        q_filter = Filter(must=[FieldCondition(key="tag", match=MatchValue(value=tag_filter))])
        
    results = client_qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=q_filter,
        limit=limit
    )
    return results

def ask_ai_chef(query, search_results):
    if not search_results:
        return "К сожалению, в базе нет подходящих рецептов."
        
    context = ""
    for idx, hit in enumerate(search_results, 1):
        context += f"Рецепт {idx} (Паблик: {hit.payload['tag']}):\n{hit.payload['text']}\n\n"
        
    system_prompt = "Ты профессиональный повар. Используй ТОЛЬКО предложенные рецепты из контекста, чтобы ответить на запрос пользователя. Скомпилируй лучший вариант, опиши шаги и дай список покупок."
    user_prompt = f"Запрос пользователя: {query}\n\nКонтекст (рецепты из ВК):\n{context}"
    
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    
    print("Шеф-повар DeepSeek думает...")
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content