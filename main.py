# main.py
from parser import get_all_posts
from indexer import build_index
from searcher import search_documents, ask_ai_chef

def main():
    while True:
        print("\n--- СИСТЕМА ИИ-РЕЦЕПТОВ ---")
        print("1. Спарсить паблики и обновить базу")
        print("2. Обычный векторный поиск (Ссылки)")
        print("3. Спросить ИИ-Шефа (Режим RAG)")
        print("4. Выход")
        
        choice = input("Ваш выбор: ")
        
        if choice == "1":
            docs = get_all_posts()
            build_index(docs)
            
        elif choice == "2":
            query = input("Что ищем?: ")
            results = search_documents(query)
            for idx, hit in enumerate(results, 1):
                print(f"\n[{idx}] {hit.payload['tag']} | Ссылка: {hit.payload['url']}")
                if hit.payload['image_url']: print(f"Фото: {hit.payload['image_url']}")
                print(f"{hit.payload['text'][:200]}...")
                
        elif choice == "3":
            query = input("Что приготовить?: ")
            results = search_documents(query, limit=3)
            answer = ask_ai_chef(query, results)
            
            print("\n" + "="*40)
            print("👨‍🍳 ОТВЕТ ИИ-ШЕФА:")
            print("="*40)
            print(answer)
            print("="*40)
            print("Источники:")
            for hit in results:
                print(f"- {hit.payload['url']}")
                
        elif choice == "4":
            break

if __name__ == "__main__":
    main()