# indexer.py

import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from config import QDRANT_PATH, COLLECTION_NAME, EMBEDDER_MODEL, API_KEY, API_BASE_URL

def build_index(documents):
    if not documents: return

    start_time = time.time()
    client_api = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    client_qdrant = QdrantClient(path=QDRANT_PATH)

    if not client_qdrant.collection_exists(COLLECTION_NAME):
        client_qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )

    print(f"Индексация. Всего документов: {len(documents)}")
    batch_size = 50
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        texts = [doc['text'] for doc in batch_docs]
        
        try:
            response = client_api.embeddings.create(model=EMBEDDER_MODEL, input=texts)
            points = []
            for j, doc in enumerate(batch_docs):
                points.append(PointStruct(
                    id=doc['id'],
                    vector=response.data[j].embedding,
                    payload={
                        "tag": doc["tag"],
                        "url": doc["url"],
                        "text": doc["text"],
                        "image_url": doc["image_url"]
                    }
                ))
            client_qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"  Сохранено: {min(i + batch_size, len(documents))} / {len(documents)}")
        except Exception as e:
            print(f"  [Ошибка API]: {e}")

    print(f"⏱ Время: {int((time.time() - start_time) // 60)} мин {int((time.time() - start_time) % 60)} сек.")