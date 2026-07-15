# app.py
import streamlit as st
from parser import get_all_posts
from indexer import build_index
from searcher import search_documents, ask_ai_chef
from config import PUBLICS

# Настройка страницы
st.set_page_config(page_title="ИИ-Шеф: Поиск рецептов", page_icon="👨‍🍳", layout="centered")

st.title("👨‍🍳 Умная система рецептов")
st.write("Ищите лучшие рецепты из VK и создавайте идеальные блюда!")

# Создаем две вкладки на сайте
tab_search, tab_manage = st.tabs(["🔍 Поиск и Шеф", "⚙️ Управление базой"])

# =====================================================================
# ВКЛАДКА 1: ПОИСК И ОБЩЕНИЕ С ИИ
# =====================================================================
with tab_search:
    st.subheader("Что вы хотите приготовить?")
    
    # Строка поиска
    query = st.text_input("Введите запрос (например: 'нежный чизкейк' или 'ужин из курицы и кабачков'):", "")
    
    # Дополнительные настройки в выпадающем спойлере
    with st.expander("Дополнительные фильтры и настройки"):
        # Настройки векторного поиска
        public_names = ["Все паблики"] + [p[1] for p in PUBLICS]
        selected_public = st.selectbox("Искать в конкретном паблике:", public_names)
        limit = st.slider("Количество рецептов в выдаче:", min_value=1, max_value=5, value=3)
        
        st.markdown("---")
        
        # Настройки промпта для ИИ
        default_prompt = "Ты профессиональный повар. Используй ТОЛЬКО предложенные рецепты из контекста, чтобы ответить на запрос пользователя. " \
        "Скомпилируй лучший вариант, опиши шаги и дай список покупок. Если документы не отвечают на запрос пользователя- скажи об этом, не придумывай ответ."
        custom_prompt = st.text_area("Системный промпт (Инструкция для Шефа):", value=default_prompt, height=100)

    # Две кнопки для разных режимов поиска
    col1, col2 = st.columns(2)
    
    with col1:
        btn_regular = st.button("🔍 Обычный поиск (Ссылки)", use_container_width=True)
    with col2:
        btn_ai = st.button("🤖 Спросить Шефа (RAG)", use_container_width=True)

    tag_filter = None if selected_public == "Все паблики" else selected_public

    # РЕЖИМ 1: ОБЫЧНЫЙ ВЕКТОРНЫЙ ПОИСК
    if btn_regular and query:
        with st.spinner("Ищу лучшие рецепты..."):
            results = search_documents(query, limit=limit, tag_filter=tag_filter)
            
            if not results:
                st.warning("Ничего не найдено. Попробуйте изменить запрос.")
            
            for idx, hit in enumerate(results, 1):
                with st.container(border=True):
                    st.markdown(f"### [{idx}] Паблик: {hit.payload['tag']}")
                    st.markdown(f"🔗 **[Оригинальный пост в VK]({hit.payload['url']})**")
                    
                    if hit.payload.get('image_url'):
                        st.image(hit.payload['image_url'], use_container_width=True)
                        
                    text_preview = hit.payload['text']
                    if len(text_preview) > 400:
                        st.write(text_preview[:400] + "...")
                        with st.expander("Читать полностью"):
                            st.write(text_preview[400:])
                    else:
                        st.write(text_preview)

    # РЕЖИМ 2: RAG ПОИСК (DEEPSEEK)
    if btn_ai and query:
        with st.spinner("Ищу рецепты и отправляю ИИ-Шефу..."):
            results = search_documents(query, limit=limit, tag_filter=tag_filter)
            
            if not results:
                st.warning("В базе нет рецептов по этому запросу, Шефу не из чего готовить.")
            else:
                # Передаем кастомный промпт из интерфейса в backend
                ai_answer = ask_ai_chef(query, results, custom_prompt=custom_prompt)
                
                st.success("👨‍🍳 Вердикт ИИ-Шеф-повара:")
                st.markdown(ai_answer)
                
                st.markdown("---")
                st.caption("Рецепты из базы, которые использовал ИИ:")
                for hit in results:
                    st.markdown(f"- [{hit.payload['tag']}]({hit.payload['url']})")

# =====================================================================
# ВКЛАДКА 2: УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ
# =====================================================================
with tab_manage:
    st.subheader("⚙️ Панель управления базой данных")
    st.markdown("""
    Здесь вы можете запустить процесс принудительного обновления базы данных рецептов. 
    Скрипт подключится к указанным пабликам ВКонтакте, скачает свежие посты, 
    прогонит их через систему умных фильтров, векторизует и сохранит в Qdrant.
    """)
    
    # Информационный блок о текущих источниках
    with st.expander("📋 Список отслеживаемых сообществ (источников)", expanded=False):
        st.write("Рецепты собираются из следующих пабликов:")
        for owner_id, tag in PUBLICS:
            st.markdown(f"- **{tag}** (ID: `{owner_id}`)")
    
    st.warning("⚠️ Обновление базы данных может занять некоторое время в зависимости от установленных лимитов.")
    
# Кнопка запуска парсинга и индексации
    if st.button("🔄 Спарсить паблики и обновить индекс", type="primary", use_container_width=True):
        # Создаем пустой контейнер-индикатор для красивого вывода прогресса
        progress_placeholder = st.empty()
        
        # 1. Функция для мониторинга парсинга (VK)
        def update_parsing_progress(tag, count, status_text):
            with progress_placeholder.container(border=True):
                st.markdown("### 📊 Этап 1: Сбор данных из VK")
                col_tag, col_count = st.columns([2, 1])
                with col_tag:
                    st.markdown(f"**Активное сообщество:** `{tag}`")
                    st.markdown(f"*Действие:* {status_text}")
                with col_count:
                    st.metric(label="Собрано рецептов", value=count)

        # 2. Функция для мониторинга векторизации (ИИ)
        def update_vector_progress(percent, status_text):
            with progress_placeholder.container(border=True):
                st.markdown("### 🧠 Этап 2: Создание ИИ-векторов")
                st.markdown(f"**Статус:** {status_text}")
                st.progress(percent) # Отрисовываем полосу загрузки

        try:
            # Запускаем парсинг
            docs = get_all_posts(progress_callback=update_parsing_progress)
            
            if docs:
                # Плавно переключаем UI на показ процентов векторизации
                build_index(docs, progress_callback=update_vector_progress)
                
                # Очищаем временное табло прогресса и празднуем победу
                progress_placeholder.empty()
                st.success(f"🎉 База данных успешно обновлена! Всего уникальных постов в индексе: {len(docs)}")
                st.balloons()
            else:
                progress_placeholder.empty()
                st.error("❌ Не удалось собрать посты. Проверьте соединение с интернетом, лимиты или токен VK.")
                
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"💥 Произошла ошибка во время обновления: {str(e)}")