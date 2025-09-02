"""Современный Streamlit интерфейс для PostgreSQL SQL Analyzer."""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

from app.analyzer import SQLAnalyzer
from app.config import get_default_config

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

# CSS стили для улучшения внешнего вида
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .connection-status {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .connection-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .connection-error {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    
    .stButton > button {
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def test_database_connection(dsn):
    """Тестирует подключение к базе данных."""
    try:
        analyzer = SQLAnalyzer(dsn, mock_mode=False)
        # Пробуем получить простую информацию о базе
        test_result = analyzer.analyze_sql("SELECT 1 as test;")
        return True, "✅ Подключение успешно! База данных доступна."
    except Exception as e:
        return False, f"❌ Ошибка подключения: {str(e)}"

def test_openai_connection(api_key):
    """Тестирует подключение к OpenAI API."""
    try:
        import openai
        openai.api_key = api_key
        # Пробуем получить список моделей
        models = openai.Model.list()
        return True
    except Exception as e:
        return False

def test_anthropic_connection(api_key):
    """Тестирует подключение к Anthropic API."""
    try:
        import requests
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        response = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False

def test_local_llm_connection(url, model):
    """Тестирует подключение к локальному LLM."""
    try:
        import requests
        # Пробуем Ollama формат
        try:
            data = {"model": model, "prompt": "test", "stream": False}
            response = requests.post(f"{url}/api/generate", json=data, timeout=10)
            return response.status_code == 200
        except:
            # Пробуем LM Studio формат
            data = {"model": model, "messages": [{"role": "user", "content": "test"}]}
            response = requests.post(f"{url}/v1/chat/completions", json=data, timeout=10)
            return response.status_code == 200
    except Exception as e:
        return False

def main():
    """Основная функция Streamlit приложения."""
    
    # Заголовок с градиентом
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
        
        # Режим работы
        st.markdown("### 🔧 Режим работы")
        mock_mode = st.checkbox(
            "Mock режим (без подключения к БД)", 
            value=False,
            help="Включите для демонстрации без реального подключения к базе данных"
        )
        
        # Настройки подключения к базе данных
        if not mock_mode:
            st.markdown("### 🔌 Подключение к PostgreSQL")
            
            # Параметры подключения
            host = st.text_input("Хост", value="localhost", help="IP адрес или домен сервера")
            port = st.number_input("Порт", value=5432, min_value=1, max_value=65535, help="Порт PostgreSQL")
            database = st.text_input("База данных", value="postgres", help="Имя базы данных")
            username = st.text_input("Пользователь", value="postgres", help="Имя пользователя")
            password = st.text_input("Пароль", type="password", help="Пароль пользователя")
            
            # Формируем DSN
            dsn = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            
            # Кнопка тестирования подключения
            if st.button("🔍 Тестировать подключение", use_container_width=True):
                with st.spinner("🔍 Тестирую подключение к базе данных..."):
                    success, message = test_database_connection(dsn)
                    if success:
                        st.success(message)
                        st.session_state['dsn'] = dsn
                        st.session_state['connection_status'] = 'success'
                    else:
                        st.error(message)
                        st.session_state['connection_status'] = 'error'
            
            # Статус подключения
            if 'connection_status' in st.session_state:
                if st.session_state['connection_status'] == 'success':
                    st.markdown("""
                    <div class="connection-status connection-success">
                        <strong>🟢 Подключение активно</strong><br>
                        База данных готова к анализу
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="connection-status connection-error">
                        <strong>🔴 Подключение не установлено</strong><br>
                        Проверьте параметры подключения
                    </div>
                    """, unsafe_allow_html=True)
            
            # Сохраняем DSN в сессии
            if 'dsn' in st.session_state:
                dsn = st.session_state['dsn']
            else:
                dsn = None
                
        else:
            dsn = None
            st.success("✅ Mock режим активен - используются тестовые данные")
        
        # Настройки конфигурации PostgreSQL
        st.markdown("### 🐘 Параметры PostgreSQL")
        
        col1, col2 = st.columns(2)
        with col1:
            work_mem = st.slider(
                "work_mem (MB)", 
                1, 512, 4,
                help="Память для операций сортировки и хеширования"
            )
            shared_buffers = st.slider(
                "shared_buffers (MB)", 
                32, 2048, 128,
                help="Общий буфер для кэширования данных"
            )
        
        with col2:
            effective_cache_size = st.slider(
                "effective_cache_size (GB)", 
                1, 32, 4,
                help="Размер системного кэша"
            )
        
        # Пороги анализа
        st.markdown("### 📊 Пороги анализа")
        large_table_threshold = st.number_input(
            "Порог 'большой' таблицы (строк)",
            value=1000000,
            step=100000,
            format="%d",
            help="Таблицы с большим количеством строк считаются 'большими'"
        )
        
        expensive_query_threshold = st.number_input(
            "Порог 'дорогого' запроса (cost)",
            value=1000.0,
            step=100.0,
            format="%.1f",
            help="Запросы с cost выше этого значения считаются 'дорогими'"
        )
        
        # Кнопка применения настроек
        if st.button("🔄 Применить настройки", use_container_width=True):
            st.success("✅ Настройки применены!")
            time.sleep(1)
            st.rerun()
        
        # Настройки LLM
        st.markdown("---")
        st.markdown("### 🤖 Настройки LLM")
        
        # Включение AI-рекомендаций
        enable_ai = st.checkbox(
            "Включить AI-рекомендации", 
            value=False, 
            help="Получать рекомендации от языковых моделей"
        )
        
        if enable_ai:
            # Выбор провайдера LLM
            llm_provider = st.selectbox(
                "LLM провайдер",
                options=["openai", "anthropic", "local"],
                help="Выберите провайдера языковой модели"
            )
            
            if llm_provider == "openai":
                openai_api_key = st.text_input(
                    "OpenAI API ключ",
                    type="password",
                    help="Введите ваш OpenAI API ключ"
                )
                
                openai_model = st.selectbox(
                    "OpenAI модель",
                    options=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                    index=0,
                    help="Выберите модель OpenAI"
                )
                
                openai_temperature = st.slider(
                    "Температура",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1,
                    help="Контролирует креативность ответов (0.0 = детерминированный, 2.0 = очень креативный)"
                )
                
                # Сохранение настроек OpenAI
                if openai_api_key:
                    st.session_state['openai_api_key'] = openai_api_key
                    st.session_state['openai_model'] = openai_model
                    st.session_state['openai_temperature'] = openai_temperature
                    
                    # Тестирование подключения к OpenAI
                    if st.button("🔍 Тестировать OpenAI", key="test_openai"):
                        with st.spinner("🔍 Тестирую подключение к OpenAI..."):
                            if test_openai_connection(openai_api_key):
                                st.success("🟢 OpenAI подключение активно")
                            else:
                                st.error("🔴 Ошибка подключения к OpenAI")
            
            elif llm_provider == "anthropic":
                anthropic_api_key = st.text_input(
                    "Anthropic API ключ",
                    type="password",
                    help="Введите ваш Anthropic API ключ"
                )
                
                anthropic_model = st.selectbox(
                    "Anthropic модель",
                    options=["claude-3-sonnet", "claude-3-haiku", "claude-3-opus"],
                    index=0,
                    help="Выберите модель Anthropic"
                )
                
                # Сохранение настроек Anthropic
                if anthropic_api_key:
                    st.session_state['anthropic_api_key'] = anthropic_api_key
                    st.session_state['anthropic_model'] = anthropic_model
                    
                    # Тестирование подключения к Anthropic
                    if st.button("🔍 Тестировать Anthropic", key="test_anthropic"):
                        with st.spinner("🔍 Тестирую подключение к Anthropic..."):
                            if test_anthropic_connection(anthropic_api_key):
                                st.success("🟢 Anthropic подключение активно")
                            else:
                                st.error("🔴 Ошибка подключения к Anthropic")
            
            elif llm_provider == "local":
                local_llm_url = st.text_input(
                    "URL локального LLM",
                    value="http://localhost:11434",
                    help="URL для Ollama или LM Studio"
                )
                
                local_llm_model = st.text_input(
                    "Модель локального LLM",
                    value="llama2",
                    help="Название модели (например, llama2, mistral)"
                )
                
                # Сохранение настроек локального LLM
                if local_llm_url and local_llm_model:
                    st.session_state['local_llm_url'] = local_llm_url
                    st.session_state['local_llm_model'] = local_llm_model
                    
                    # Тестирование подключения к локальному LLM
                    if st.button("🔍 Тестировать локальный LLM", key="test_local"):
                        with st.spinner("🔍 Тестирую подключение к локальному LLM..."):
                            if test_local_llm_connection(local_llm_url, local_llm_model):
                                st.success("🟢 Локальный LLM подключение активно")
                            else:
                                st.error("🔴 Ошибка подключения к локальному LLM")
            
            # Общие настройки AI
            ai_confidence_threshold = st.slider(
                "Порог уверенности AI",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05,
                help="Минимальная уверенность для показа AI-рекомендаций"
            )
            
            # Сохранение общих настроек
            st.session_state['enable_ai_recommendations'] = True
            st.session_state['ai_provider'] = llm_provider
            st.session_state['ai_confidence_threshold'] = ai_confidence_threshold
            
            # Статус LLM
            st.success(f"🤖 LLM: {llm_provider.upper()}")
        else:
            st.session_state['enable_ai_recommendations'] = False
            st.info("🤖 AI-рекомендации отключены")
        
        # Информация о системе
        st.markdown("---")
        st.markdown("### ℹ️ Информация")
        st.info(f"**Streamlit:** {st.__version__}")
        st.info(f"**Mock режим:** {'Включен' if mock_mode else 'Выключен'}")
        if not mock_mode and dsn:
            st.info("**База данных:** Подключена")
        else:
            st.info("**База данных:** Не подключена")
        if enable_ai:
            st.info(f"**LLM:** {llm_provider.upper()}")
        else:
            st.info("**LLM:** Отключен")
    
    # Основной контент с вкладками
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Анализ SQL", 
        "📊 Статистика", 
        "📋 Примеры", 
        "🔍 Планы выполнения",
        "ℹ️ Справка"
    ])
    
    with tab1:
        # Получаем настройки LLM из session_state
        enable_ai = st.session_state.get('enable_ai_recommendations', False)
        ai_provider = st.session_state.get('ai_provider', 'auto')
        ai_confidence_threshold = st.session_state.get('ai_confidence_threshold', 0.7)
        
        # API ключи
        openai_api_key = st.session_state.get('openai_api_key', '')
        anthropic_api_key = st.session_state.get('anthropic_api_key', '')
        local_llm_url = st.session_state.get('local_llm_url', '')
        local_llm_model = st.session_state.get('local_llm_model', '')
        
        show_sql_analysis_tab(
            dsn, mock_mode, work_mem, shared_buffers, effective_cache_size, 
            large_table_threshold, expensive_query_threshold,
            enable_ai, ai_provider, ai_confidence_threshold,
            openai_api_key, anthropic_api_key, local_llm_url, local_llm_model
        )
    
    with tab2:
        show_statistics_tab(dsn, mock_mode)
    
    with tab3:
        show_examples_tab(
            dsn, mock_mode, work_mem, shared_buffers, effective_cache_size,
            large_table_threshold, expensive_query_threshold
        )
    
    with tab4:
        show_execution_plans_tab(dsn, mock_mode)
    
    with tab5:
        show_help_tab()


def show_sql_analysis_tab(dsn, mock_mode, work_mem, shared_buffers, effective_cache_size,
                          large_table_threshold, expensive_query_threshold,
                          enable_ai=False, ai_provider='auto', ai_confidence_threshold=0.7,
                          openai_api_key='', anthropic_api_key='', local_llm_url='', local_llm_model=''):
    """Показывает вкладку анализа SQL с улучшенным дизайном."""
    
    # Проверка подключения
    if not mock_mode and not dsn:
        st.warning("⚠️ Для анализа SQL необходимо подключиться к базе данных. Перейдите в боковую панель и настройте подключение.")
        return
    
    # Ввод SQL с улучшенным дизайном
    st.markdown("## 🔍 Анализ SQL-запроса")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sql_input = st.text_area(
            "Введите SQL-запрос для анализа:",
            height=200,
            placeholder="SELECT u.name, o.total_amount \nFROM users u \nJOIN orders o ON u.id = o.user_id \nWHERE o.total_amount > 1000;",
            help="Поддерживаются SELECT, WITH, JOIN, агрегатные функции и подзапросы"
        )
    
    with col2:
        st.markdown("### 📁 Загрузка файла")
        uploaded_file = st.file_uploader(
            "Или загрузите .sql файл:",
            type=['sql'],
            help="Поддерживаются файлы .sql"
        )
        
        if uploaded_file is not None:
            sql_input = uploaded_file.getvalue().decode("utf-8")
            st.success(f"✅ Файл загружен: {uploaded_file.name}")
            st.text_area("Содержимое файла:", value=sql_input, height=150)
    
    # Кнопка анализа с улучшенным дизайном
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button(
            "🔍 Анализировать SQL", 
            type="primary",
            use_container_width=True,
            disabled=not sql_input.strip() or (not mock_mode and not dsn)
        )
    
    # Индикатор загрузки
    if analyze_button and sql_input.strip():
        with st.spinner("🔍 Выполняется анализ SQL-запроса..."):
            time.sleep(0.5)  # Имитация загрузки
    
    # Анализ SQL
    if analyze_button and sql_input.strip():
        try:
            # Создаем конфигурацию
            custom_config = {
                'work_mem': work_mem,
                'shared_buffers': shared_buffers,
                'effective_cache_size': effective_cache_size,
                'large_table_threshold': large_table_threshold,
                'expensive_query_threshold': expensive_query_threshold,
                'enable_ai_recommendations': enable_ai,
                'ai_provider': ai_provider,
                'ai_confidence_threshold': ai_confidence_threshold,
                'openai_api_key': openai_api_key,
                'openai_model': st.session_state.get('openai_model', 'gpt-4'),
                'openai_temperature': st.session_state.get('openai_temperature', 0.7),
                'anthropic_api_key': anthropic_api_key,
                'anthropic_model': st.session_state.get('anthropic_model', 'claude-3-sonnet'),
                'local_llm_url': local_llm_url,
                'local_llm_model': local_llm_model
            }
            
            # Создаем анализатор с конфигурацией
            analyzer = SQLAnalyzer(dsn, mock_mode, custom_config)
            
            # Анализируем SQL
            result = analyzer.analyze_sql(sql_input)
            
            # Показываем результаты
            display_analysis_results(result, analyzer)
            
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            st.exception(e)


def display_analysis_results(result, analyzer):
    """Отображает результаты анализа с улучшенным дизайном."""
    
    # Успешное завершение
    st.success("🎉 Анализ SQL-запроса завершен успешно!")
    
    # Основные метрики в красивых карточках
    if result.metrics:
        st.markdown("## 📊 Метрики производительности")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>⏱️ Время выполнения</h3>
                <h2>{:.2f} мс</h2>
                <p>Ожидаемое время</p>
            </div>
            """.format(result.metrics.estimated_time_ms), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>💾 I/O операции</h3>
                <h2>{:.2f} MB</h2>
                <p>Ожидаемое использование</p>
            </div>
            """.format(result.metrics.estimated_io_mb), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🧠 Память</h3>
                <h2>{:.2f} MB</h2>
                <p>Ожидаемое использование</p>
            </div>
            """.format(result.metrics.estimated_memory_mb), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>📊 Строки</h3>
                <h2>{:,}</h2>
                <p>Ожидаемое количество</p>
            </div>
            """.format(result.metrics.estimated_rows), unsafe_allow_html=True)
    
    # Сводка плана выполнения
    if result.plan_summary:
        st.markdown("## 📋 Сводка плана выполнения")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.json(result.plan_summary)
        
        with col2:
            # Визуализация плана
            if result.explain_json:
                create_plan_visualization(result.explain_json)
    
    # Рекомендации по оптимизации
    if result.recommendations:
        st.markdown("## 💡 Рекомендации по оптимизации")
        
        # Группируем по приоритету
        high_recs = [r for r in result.recommendations if r.priority.value == "high"]
        medium_recs = [r for r in result.recommendations if r.priority.value == "medium"]
        low_recs = [r for r in result.recommendations if r.priority.value == "low"]
        
        # Высокий приоритет
        if high_recs:
            st.markdown("### 🚨 Высокий приоритет")
            for rec in high_recs:
                with st.expander(f"🔴 {rec.title}", expanded=True):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")
        
        # Средний приоритет
        if medium_recs:
            st.markdown("### ⚠️ Средний приоритет")
            for rec in medium_recs:
                with st.expander(f"🟡 {rec.title}"):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")
        
        # Низкий приоритет
        if low_recs:
            st.markdown("### ℹ️ Низкий приоритет")
            for rec in low_recs:
                with st.expander(f"🟢 {rec.title}"):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")
    
    # AI-рекомендации
    ai_recs = [r for r in result.recommendations if hasattr(r, 'type') and r.type == "ai_recommendation"]
    if ai_recs:
        st.markdown("## 🤖 AI-рекомендации")
        st.info("💡 Эти рекомендации сгенерированы с помощью искусственного интеллекта")
        
        for rec in ai_recs:
            # Определяем цвет приоритета
            priority_color = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(rec.priority, "🟡")
            
            with st.expander(f"{priority_color} AI: {rec.description}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Приоритет:** {rec.priority.upper()}")
                    st.markdown(f"**Категория:** {rec.category}")
                    st.markdown(f"**Уверенность:** {rec.confidence:.2f}")
                    if rec.expected_improvement:
                        st.markdown(f"**Ожидаемое улучшение:** {rec.expected_improvement}")
                
                with col2:
                    if rec.current_query and rec.optimized_query:
                        st.markdown("**Текущий запрос:**")
                        st.code(rec.current_query, language="sql")
                        st.markdown("**Оптимизированный запрос:**")
                        st.code(rec.optimized_query, language="sql")
                
                if rec.reasoning:
                    st.markdown("**Объяснение:**")
                    st.info(rec.reasoning)
                
                if rec.llm_model:
                    st.markdown(f"**Модель:** {rec.llm_model}")
                
                if rec.additional_suggestions:
                    st.markdown("**Дополнительные предложения:**")
                    for suggestion in rec.additional_suggestions:
                        st.markdown(f"• {suggestion}")
    
    # Экспорт результатов
    st.markdown("## 📤 Экспорт результатов")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # JSON экспорт
        json_report = analyzer.export_analysis_report(result, "json")
        st.download_button(
            label="📄 Скачать JSON",
            data=json_report,
            file_name=f"sql_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Текстовый экспорт
        text_report = analyzer.export_analysis_report(result, "text")
        st.download_button(
            label="📝 Скачать текст",
            data=text_report,
            file_name=f"sql_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        # Raw EXPLAIN JSON
        if result.explain_json:
            st.download_button(
                label="🔍 Скачать EXPLAIN",
                data=json.dumps(result.explain_json, indent=2),
                file_name=f"explain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col4:
        # PDF экспорт (если доступен)
        st.download_button(
            label="📊 Скачать PDF",
            data="PDF content would go here",
            file_name=f"sql_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=True,
            help="PDF экспорт в разработке"
        )
    
    # Детали анализа
    with st.expander("🔍 Детали анализа", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Валидация")
            if result.is_valid:
                st.success("✅ Запрос валиден")
            else:
                st.error("❌ Запрос содержит ошибки:")
                for error in result.validation_errors:
                    st.write(f"• {error}")
        
        with col2:
            st.markdown("### ⚙️ Конфигурация")
            st.json(result.config_used)
        
        st.markdown(f"**⏱️ Время анализа:** {result.analysis_time:.3f} секунд")


def create_plan_visualization(explain_json):
    """Создает улучшенную визуализацию плана выполнения."""
    try:
        # Извлекаем узлы плана
        def extract_nodes(plan, level=0):
            nodes = []
            if 'Node Type' in plan:
                nodes.append({
                    'level': level,
                    'type': plan['Node Type'],
                    'cost': plan.get('Total Cost', 0),
                    'rows': plan.get('Plan Rows', 0),
                    'width': plan.get('Plan Width', 0)
                })
            
            if 'Plans' in plan:
                for child in plan['Plans']:
                    nodes.extend(extract_nodes(child, level + 1))
            
            return nodes
        
        nodes = extract_nodes(explain_json.get('Plan', {}))
        
        if nodes:
            # Создаем DataFrame для визуализации
            df = pd.DataFrame(nodes)
            
            # Визуализация по уровням
            fig = px.bar(
                df, 
                x='level', 
                y='cost',
                color='type',
                title="Структура плана выполнения",
                labels={'level': 'Уровень', 'cost': 'Стоимость', 'type': 'Тип узла'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_layout(
                height=400,
                showlegend=True,
                xaxis_title="Уровень плана",
                yaxis_title="Стоимость (cost)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Дополнительная информация о плане
            st.markdown("### 📊 Детали плана")
            st.dataframe(
                df[['level', 'type', 'cost', 'rows', 'width']].sort_values('level'),
                use_container_width=True
            )
            
    except Exception as e:
        st.warning(f"⚠️ Не удалось создать визуализацию: {e}")


def show_statistics_tab(dsn, mock_mode):
    """Показывает вкладку статистики с улучшенным дизайном."""
    st.markdown("## 📊 Статистика pg_stat_statements")
    
    if mock_mode:
        st.info("📝 Mock режим: отображаются тестовые данные")
    elif not dsn:
        st.warning("⚠️ Для просмотра статистики необходимо подключиться к базе данных.")
        return
    
    try:
        analyzer = SQLAnalyzer(dsn, mock_mode)
        stats = analyzer.get_pg_stat_statements(limit=50)
        
        if stats:
            # Создаем DataFrame
            df = pd.DataFrame(stats)
            
            # Основные метрики в красивых карточках
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h3>📝 Всего запросов</h3>
                    <h2>{}</h2>
                    <p>Уникальных запросов</p>
                </div>
                """.format(len(stats)), unsafe_allow_html=True)
            
            with col2:
                total_calls = df['calls'].sum()
                st.markdown("""
                <div class="metric-card">
                    <h3>🔄 Общее количество</h3>
                    <h2>{:,}</h2>
                    <p>Вызовов запросов</p>
                </div>
                """.format(total_calls), unsafe_allow_html=True)
            
            with col3:
                total_time = df['total_time'].sum()
                st.markdown("""
                <div class="metric-card">
                    <h3>⏱️ Общее время</h3>
                    <h2>{:.2f} мс</h2>
                    <p>Выполнения</p>
                </div>
                """.format(total_time), unsafe_allow_html=True)
            
            with col4:
                avg_time = df['mean_time'].mean()
                st.markdown("""
                <div class="metric-card">
                    <h3>📊 Среднее время</h3>
                    <h2>{:.2f} мс</h2>
                    <p>На запрос</p>
                </div>
                """.format(avg_time), unsafe_allow_html=True)
            
            # Топ медленных запросов
            st.markdown("## 🐌 Топ медленных запросов")
            slow_queries = df.nlargest(10, 'total_time')
            
            fig = px.bar(
                slow_queries,
                x='total_time',
                y='query',
                orientation='h',
                title="Топ-10 медленных запросов",
                labels={'total_time': 'Время выполнения (мс)', 'query': 'SQL запрос'},
                color='total_time',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Детальная таблица
            st.markdown("## 📋 Детальная статистика")
            st.dataframe(
                df[['query', 'calls', 'total_time', 'mean_time', 'rows']].head(20),
                use_container_width=True
            )
            
        else:
            st.warning("⚠️ Статистика недоступна или пуста")
            
    except Exception as e:
        st.error(f"❌ Ошибка получения статистики: {e}")


def show_examples_tab(dsn, mock_mode, work_mem, shared_buffers, effective_cache_size,
                      large_table_threshold, expensive_query_threshold):
    """Показывает вкладку с примерами с улучшенным дизайном."""
    st.markdown("## 📋 Примеры запросов")
    
    try:
        analyzer = SQLAnalyzer(dsn, mock_mode)
        examples = analyzer.get_example_queries()
        
        # Создаем вкладки для каждого примера
        example_tabs = st.tabs([f"📝 {ex['name']}" for ex in examples])
        
        for i, (example, tab) in enumerate(zip(examples, example_tabs)):
            with tab:
                st.markdown(f"### {example['name']}")
                st.markdown(f"**Описание:** {example['description']}")
                
                # SQL код в красивом блоке
                st.markdown("**SQL запрос:**")
                st.code(example['sql'], language="sql")
                
                # Кнопка анализа
                if st.button(f"🔍 Анализировать пример {i+1}", key=f"analyze_{i}"):
                    try:
                        with st.spinner("🔍 Анализирую пример..."):
                            # Обновляем конфигурацию
                            custom_config = {
                                'work_mem': work_mem,
                                'shared_buffers': shared_buffers,
                                'effective_cache_size': effective_cache_size,
                                'large_table_threshold': large_table_threshold,
                                'expensive_query_threshold': expensive_query_threshold
                            }
                            
                            # Анализируем пример
                            result = analyzer.analyze_sql(example['sql'], custom_config)
                            
                            # Показываем краткие результаты
                            st.success("✅ Анализ примера завершен!")
                            
                            if result.metrics:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("⏱️ Время", f"{result.metrics.estimated_time_ms:.2f} мс")
                                with col2:
                                    st.metric("💾 I/O", f"{result.metrics.estimated_io_mb:.2f} MB")
                                with col3:
                                    st.metric("🧠 Память", f"{result.metrics.estimated_memory_mb:.2f} MB")
                            
                            if result.recommendations:
                                st.markdown(f"**💡 Рекомендации:** {len(result.recommendations)} найдено")
                                for rec in result.recommendations[:3]:  # Показываем первые 3
                                    st.write(f"• {rec.title} ({rec.priority.value})")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка анализа примера: {e}")
    
    except Exception as e:
        st.error(f"❌ Ошибка загрузки примеров: {e}")


def show_execution_plans_tab(dsn, mock_mode):
    """Показывает вкладку с анализом планов выполнения."""
    st.markdown("## 🔍 Анализ планов выполнения")
    
    if mock_mode:
        st.info("📝 Mock режим: отображаются тестовые планы")
    elif not dsn:
        st.warning("⚠️ Для анализа планов необходимо подключиться к базе данных.")
        return
    
    # Примеры планов выполнения
    st.markdown("### 📊 Типы узлов планов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔍 Операции сканирования:**
        - **Seq Scan** - последовательное сканирование
        - **Index Scan** - сканирование по индексу
        - **Bitmap Scan** - битовая карта индексов
        - **Tid Scan** - сканирование по TID
        
        **🔗 Операции соединения:**
        - **Nested Loop** - вложенный цикл
        - **Hash Join** - хеш-соединение
        - **Merge Join** - слияние-соединение
        """)
    
    with col2:
        st.markdown("""
        **📊 Операции агрегации:**
        - **HashAggregate** - хеш-агрегация
        - **GroupAggregate** - групповая агрегация
        
        **📝 Операции сортировки:**
        - **Sort** - сортировка
        - **Incremental Sort** - инкрементальная сортировка
        
        **🔄 Другие операции:**
        - **Limit** - ограничение результатов
        - **WindowAgg** - оконные функции
        """)
    
    # Интерактивный анализатор планов
    st.markdown("### 🔍 Анализ вашего плана")
    
    plan_json = st.text_area(
        "Вставьте JSON план выполнения (EXPLAIN FORMAT JSON):",
        height=200,
        placeholder='{"Plan": {"Node Type": "Seq Scan", "Total Cost": 100, "Plan Rows": 1000}}',
        help="Скопируйте результат команды EXPLAIN (FORMAT JSON)"
    )
    
    if st.button("🔍 Анализировать план", use_container_width=True):
        if plan_json.strip():
            try:
                plan_data = json.loads(plan_json)
                st.success("✅ План загружен!")
                
                # Анализируем план
                analyzer = SQLAnalyzer(dsn, mock_mode)
                plan_parser = analyzer.plan_parser
                
                # Парсим план
                plan = plan_parser.parse_explain_json(plan_data)
                plan_summary = plan_parser.get_plan_summary(plan)
                
                # Показываем сводку
                st.markdown("### 📋 Сводка плана")
                st.json(plan_summary)
                
                # Визуализация
                create_plan_visualization(plan_data)
                
            except json.JSONDecodeError:
                st.error("❌ Неверный формат JSON")
            except Exception as e:
                st.error(f"❌ Ошибка анализа плана: {e}")
        else:
            st.warning("⚠️ Введите план для анализа")


def show_help_tab():
    """Показывает вкладку справки с улучшенным дизайном."""
    st.markdown("## ℹ️ Справка")
    
    st.markdown("""
    ## 🚀 PostgreSQL SQL Analyzer
    
    **Инструмент для превентивного анализа SQL-запросов к PostgreSQL версии 15+.**
    
    ### ✨ Основные возможности
    
    - **🔍 Анализ планов выполнения** - парсинг EXPLAIN (FORMAT JSON)
    - **📊 Прогнозирование ресурсов** - оценка времени, I/O, памяти
    - **💡 Рекомендации по оптимизации** - с приоритетами и примерами
    - **📈 Анализ статистики** - чтение pg_stat_statements
    - **🎭 Mock режим** - тестирование без подключения к БД
    
    ### 🔧 Как использовать
    
    1. **📝 Введите SQL-запрос** в текстовое поле или загрузите .sql файл
    2. **⚙️ Настройте параметры** PostgreSQL в боковой панели
    3. **🔍 Нажмите "Анализировать"** для получения результатов
    4. **💡 Изучите рекомендации** по оптимизации
    5. **📤 Экспортируйте отчет** в JSON или текстовом формате
    
    ### 📊 Интерпретация результатов
    
    - **⏱️ Время выполнения** - оценка в миллисекундах
    - **💾 I/O операции** - ожидаемый объем данных в MB
    - **🧠 Память** - использование work_mem и shared_buffers
    - **📊 Строки** - количество обрабатываемых записей
    
    ### 🎯 Система рекомендаций
    
    - **🔴 Высокий приоритет** - критичные проблемы производительности
    - **🟡 Средний приоритет** - значимые улучшения
    - **🟢 Низкий приоритет** - тонкая настройка
    
    ### 🔒 Безопасность
    
    - ✅ Только read-only операции (SELECT, WITH)
    - ✅ Валидация SQL на опасные операции
    - ✅ Поддержка только расширения pg_stat_statements
    - ✅ Изоляция подключений
    
    ### 🐳 Способы запуска
    
    ```bash
    # 🚀 Локально
    streamlit run app/streamlit_app.py
    
    # 🐳 Docker
    docker-compose up
    
    # 📱 Наш скрипт
    python run_streamlit.py
    ```
    
    ### 📚 Документация
    
    - **📖 README.md** - подробная документация
    - **⚡ QUICKSTART.md** - быстрый старт
    - **📊 PROJECT_STATUS.md** - статус проекта
    - **🚀 LAUNCH.md** - инструкции по запуску
    - **📝 examples/queries.sql** - примеры запросов
    
    ### 🤝 Поддержка
    
    - **🐛 Баги и проблемы** - создайте Issue в репозитории
    - **💡 Предложения** - обсудите в Discussions
    - **📚 Документация** - изучите примеры и руководства
    - **🔧 Разработка** - внесите свой вклад в проект
    
    ### 📈 Roadmap
    
    - **v0.2.0** - Поддержка PostgreSQL 16+, расширенная аналитика
    - **v0.3.0** - Автоматическая оптимизация, поддержка других СУБД
    - **v1.0.0** - Production готовность, коммерческая поддержка
    
    ---
    
    **🎉 Спасибо за использование PostgreSQL SQL Analyzer!**
    
    **Сделайте SQL быстрее и умнее!** 🚀
    """)


if __name__ == "__main__":
    main()
