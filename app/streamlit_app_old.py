"""Современный Streamlit интерфейс для PostgreSQL SQL Analyzer."""

import streamlit as st

from app.config import get_default_config
from app.ui import (
    apply_custom_styles,
    show_connection_status,
    show_db_overview_tab,
    show_db_config_tab,
    show_statistics_tab,
    show_explain_analysis_tab,
    show_metrics_tab,
    show_logging_tab,
    show_help_tab
)


def test_db_connection(dsn):
    """Тестирует подключение к базе данных."""
    try:
        from app.analyzer import SQLAnalyzer
        analyzer = SQLAnalyzer(dsn, mock_mode=False)
        # Пробуем получить простую информацию о базе
        test_result = analyzer.analyze_sql("SELECT 1 as test;")
        return True, "✅ Подключение успешно! База данных доступна."
    except Exception as e:
        return False, f"❌ Ошибка подключения: {str(e)}"


def main():
    """Основная функция приложения."""
    # Настройка страницы
    st.set_page_config(
        page_title="PostgreSQL SQL Analyzer",
        page_icon="🐘",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo/postgres-sql-analyzer',
            'Report a bug': "https://github.com/your-repo/postgres-sql-analyzer/issues",
            'About': "# PostgreSQL SQL Analyzer\nИнструмент для превентивного анализа SQL-запросов"
        }
    )

    # Применяем кастомные стили
    apply_custom_styles()

    # Заголовок приложения
    st.markdown("""
    <div class="main-header">
        <h1>🐘 PostgreSQL SQL Analyzer</h1>
        <p style="font-size: 1.2rem; margin: 0;">Инструмент для превентивного анализа SQL-запросов к PostgreSQL</p>
        <p style="font-size: 1rem; margin: 0; opacity: 0.9;">Анализируйте производительность до выполнения запросов</p>
    </div>
    """, unsafe_allow_html=True)

    # Боковая панель с настройками подключения
    with st.sidebar:
        st.markdown("## ⚙️ Настройки подключения")

        # Настройки подключения к базе данных
        st.markdown("### 🔌 Подключение к PostgreSQL")

        # Тип подключения
        connection_type = st.selectbox(
            "Тип подключения",
            ["SSH туннель", "Прямое подключение", "Mock режим"],
            index=0,
            help="Выберите способ подключения к базе данных"
        )

        if connection_type == "Mock режим":
            st.info("🎭 Используется тестовый режим без реального подключения к БД")
            mock_mode = True
            dsn = ""
            host = "localhost"
            port = 5433
            database = "postgres"
            username = "readonly_user"
            password = "skripka_user"
        else:
            mock_mode = False

            # SSH настройки (по умолчанию)
            if connection_type == "SSH туннель":
                st.markdown("#### 🔐 SSH туннель")
                col1, col2 = st.columns(2)
                with col1:
                    ssh_host = st.text_input("SSH хост", value="193.246.150.18", help="IP адрес SSH сервера")
                with col2:
                    ssh_port = st.number_input("SSH порт", value=22, min_value=1, max_value=65535)

                ssh_user = st.text_input("SSH пользователь", value="skripka", help="Имя пользователя SSH")
                ssh_key_path = st.text_input("Путь к SSH ключу", value="~/.ssh/id_rsa", help="Путь к приватному ключу")

                st.info("🔗 SSH туннель: ssh -v -i ~/.ssh/id_rsa skripka@193.246.150.18")

            # Параметры подключения к БД
            st.markdown("#### 🗄️ База данных")
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Хост БД", value="localhost", help="IP адрес или домен сервера БД")
            with col2:
                port = st.number_input("Порт БД", value=5433, min_value=1, max_value=65535, help="Порт PostgreSQL")

            database = st.text_input("База данных", value="postgres", help="Имя базы данных")

            # Пользователи для подключения
            user_type = st.selectbox(
                "Тип пользователя",
                ["readonly_user (только чтение)", "admin_user (администратор)",
                                 "postgres (суперпользователь)", "Другой"],
                index=0,
                help="Выберите тип пользователя для подключения"
            )

            if user_type == "readonly_user (только чтение)":
                username = "readonly_user"
                password = "skripka_user"
                st.info("👤 readonly_user - безопасный доступ только для чтения")
            elif user_type == "admin_user (администратор)":
                username = "admin_user"
                password = "skripka_admin"
                st.info("👨‍💼 admin_user - административные права")
            elif user_type == "postgres (суперпользователь)":
                username = "postgres"
                password = "skripka_super"
                st.info("🔑 postgres - полные права суперпользователя")
            else:
                username = st.text_input("Пользователь", value="", help="Имя пользователя")
            password = st.text_input("Пароль", type="password", help="Пароль пользователя")

            # Формируем DSN
            if connection_type == "SSH туннель":
                # Для SSH туннеля используем localhost и локальный порт
                dsn = f"host=localhost port={port} dbname={database} user={username} password={password}"
            else:
                # Для прямого подключения используем указанный хост
                dsn = f"host={host} port={port} dbname={database} user={username} password={password}"

        # Настройки PostgreSQL
        st.markdown("### ⚙️ Настройки PostgreSQL")
        col1, col2 = st.columns(2)
        with col1:
            work_mem = st.number_input("work_mem (MB)", value=4, min_value=1,
                                       max_value=2048, help="Память для операций сортировки")
        with col2:
            shared_buffers = st.number_input("shared_buffers (MB)", value=128,
                                             min_value=1, max_value=8192, help="Буферный кеш")

        effective_cache_size = st.number_input("effective_cache_size (GB)", value=4,
                                               min_value=1, max_value=64, help="Размер кеша ОС")

        # Кнопка подключения к БД
        if not mock_mode and connection_type != "Mock режим":
            if st.button("🔌 Подключиться к БД", use_container_width=True, type="primary"):
                with st.spinner("Подключение к базе данных..."):
                    try:
                        if connection_type == "SSH туннель":
                            st.info("🔐 Создание SSH туннеля...")

                        # Тестируем подключение к БД
                        success, message = test_db_connection(dsn)
                        if success:
                            st.success("✅ Подключено к БД")
                            st.session_state.db_connected = True
                        else:
                            st.error("❌ Ошибка подключения")
                            st.session_state.db_connected = False
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
                        st.session_state.db_connected = False
            else:
                st.session_state.db_connected = False

        # Статус подключения
        if 'db_connected' in st.session_state:
            if st.session_state.db_connected:
                st.success("🟢 База данных подключена")
            else:
                st.error("🔴 База данных не подключена")
        else:
            st.info("⚪ Статус подключения неизвестен")

        # Настройки LLM
        st.markdown("### 🤖 Настройки AI")

        # Провайдер LLM
        llm_provider = st.selectbox(
            "Провайдер AI",
            ["OpenAI", "Anthropic", "Локальный LLM", "Отключить AI"],
            index=0,
            help="Выберите провайдера для AI-рекомендаций"
        )

        if llm_provider == "OpenAI":
            openai_api_key = st.text_input(
                "OpenAI API Key",
                value="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",
                type="password",
                help="API ключ OpenAI"
            )

            # Актуальные модели OpenAI
                openai_model = st.selectbox(
                "Модель OpenAI",
                [
                    "gpt-4o-mini",  # Самая доступная модель
                    "gpt-4o",       # Новая мультимодальная модель
                    "gpt-4-turbo",  # Быстрая модель GPT-4
                    "gpt-4",        # Стандартная GPT-4
                    "gpt-3.5-turbo"  # Экономичная модель
                ],
                    index=0,
                help="Выберите модель OpenAI (gpt-4o-mini рекомендуется для баланса качества и стоимости)"
                )

            temperature = st.slider(
                    "Температура",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1,
                help="Креативность ответов (0.0 - детерминированно, 2.0 - очень креативно)"
            )

            enable_ai = True
            anthropic_api_key = ""
            local_llm_url = ""
            local_llm_model = ""

            # Сохраняем в session_state для использования в других модулях
            st.session_state['enable_ai'] = enable_ai
            st.session_state['ai_provider'] = llm_provider
                    st.session_state['openai_api_key'] = openai_api_key
                    st.session_state['openai_model'] = openai_model
            st.session_state['openai_temperature'] = temperature

        elif llm_provider == "Anthropic":
                anthropic_api_key = st.text_input(
                "Anthropic API Key",
                value="",
                    type="password",
                help="API ключ Anthropic"
                )

                anthropic_model = st.selectbox(
                "Модель Anthropic",
                [
                    "claude-3-5-sonnet-20241022",  # Самая новая и мощная
                    "claude-3-5-sonnet-20240620",  # Предыдущая версия
                    "claude-3-opus-20240229",      # Самая мощная
                    "claude-3-sonnet-20240229",    # Баланс качества и скорости
                    "claude-3-haiku-20240307"      # Самая быстрая
                ],
                index=1,
                    help="Выберите модель Anthropic"
                )

            temperature = st.slider(
                "Температура", 
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Креативность ответов"
            )
            
            enable_ai = True
            openai_api_key = ""
            openai_model = "gpt-4o-mini"
            local_llm_url = ""
            local_llm_model = ""
            
            # Сохраняем в session_state для использования в других модулях
            st.session_state['enable_ai'] = enable_ai
            st.session_state['ai_provider'] = llm_provider
            st.session_state['anthropic_api_key'] = anthropic_api_key
            st.session_state['anthropic_model'] = anthropic_model
            st.session_state['anthropic_temperature'] = temperature
            
        elif llm_provider == "Локальный LLM":
            local_llm_url = st.text_input(
                "URL локального LLM", 
                value="http://localhost:11434",
                help="URL сервера локального LLM (например, Ollama)"
            )
            
            local_llm_model = st.selectbox(
                "Модель локального LLM",
                [
                    "llama3.1:8b",      # Llama 3.1 8B
                    "llama3.1:70b",     # Llama 3.1 70B
                    "llama3:8b",        # Llama 3 8B
                    "llama3:70b",       # Llama 3 70B
                    "codellama:7b",     # Code Llama 7B
                    "codellama:13b",    # Code Llama 13B
                    "mistral:7b",       # Mistral 7B
                    "qwen:7b",          # Qwen 7B
                    "custom"            # Пользовательская модель
                ],
                index=0,
                help="Выберите модель локального LLM"
            )
            
            if local_llm_model == "custom":
                local_llm_model = st.text_input("Имя модели", value="", help="Введите имя пользовательской модели")
            
            temperature = st.slider(
                "Температура", 
                min_value=0.0, 
                max_value=2.0, 
                value=0.7, 
                step=0.1,
                help="Креативность ответов"
            )
            
            enable_ai = True
            openai_api_key = ""
            openai_model = "gpt-4o-mini"
            anthropic_api_key = ""
            
            # Сохраняем в session_state для использования в других модулях
            st.session_state['enable_ai'] = enable_ai
            st.session_state['ai_provider'] = llm_provider
            st.session_state['local_llm_url'] = local_llm_url
            st.session_state['local_llm_model'] = local_llm_model
            st.session_state['local_llm_temperature'] = temperature
            
        else:  # Отключить AI
            enable_ai = False
            openai_api_key = ""
            openai_model = "gpt-4o-mini"
            anthropic_api_key = ""
            local_llm_url = ""
            local_llm_model = ""
            temperature = 0.7
            st.info("🚫 AI-рекомендации отключены")
            
            # Сохраняем в session_state для использования в других модулях
            st.session_state['enable_ai'] = enable_ai
            st.session_state['ai_provider'] = llm_provider
        
        # Дополнительные настройки AI
        if enable_ai:
            st.markdown("#### 🎯 Дополнительные настройки AI")
            ai_confidence_threshold = st.slider(
                "Порог уверенности", 
                min_value=0.0, 
                max_value=1.0, 
                value=0.7, 
                step=0.1,
                help="Минимальная уверенность для показа рекомендаций"
            )
        else:
            ai_confidence_threshold = 0.7
        
    
    # Проверяем подключение
    if not mock_mode and (not dsn or not all([host, database, username])):
        st.warning("⚠️ Заполните все обязательные поля подключения в боковой панели")
        return
    
    # Показываем статус подключения
    show_connection_status(dsn)
    
    # Основные вкладки
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🗄️ Обзор БД", 
        "⚙️ Конфигурация БД", 
        "📊 Статистики", 
        "🔍 Explain анализ", 
        "📈 Метрики",
        "📝 Логирование",
        "❓ Помощь"
    ])
    
    # Конфигурация для анализа
    custom_config = {
        "work_mem": work_mem,
        "shared_buffers": shared_buffers,
        "effective_cache_size": effective_cache_size * 1024,  # Конвертируем в MB
        "large_table_threshold": 1000000,
        "expensive_query_threshold": 1000.0,
        "slow_query_threshold": 100.0,
        "enable_ai_recommendations": enable_ai,
        "ai_provider": llm_provider.lower(),
        "ai_confidence_threshold": ai_confidence_threshold,
        "openai_api_key": openai_api_key,
        "openai_model": openai_model,
        "openai_temperature": temperature,
        "anthropic_api_key": anthropic_api_key,
        "anthropic_model": anthropic_model if llm_provider == "Anthropic" else "claude-3-5-sonnet-20240620",
        "local_llm_url": local_llm_url,
        "local_llm_model": local_llm_model
    }
    
    with tab1:
        show_db_overview_tab(dsn, mock_mode)
    
    with tab2:
        show_db_config_tab(dsn, mock_mode)
    
    with tab3:
        show_statistics_tab(dsn, mock_mode)
    
    with tab4:
        show_explain_analysis_tab(dsn, mock_mode)
    
    with tab5:
        show_metrics_tab(dsn, mock_mode)
    
    with tab6:
        show_logging_tab(dsn, mock_mode)
    
    with tab7:
        show_help_tab()


if __name__ == "__main__":
    main()
