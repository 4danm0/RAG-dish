# indexer.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from config import QDRANT_PATH, COLLECTION_NAME, EMBEDDER_MODEL, API_KEY, API_BASE_URL

def build_index(docs, progress_callback=None):
    if not docs:
        print("Нет документов для индексации.")
        return

    client_api = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    client_qdrant = QdrantClient(path=QDRANT_PATH)

    # Определяем размерность векторов
    if progress_callback:
        progress_callback(0, "Определяем размерность нейросети...")
        
    test_emb = client_api.embeddings.create(model=EMBEDDER_MODEL, input=["test"]).data[0].embedding
    vector_size = len(test_emb)

    # Создаем коллекцию только в том случае, если её не существует
    if not client_qdrant.collection_exists(COLLECTION_NAME):
        client_qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
    
    texts = [doc['text'] for doc in docs]
    total_docs = len(texts)
    
    # Отправляем тексты пакетами по 32 штуки
    batch_size = 32
    embeddings = []
    
    for i in range(0, total_docs, batch_size):
        batch_texts = texts[i:i+batch_size]
        response = client_api.embeddings.create(model=EMBEDDER_MODEL, input=batch_texts)
        embeddings.extend([item.embedding for item in response.data])
        
        # Считаем проценты и отправляем в UI
        if progress_callback:
            processed = min(i + batch_size, total_docs)
            percent = int((processed / total_docs) * 100)
            progress_callback(percent, f"Векторизуем тексты: {processed} из {total_docs}...")

    if progress_callback:
        progress_callback(95, "Сохраняем векторы в базу Qdrant...")

    # Подготовка данных в Qdrant с использованием PointStruct
    points = []
    for idx, doc in enumerate(docs):
        points.append(
            PointStruct(
                id=doc['id'],
                vector=embeddings[idx],
                payload={
                    "tag": doc['tag'],
                    "url": doc['url'],
                    "text": doc['text'],
                    "image_url": doc['image_url']
                }
            )
        )

    client_qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    
    if progress_callback:
        progress_callback(100, "Индексация успешно завершена!")
    
    print("Индексация успешно завершена!")