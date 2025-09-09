"""Современный Streamlit интерфейс для PostgreSQL SQL Analyzer."""

import streamlit as st
from app.config import settings
from app.ssh_tunnel import ssh_tunnel

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


def test_db_connection(dsn: str) -> tuple[bool, str]:
    """Тестирует подключение к базе данных."""
    try:
        from app.analyzer import SQLAnalyzer
        analyzer = SQLAnalyzer(dsn)
        # Пробуем получить простую информацию о базе
        _ = analyzer.analyze_sql("SELECT 1 as test;")
        return True, "✅ Подключение успешно! База данных доступна."
    except Exception as e:
        return False, f"❌ Ошибка подключения: {str(e)}"


def handle_database_connection(
    connection_type: str,
    dsn: str,
    ssh_host: str,
    ssh_user: str,
    ssh_key_path: str,
    port: int,
    username: str,
    password: str
) -> bool:
    """Обрабатывает подключение к базе данных с созданием SSH туннеля при необходимости"""
    with st.spinner("Подключение к базе данных..."):
        try:
            # Создаем SSH туннель, если нужно
            if connection_type == "SSH туннель" and not ssh_tunnel.is_tunnel_active():
                _ = st.info("🔐 Создание SSH туннеля...")
                if ssh_tunnel.create_tunnel(
                    remote_host='localhost',  # PostgreSQL на удаленном сервере
                    remote_port=5433,  # Порт PostgreSQL на сервере
                    local_port=port,  # Локальный порт
                    ssh_host=ssh_host,
                    ssh_user=ssh_user,
                    ssh_key_path=ssh_key_path
                ):
                    _ = st.success("✅ SSH туннель создан успешно")
                else:
                    _ = st.error("❌ Не удалось создать SSH туннель")
                    return False

            # Показываем DSN для отладки (без пароля)
            dsn_debug = dsn.replace(f"password={password}", "password=***") if password else dsn
            _ = st.info(f"🔍 Подключение с DSN: {dsn_debug}")

            # Тестируем подключение к БД
            success, message = test_db_connection(dsn)
            if success:
                _ = st.success("✅ Подключено к БД")
                st.session_state.db_connected = True
                st.session_state.connection_dsn = dsn
                return True
            else:
                _ = st.error(f"❌ Ошибка подключения: {message}")
                st.session_state.db_connected = False

                # Дополнительные советы по устранению неполадок
                if "подключение к серверу" in message.lower():
                    _ = st.info("💡 **Советы по устранению неполадок:**\n"
                                + "- Убедитесь, что PostgreSQL запущен\n"
                                + "- Проверьте правильность хоста и порта\n"
                                + "- Убедитесь, что сервер принимает подключения")
                elif "role" in message.lower() and "does not exist" in message.lower():
                    _ = st.error("👤 **Проблема с пользователем PostgreSQL:**\n"
                                 + f"Пользователь '{username}' не существует в базе данных")
                    _ = st.info("🔧 **Решение:**\n"
                                + "1. Создайте пользователя: `sudo -u postgres createuser {username}`\n"
                                + "2. Или используйте существующего пользователя 'postgres'\n"
                                + "3. Проверьте пользователей: `sudo -u postgres psql -c \"\\du\"`")
                elif "password authentication failed" in message.lower():
                    _ = st.error("🔐 **Ошибка аутентификации:**\n"
                                 + "Неверный пароль для пользователя")
                    _ = st.info("🔧 **Решение:**\n"
                                + "1. Проверьте правильность пароля\n"
                                + "2. Сбросьте пароль: `sudo -u postgres psql -c \"ALTER USER {username} PASSWORD 'new_password';\"`")
                return False
        except Exception as e:
            _ = st.error(f"❌ Ошибка: {str(e)}")
            st.session_state.db_connected = False
            return False


def _show_welcome_screen() -> None:
    """Показывает красивый экран приветствия когда БД не подключена."""
    _ = st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    ">
        <h1 style="font-size: 3rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🐘 PostgreSQL SQL Analyzer
        </h1>
        <p style="font-size: 1.3rem; margin: 1rem 0; opacity: 0.9;">
            Интеллектуальный анализ производительности SQL-запросов
        </p>
        <div style="
            background: rgba(255,255,255,0.1);
            padding: 2rem;
            border-radius: 10px;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
        ">
            <h2 style="margin: 0 0 1rem 0; font-size: 1.5rem;">🚀 Готов к работе!</h2>
            <p style="margin: 0; font-size: 1.1rem;">
                Для начала анализа подключитесь к базе данных PostgreSQL
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Карточки с возможностями
    col1, col2, col3 = st.columns(3)

    with col1:
        _ = st.markdown("""
        <div style="
            background: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #4CAF50;
        ">
            <h3 style="color: #4CAF50; margin: 0 0 1rem 0;">🔍 Explain анализ</h3>
            <p style="color: #666; margin: 0;">
                Анализ планов выполнения SQL-запросов с AI-рекомендациями
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        _ = st.markdown("""
        <div style="
            background: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #2196F3;
        ">
            <h3 style="color: #2196F3; margin: 0 0 1rem 0;">📊 Статистики</h3>
            <p style="color: #666; margin: 0;">
                Мониторинг производительности и анализ нагрузки
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        _ = st.markdown("""
        <div style="
            background: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #FF9800;
        ">
            <h3 style="color: #FF9800; margin: 0 0 1rem 0;">🤖 AI помощник</h3>
            <p style="color: #666; margin: 0;">
                Интеллектуальные рекомендации по оптимизации
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Инструкция по подключению
    _ = st.markdown("""
    <div style="
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
        border: 1px solid #e9ecef;
    ">
        <h3 style="color: #495057; margin: 0 0 1rem 0;">📋 Как начать работу:</h3>
        <ol style="color: #6c757d; margin: 0; padding-left: 2rem;">
            <li>Настройте параметры подключения в боковой панели</li>
            <li>Нажмите кнопку "🔌 Подключиться к БД"</li>
            <li>Выберите нужную вкладку для анализа</li>
            <li>Наслаждайтесь мощными возможностями анализа!</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def main() -> None:
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
    _ = st.markdown("""
    <div class="main-header">
        <h1>🐘 PostgreSQL SQL Analyzer</h1>
        <p style="font-size: 1.2rem; margin: 0;">Инструмент для превентивного анализа SQL-запросов к PostgreSQL</p>
        <p style="font-size: 1rem; margin: 0; opacity: 0.9;">Анализируйте производительность до выполнения запросов</p>
    </div>
    """, unsafe_allow_html=True)

    # Боковая панель с настройками подключения
    with st.sidebar:
        _ = st.markdown("## ⚙️ Настройки подключения")

        # Настройки подключения к базе данных
        _ = st.markdown("### 🔌 Подключение к PostgreSQL")

        # Тип подключения
        connection_type = st.selectbox(
            "Тип подключения",
            ["SSH туннель", "Прямое подключение", "Mock режим"],
            index=0,
            help="Выберите способ подключения к базе данных"
        )

        if connection_type == "Mock режим":
            _ = st.info("🎭 Используется тестовый режим без реального подключения к БД")
            mock_mode = True
            dsn = ""
            host = "localhost"
            port = 5433
            database = "postgres"
            username = "readonly_user"
            password = "skripka_user"
        else:
            mock_mode = False

            # Используем настройки из .env по умолчанию
            host = settings.DB_HOST
            port = settings.DB_PORT
            database = settings.DB_NAME
            username = settings.DB_USER
            password = settings.DB_PASSWORD
            ssh_host = settings.SSH_HOST
            ssh_port = settings.SSH_PORT
            ssh_user = settings.SSH_USER
            ssh_key_path = settings.SSH_KEY_PATH

            # SSH настройки
            if connection_type == "SSH туннель":
                _ = st.markdown("#### 🔐 SSH туннель")

                # Показываем настройки из .env
                col1, col2 = st.columns(2)
                with col1:
                    _ = st.text_input("SSH хост", value=ssh_host, disabled=True, help="Из .env файла")
                    _ = st.text_input("SSH пользователь", value=ssh_user, disabled=True, help="Из .env файла")
                with col2:
                    _ = st.number_input("SSH порт", value=ssh_port, disabled=True, help="Из .env файла")
                    _ = st.text_input("SSH ключ", value=ssh_key_path, disabled=True, help="Из .env файла")

            # Параметры подключения к БД
            _ = st.markdown("#### 🗄️ База данных")

            # Показываем настройки из .env
            col1, col2 = st.columns(2)
            with col1:
                _ = st.text_input("Хост БД", value=host, disabled=True, help="Из .env файла")
                _ = st.text_input("База данных", value=database, disabled=True, help="Из .env файла")
            with col2:
                _ = st.number_input("Порт БД", value=port, disabled=True, help="Из .env файла")
                _ = st.text_input("Пользователь", value=username, disabled=True, help="Из .env файла")

            # Формируем DSN
            if connection_type == "SSH туннель":
                # Для SSH туннеля используем localhost и локальный порт
                dsn = (f"host=localhost port={port} dbname={database} "
                       f"user={username} password={password} connect_timeout=10")
            else:
                # Для прямого подключения используем указанный хост
                dsn = (f"host={host} port={port} dbname={database} "
                       f"user={username} password={password} connect_timeout=10")

            # Отладочная информация DSN (скрываем пароль)
            dsn_debug = dsn.replace(f"password={password}", "password=***") if password else dsn
            _ = st.text_input("DSN (для отладки)", value=dsn_debug, disabled=True,
                              help="Строка подключения к базе данных")

        # Настройки PostgreSQL
        _ = st.markdown("### ⚙️ Настройки PostgreSQL")
        col1, col2 = st.columns(2)
        with col1:
            _ = st.number_input("work_mem (MB)", value=4, min_value=1,
                                max_value=2048, help="Память для операций сортировки")
        with col2:
            _ = st.number_input("shared_buffers (MB)", value=128,
                                min_value=1, max_value=8192, help="Буферный кеш")

        _ = st.number_input("effective_cache_size (GB)", value=4,
                            min_value=1, max_value=64, help="Размер кеша ОС")

        # Статус подключения убран по требованию пользователя

        # Настройки LLM в отдельном блоке
        with st.expander("🤖 Настройки AI", expanded=True):
            # Провайдер LLM
            llm_provider = st.selectbox(
                "Провайдер AI",
                ["OpenAI", "Anthropic", "Локальный LLM", "Отключить AI"],
                index=0 if settings.AI_PROVIDER == "openai" else 3,
                help="Выберите провайдера для AI-рекомендаций"
            )

            if llm_provider == "OpenAI":
                openai_api_key = st.text_input(
                    "OpenAI API Key",
                    value=settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else "",
                    type="password",
                    help="API ключ OpenAI (из .env файла)"
                )

                # Актуальные модели OpenAI
                models = [
                    "gpt-4o-mini",  # Самая доступная модель
                    "gpt-4o",       # Новая мультимодальная модель
                    "gpt-4-turbo",  # Быстрая модель GPT-4
                    "gpt-4",        # Стандартная GPT-4
                    "gpt-3.5-turbo"  # Экономичная модель
                ]
                default_model_index = models.index(settings.OPENAI_MODEL) if settings.OPENAI_MODEL in models else 0
                openai_model = st.selectbox(
                    "Модель OpenAI",
                    models,
                    index=default_model_index,
                    help="Выберите модель OpenAI (gpt-4o-mini рекомендуется для баланса качества и стоимости)"
                )

                temperature = st.slider(
                    "Температура",
                    min_value=0.0,
                    max_value=2.0,
                    value=settings.OPENAI_TEMPERATURE,
                    step=0.1,
                    help="Креативность ответов (0.0 - детерминированно, 2.0 - очень креативно)"
                )

                enable_ai = settings.ENABLE_AI_RECOMMENDATIONS
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
                _ = st.info("🚫 AI-рекомендации отключены")

                # Сохраняем в session_state для использования в других модулях
                st.session_state['enable_ai'] = enable_ai
                st.session_state['ai_provider'] = llm_provider

            # Настройки прокси (всегда включены по умолчанию)
            _ = st.markdown("#### 🌐 Настройки прокси")
            enable_proxy = st.checkbox(
                "Использовать SOCKS5 прокси",
                value=True,  # По умолчанию включен
                help="SOCKS5 прокси для доступа к внешним AI сервисам"
            )

            if enable_proxy:
                proxy_host = st.text_input(
                    "Хост прокси",
                    value="localhost",
                    help="Адрес SOCKS5 прокси сервера"
                )
                proxy_port = st.number_input(
                    "Порт прокси",
                    value=1080,
                    min_value=1,
                    max_value=65535,
                    help="Порт SOCKS5 прокси сервера"
                )
            else:
                proxy_host = "localhost"
                proxy_port = 1080

            # Сохраняем настройки прокси
            st.session_state['enable_proxy'] = enable_proxy
            st.session_state['proxy_host'] = proxy_host
            st.session_state['proxy_port'] = proxy_port

            # Дополнительные настройки AI
            if enable_ai:
                _ = st.markdown("#### 🎯 Дополнительные настройки AI")
                confidence_threshold = st.slider(
                    "Порог уверенности",
                    min_value=0.0,
                    max_value=1.0,
                    value=settings.AI_CONFIDENCE_THRESHOLD,
                    step=0.1,
                    help="Минимальная уверенность для показа рекомендаций"
                )
                st.session_state['ai_confidence_threshold'] = confidence_threshold
            else:
                st.session_state['ai_confidence_threshold'] = settings.AI_CONFIDENCE_THRESHOLD

        # Кнопка подключения к БД (в конце sidebar)
        _ = st.markdown("---")
        _ = st.markdown("#### 🔌 Подключение к БД")

        if st.button("🔌 Подключиться к БД", use_container_width=True, type="primary"):
            # Вызываем функцию обработки подключения
            _ = handle_database_connection(connection_type, dsn, ssh_host, ssh_user,
                                           ssh_key_path, port, username, password)
        else:
            st.session_state.db_connected = False


        # Дополнительная информация
        with st.expander("ℹ️ О приложении"):
            _ = st.markdown("""
            **PostgreSQL SQL Analyzer** - это мощный инструмент для:
            
            • 🔍 Анализа планов выполнения SQL
            • 📊 Мониторинга производительности
            • 🤖 AI-рекомендаций по оптимизации
            • 📈 Визуализации метрик
            
            Поддерживает PostgreSQL 12+ и современные AI-модели.
            """)

    # Показываем статус подключения
    if 'db_connected' in st.session_state and st.session_state.db_connected:
        _ = show_connection_status(dsn)
    else:
        # Красивое окно для главной страницы когда БД не подключена
        _show_welcome_screen()
        return

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
