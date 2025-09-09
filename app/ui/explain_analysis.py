"""Модуль для вкладки 'Explain анализ' с LLM."""

from py_pg_explain_analyzer.llm_summarizer import run_llm
from py_pg_explain_analyzer.sql_metadata_extractor import TableInfoExtractor
from py_pg_explain_analyzer.sql_parser import SqlAnalyzer
from py_pg_explain_analyzer.db import PgConnection
from py_pg_explain_analyzer import PgExplainAnalyzer, AnalysisRequest, AnalysisResult
import streamlit as st
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
import plotly.express as px
import sys
import os

# Добавляем путь к модулю _explain_analyze
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '_explain_analyze'))


logger = logging.getLogger(__name__)


def show_explain_analysis_tab(dsn: str, mock_mode: bool = False):
    """Отображает вкладку 'Explain анализ' с красивым дашбордом."""
    # Красивый заголовок
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    ">
        <h1 style="font-size: 2.5rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🔍 Explain анализ SQL запросов
        </h1>
        <p style="font-size: 1.2rem; margin: 1rem 0; opacity: 0.9;">
            Интеллектуальный анализ планов выполнения с AI-рекомендациями
        </p>
    </div>
    """, unsafe_allow_html=True)

    if mock_mode:
        st.info("🎭 Mock режим: отображаются тестовые данные")
        _show_mock_explain_analysis()
        return

    try:
        # Создаем вкладки для разных разделов
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Ввод SQL",
            "📊 Анализ плана",
            "🤖 AI рекомендации",
            "📈 Сравнение"
        ])

        with tab1:
            _show_sql_input_dashboard()

        with tab2:
            if st.session_state.get('sql_query'):
                _analyze_sql_query(dsn)
            else:
                _show_analysis_placeholder()

        with tab3:
            if st.session_state.get('current_analysis'):
                _show_ai_recommendations_dashboard()
            else:
                _show_ai_placeholder()

        with tab4:
            _show_plan_comparison()

    except Exception as e:
        st.error(f"❌ Ошибка анализа SQL: {str(e)}")
        logger.error(f"Ошибка в show_explain_analysis_tab: {e}")


def _show_sql_input_dashboard():
    """Отображает красивое поле для ввода SQL запроса."""
    st.markdown("### 📝 Ввод SQL запроса")

    # Красивая карточка для ввода
    st.markdown("""
    <div style="
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
        margin-bottom: 2rem;
    ">
        <h3 style="color: #4CAF50; margin: 0 0 1rem 0;">💡 Введите ваш SQL запрос</h3>
        <p style="color: #666; margin: 0;">
            Поддерживаются SELECT, INSERT, UPDATE, DELETE запросы с автоматическим анализом плана выполнения
        </p>
    </div>
    """, unsafe_allow_html=True)

    _show_sql_input()


def _show_analysis_placeholder():
    """Показывает заглушку для анализа."""
    st.markdown("""
    <div style="
        background: #f8f9fa;
        padding: 3rem;
        border-radius: 10px;
        text-align: center;
        border: 2px dashed #dee2e6;
        margin: 2rem 0;
    ">
        <h3 style="color: #6c757d; margin: 0 0 1rem 0;">📊 Анализ плана выполнения</h3>
        <p style="color: #6c757d; margin: 0;">
            Введите SQL запрос в разделе "📝 Ввод SQL" для начала анализа
        </p>
    </div>
    """, unsafe_allow_html=True)


def _show_ai_placeholder():
    """Показывает заглушку для AI рекомендаций."""
    st.markdown("""
    <div style="
        background: #f8f9fa;
        padding: 3rem;
        border-radius: 10px;
        text-align: center;
        border: 2px dashed #dee2e6;
        margin: 2rem 0;
    ">
        <h3 style="color: #6c757d; margin: 0 0 1rem 0;">🤖 AI рекомендации</h3>
        <p style="color: #6c757d; margin: 0;">
            После анализа SQL запроса здесь появятся интеллектуальные рекомендации по оптимизации
        </p>
    </div>
    """, unsafe_allow_html=True)


def _show_ai_recommendations_dashboard():
    """Показывает красивый дашборд с AI рекомендациями."""
    st.markdown("### 🤖 AI рекомендации по оптимизации")

    # Автоматически запускаем AI анализ
    if st.session_state.get('current_analysis') and not st.session_state.get('ai_analysis_done'):
        st.session_state['run_ai_analysis'] = True
        st.session_state['ai_analysis_done'] = True
        st.rerun()

    # Показываем результаты если есть
    if 'llm_analysis_result' in st.session_state:
        _display_llm_analysis_results(st.session_state['llm_analysis_result'])


def _show_sql_input():
    """Отображает поле для ввода SQL запроса."""
    st.markdown("### 📝 Ввод SQL запроса")

    # Поле для ввода SQL
    sql_query = st.text_area(
        "SQL запрос",
        value=st.session_state.get('sql_query', ''),
        height=200,
        placeholder="Введите SQL запрос для анализа...",
        help="Введите SQL запрос для анализа плана выполнения"
    )

    # Сохраняем в session_state
    st.session_state['sql_query'] = sql_query

    # Кнопки
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Анализировать", type="primary"):
            if sql_query.strip():
                st.session_state['analyze_query'] = True
                st.session_state['run_ai_analysis'] = True  # Автоматически запускаем AI анализ
            else:
                st.warning("⚠️ Введите SQL запрос для анализа")

    with col2:
        if st.button("📋 Очистить"):
            st.session_state['sql_query'] = ""
            st.session_state['analyze_query'] = False
            st.session_state['run_ai_analysis'] = False
            st.rerun()

    with col3:
        if st.button("💾 Сохранить план"):
            if st.session_state.get('current_plan'):
                st.session_state['saved_plan'] = st.session_state['current_plan']
                st.success("✅ План сохранен для сравнения")


def _analyze_sql_query(dsn: str):
    """Анализирует SQL запрос с использованием нового анализатора."""
    if not st.session_state.get('analyze_query'):
        return

    sql_query = st.session_state.get('sql_query', '')
    if not sql_query.strip():
        return

    with st.spinner("Анализ SQL запроса..."):
        try:
            # Создаем подключение к БД
            db_conn = PgConnection(dsn)
            analyzer = PgExplainAnalyzer(db_conn)

            # Создаем запрос на анализ
            analysis_request = AnalysisRequest(
                sql=sql_query,
                analyze=True,  # Включаем ANALYZE для получения реальных метрик
                verbose=True,  # Подробная информация
                buffers=True,  # Информация о буферах
                timing=True,   # Время выполнения
                settings=True,  # Настройки PostgreSQL
                costs=True     # Стоимость операций
            )

            # Выполняем анализ
            analysis_result = analyzer.analyze_one(analysis_request)

            # Сохраняем результат
            st.session_state['current_analysis'] = analysis_result
            st.session_state['current_plan'] = analysis_result.raw_explain_json

            # Отображаем результаты
            _display_new_analysis_results(analysis_result)

            # LLM анализ
            _show_new_llm_analysis(analysis_result, sql_query, dsn)

            # Сбрасываем флаг анализа
            st.session_state['analyze_query'] = False

            # Закрываем подключение
            db_conn.close()

        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            logger.error(f"Ошибка анализа SQL: {e}")


def _execute_explain(dsn: str, sql_query: str) -> Optional[Dict[str, Any]]:
    """Выполняет EXPLAIN для SQL запроса."""
    from app.database import DatabaseConnection

    try:
        db_conn = DatabaseConnection(dsn)

        with db_conn.get_connection() as conn:
            with conn.cursor() as cur:
                # Выполняем EXPLAIN (FORMAT JSON) - БЕЗОПАСНО
                cur.execute("EXPLAIN (FORMAT JSON) %s", (sql_query,))
                result = cur.fetchone()

                if result and result[0]:
                    return result[0]

    except Exception as e:
        logger.error(f"Ошибка выполнения EXPLAIN: {e}")
        raise

    return None


def _display_explain_results(explain_result: Dict[str, Any]):
    """Отображает результаты EXPLAIN."""
    st.markdown("### 📊 План выполнения")

    if not explain_result:
        st.warning("⚠️ План выполнения не получен")
        return

    # Извлекаем план
    plan = explain_result[0] if isinstance(
        explain_result, list) else explain_result

    # Отображаем JSON план
    with st.expander("📋 JSON план выполнения"):
        st.json(plan)

    # Анализируем план
    plan_analysis = _analyze_plan(plan)

    # Отображаем сводку
    _show_plan_summary(plan_analysis)

    # Отображаем дерево плана
    _show_plan_tree(plan)

    # Отображаем метрики
    _show_plan_metrics(plan_analysis)


def _analyze_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Анализирует план выполнения."""
    analysis = {
        'total_cost': 0,
        'total_rows': 0,
        'total_time': 0,
        'node_types': [],
        'warnings': [],
        'recommendations': []
    }

    def analyze_node(node):
        if 'Plan' in node:
            plan_node = node['Plan']

            # Собираем метрики
            analysis['total_cost'] += plan_node.get('Total Cost', 0)
            analysis['total_rows'] += plan_node.get('Plan Rows', 0)

            # Собираем типы узлов
            node_type = plan_node.get('Node Type', 'Unknown')
            analysis['node_types'].append(node_type)

            # Проверяем на проблемы
            if node_type == 'Seq Scan':
                analysis['warnings'].append(
                    "Последовательное сканирование таблицы")

            if plan_node.get('Total Cost', 0) > 1000:
                analysis['warnings'].append(
                    f"Высокая стоимость узла: {node_type}")

            # Рекурсивно анализируем дочерние узлы
            if 'Plans' in plan_node:
                for child in plan_node['Plans']:
                    analyze_node({'Plan': child})

    analyze_node(plan)

    return analysis


def _show_plan_summary(plan_analysis: Dict[str, Any]):
    """Отображает сводку плана."""
    st.markdown("#### 📈 Сводка плана")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Общая стоимость",
            value=f"{plan_analysis['total_cost']:.2f}"
        )

    with col2:
        st.metric(
            label="📊 Строки",
            value=f"{plan_analysis['total_rows']:,}"
        )

    with col3:
        st.metric(
            label="🔧 Типы узлов",
            value=len(set(plan_analysis['node_types']))
        )

    with col4:
        st.metric(
            label="⚠️ Предупреждения",
            value=len(plan_analysis['warnings'])
        )

    # Предупреждения
    if plan_analysis['warnings']:
        st.markdown("#### ⚠️ Предупреждения")
        for warning in plan_analysis['warnings']:
            st.warning(f"⚠️ {warning}")


def _show_plan_tree(plan: Dict[str, Any]):
    """Отображает дерево плана выполнения."""
    st.markdown("#### 🌳 Дерево плана выполнения")

    # Создаем визуализацию дерева
    tree_data = _build_plan_tree(plan)

    if tree_data:
        # Отображаем дерево
        _display_plan_tree_visualization(tree_data)


def _build_plan_tree(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Строит дерево плана выполнения."""
    tree_data = []

    def build_node(node, level=0):
        if 'Plan' in node:
            plan_node = node['Plan']

            node_info = {
                'level': level,
                'node_type': plan_node.get('Node Type', 'Unknown'),
                'relation_name': plan_node.get('Relation Name', ''),
                'total_cost': plan_node.get('Total Cost', 0),
                'plan_rows': plan_node.get('Plan Rows', 0),
                'startup_cost': plan_node.get('Startup Cost', 0),
                'actual_rows': plan_node.get('Actual Rows', 0),
                'actual_total_time': plan_node.get('Actual Total Time', 0)
            }

            tree_data.append(node_info)

            # Рекурсивно обрабатываем дочерние узлы
            if 'Plans' in plan_node:
                for child in plan_node['Plans']:
                    build_node({'Plan': child}, level + 1)

    build_node(plan)
    return tree_data


def _display_plan_tree_visualization(tree_data: List[Dict[str, Any]]):
    """Отображает визуализацию дерева плана."""
    if not tree_data:
        return

    # Создаем DataFrame для отображения
    import pandas as pd

    df = pd.DataFrame(tree_data)

    # Отображаем таблицу
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            'level': 'Уровень',
            'node_type': 'Тип узла',
            'relation_name': 'Таблица',
            'total_cost': 'Стоимость',
            'plan_rows': 'Планируемые строки',
            'actual_rows': 'Фактические строки',
            'actual_total_time': 'Время (мс)'
        }
    )

    # График стоимости по узлам
    if len(df) > 1:
        fig = px.bar(
            df,
            x='node_type',
            y='total_cost',
            title="Стоимость по типам узлов",
            labels={'total_cost': 'Стоимость', 'node_type': 'Тип узла'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')


def _show_plan_metrics(plan_analysis: Dict[str, Any]):
    """Отображает метрики плана."""
    st.markdown("#### 📊 Метрики плана")

    # Распределение по типам узлов
    if plan_analysis['node_types']:
        import pandas as pd

        node_counts = pd.Series(plan_analysis['node_types']).value_counts()

        fig = px.pie(
            values=node_counts.values,
            names=node_counts.index,
            title="Распределение по типам узлов"
        )
        st.plotly_chart(fig, width='stretch')


def _display_new_analysis_results(analysis_result: AnalysisResult):
    """Отображает результаты нового анализа."""
    st.markdown("### 📊 Результаты анализа")

    # Отображаем JSON план
    with st.expander("📋 JSON план выполнения"):
        st.json(analysis_result.raw_explain_json)

    # Отображаем проблемы
    if analysis_result.issues:
        st.markdown("#### ⚠️ Обнаруженные проблемы")
        for issue in analysis_result.issues:
            severity_color = {
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "critical": "🚨"
            }.get(issue.severity.value, "⚪")

            st.markdown(f"{severity_color} **{issue.title}** ({issue.severity.value})")
            st.markdown(f"   {issue.details}")
            if issue.node_path:
                st.markdown(f"   *Путь: {issue.node_path}*")

    # Отображаем предложения
    if analysis_result.suggestions:
        st.markdown("#### 💡 Предложения по оптимизации")
        for suggestion in analysis_result.suggestions:
            st.markdown(f"**{suggestion.title}**")
            st.markdown(f"   {suggestion.rationale}")
            if suggestion.fix:
                st.code(suggestion.fix, language="sql")

    # Отображаем кандидаты на индексы
    if analysis_result.index_candidates:
        st.markdown("#### 🗂️ Рекомендуемые индексы")
        for idx in analysis_result.index_candidates:
            st.code(idx.to_ddl(), language="sql")

    # Отображаем Markdown отчет
    if analysis_result.markdown_report:
        with st.expander("📄 Подробный отчет"):
            st.markdown(analysis_result.markdown_report)


def _show_new_llm_analysis(analysis_result: AnalysisResult, sql_query: str, dsn: str):
    """Отображает LLM анализ с использованием нового анализатора."""
    st.markdown("### 🤖 AI анализ плана выполнения")

    # Проверяем, включен ли AI
    if not st.session_state.get('enable_ai', False):
        st.info("ℹ️ AI анализ отключен. Включите AI в настройках для получения рекомендаций.")
        return

    # Автоматически запускаем AI анализ если установлен флаг
    should_run_ai = st.session_state.get('run_ai_analysis', False)

    if should_run_ai or st.button("🔍 Анализировать план с AI", type="primary"):
        with st.spinner("AI анализирует план выполнения..."):
            try:
                # Подготавливаем данные для LLM
                llm_payload = _prepare_analysis_for_llm(analysis_result, sql_query, dsn)

                # Получаем LLM клиент
                llm_client = _get_llm_client()

                if llm_client:
                    # Выполняем LLM анализ
                    logger.info("Запуск LLM анализа...")
                    llm_result = run_llm(llm_client, llm_payload)
                    logger.info("LLM анализ завершен успешно")

                    # Сохраняем результат в session_state
                    st.session_state['llm_analysis_result'] = llm_result

                    # Отображаем результаты
                    _display_llm_analysis_results(llm_result)
                else:
                    st.error("❌ Не удалось инициализировать LLM клиент")

            except Exception as e:
                st.error(f"❌ Ошибка AI анализа: {str(e)}")
                logger.error(f"Ошибка LLM анализа плана: {e}")
            finally:
                # Сбрасываем флаг после выполнения
                st.session_state['run_ai_analysis'] = False


def _prepare_analysis_for_llm(analysis_result: AnalysisResult, sql_query: str, dsn: str) -> Dict[str, Any]:
    """Подготавливает данные анализа для LLM."""
    try:
        # Парсим SQL
        sql_analyzer = SqlAnalyzer(sql_query)
        parser_output = sql_analyzer.get_tables_and_columns()
        normalized_sql = sql_analyzer.normalize()

        # Получаем метаданные таблиц
        metadata_extractor = TableInfoExtractor(dsn)
        metadata = metadata_extractor.analyze(parser_output)

        # Подготавливаем эвристики
        heuristics = {
            "issues": [
                {
                    "code": issue.code,
                    "title": issue.title,
                    "severity": issue.severity.value,
                    "details": issue.details
                }
                for issue in analysis_result.issues
            ],
            "suggestions": [
                {
                    "code": sug.code,
                    "title": sug.title,
                    "rationale": sug.rationale,
                    "fix": sug.fix
                }
                for sug in analysis_result.suggestions
            ],
            "index_candidates": [
                {
                    "table": idx.table,
                    "columns": idx.columns,
                    "include": idx.include,
                    "where_predicate": idx.where_predicate
                }
                for idx in analysis_result.index_candidates
            ]
        }

        return {
            "sql": sql_query,
            "normalized_sql": normalized_sql,
            "parser_output": parser_output,
            "metadata": metadata,
            "explain_json": analysis_result.raw_explain_json,
            "heuristics": heuristics
        }

    except Exception as e:
        logger.error(f"Ошибка подготовки данных для LLM: {e}")
        return {
            "sql": sql_query,
            "normalized_sql": sql_query,
            "parser_output": {},
            "metadata": {},
            "explain_json": analysis_result.raw_explain_json,
            "heuristics": {"issues": [], "suggestions": [], "index_candidates": []}
        }


def _get_llm_client():
    """Получает LLM клиент на основе настроек из sidebar."""
    try:
        # Проверяем, включен ли AI
        if not st.session_state.get('enable_ai', False):
            return None

        ai_provider = st.session_state.get('ai_provider', 'openai')

        if ai_provider.lower() == 'openai':
            import openai
            api_key = st.session_state.get('openai_api_key', '')
            if not api_key:
                st.warning("⚠️ OpenAI API ключ не настроен. Настройте его в sidebar для использования AI анализа.")
                return None

            # Создаем клиент с настройками прокси если включен
            client_kwargs = {'api_key': api_key}

            if st.session_state.get('enable_proxy', True):
                proxy_host = st.session_state.get('proxy_host', 'localhost')
                proxy_port = st.session_state.get('proxy_port', 1080)
                client_kwargs['http_client'] = openai.HTTPClient(
                    proxies=f"http://{proxy_host}:{proxy_port}"
                )

            client = openai.OpenAI(**client_kwargs)
            logger.info("✅ OpenAI клиент создан успешно")
            return client

        elif ai_provider.lower() == 'anthropic':
            import anthropic
            api_key = st.session_state.get('anthropic_api_key', '')
            if not api_key:
                st.error("❌ Anthropic API ключ не настроен")
                return None
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Anthropic клиент создан успешно")
            return client

        elif ai_provider.lower() == 'локальный llm':
            # Создаем простой клиент для локального LLM
            local_llm_url = st.session_state.get('local_llm_url', 'http://localhost:11434')
            local_llm_model = st.session_state.get('local_llm_model', 'llama3.1:8b')

            # Создаем простой клиент для Ollama
            class LocalLLMClient:
                def __init__(self, base_url, model):
                    self.base_url = base_url
                    self.model = model

                def chat(self):
                    return self

                def completions(self):
                    return self

                def create(self, **kwargs):
                    # Простая заглушка для локального LLM
                    return type('Response', (), {
                        'choices': [type('Choice', (), {
                            'message': type('Message', (), {
                                'content': 'Локальный LLM анализ недоступен. Используйте OpenAI с прокси или Anthropic.'
                            })()
                        })()]
                    })()

            client = LocalLLMClient(local_llm_url, local_llm_model)
            logger.info(f"✅ Локальный LLM клиент создан: {local_llm_url}/{local_llm_model}")
            return client

        else:
            st.error(f"❌ Неподдерживаемый провайдер AI: {ai_provider}")
            return None

    except Exception as e:
        logger.error(f"Ошибка создания LLM клиента: {e}")
        st.error(f"❌ Ошибка создания LLM клиента: {str(e)}")
        return None


def _display_llm_analysis_results(llm_result: Dict[str, Any]):
    """Отображает результаты LLM анализа."""
    st.markdown("#### 🎯 AI Рекомендации")

    # Проблемы
    if llm_result.get('problems'):
        st.markdown("##### 🚨 Критические проблемы")
        for problem in llm_result['problems']:
            severity_icon = {
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "critical": "🚨"
            }.get(problem.get('severity', 'low'), "⚪")

            st.markdown(f"{severity_icon} **{problem.get('title', 'Проблема')}**")
            st.markdown(f"   {problem.get('details', '')}")

    # Предупреждения
    if llm_result.get('warnings'):
        st.markdown("##### ⚠️ Предупреждения")
        for warning in llm_result['warnings']:
            st.markdown(f"⚠️ **{warning.get('title', 'Предупреждение')}**")
            st.markdown(f"   {warning.get('details', '')}")

    # Рекомендации
    if llm_result.get('recommendations'):
        st.markdown("##### 💡 Рекомендации")
        for rec in llm_result['recommendations']:
            st.markdown(f"**{rec.get('title', 'Рекомендация')}**")
            if rec.get('actions'):
                for action in rec['actions']:
                    if action.get('sql'):
                        st.code(action['sql'], language="sql")
                    if action.get('note'):
                        st.markdown(f"   *{action['note']}*")

    # Исправленный SQL
    if llm_result.get('fixed_sql'):
        st.markdown("##### 🔧 Оптимизированный SQL")
        st.code(llm_result['fixed_sql'], language="sql")

    # Сырой ответ (для отладки)
    if llm_result.get('raw_content'):
        with st.expander("🔍 Сырой ответ LLM"):
            st.text(llm_result['raw_content'])


def _show_plan_comparison():
    """Отображает сравнение планов."""
    st.markdown("### 🔄 Сравнение планов")

    current_plan = st.session_state.get('current_plan')
    saved_plan = st.session_state.get('saved_plan')

    if not current_plan and not saved_plan:
        st.info("ℹ️ Нет планов для сравнения")
        return

    if current_plan and saved_plan:
        st.markdown("#### 📊 Сравнение текущего и сохраненного плана")

        # Сравниваем планы
        comparison = _compare_plans(current_plan, saved_plan)

        # Отображаем сравнение
        _display_plan_comparison(comparison)

    elif current_plan:
        st.info("ℹ️ Текущий план: есть, сохраненный план: нет")

    elif saved_plan:
        st.info("ℹ️ Текущий план: нет, сохраненный план: есть")


def _compare_plans(plan1: Dict[str, Any],
                   plan2: Dict[str, Any]) -> Dict[str, Any]:
    """Сравнивает два плана выполнения."""
    analysis1 = _analyze_plan(plan1)
    analysis2 = _analyze_plan(plan2)

    comparison = {
        'plan1': analysis1,
        'plan2': analysis2,
        'differences': {
            'cost_diff': analysis1['total_cost'] - analysis2['total_cost'],
            'rows_diff': analysis1['total_rows'] - analysis2['total_rows'],
            'warnings_diff': len(analysis1['warnings']) - len(analysis2['warnings'])
        }
    }

    return comparison


def _display_plan_comparison(comparison: Dict[str, Any]):
    """Отображает сравнение планов."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Текущий план")
        st.metric("Стоимость", f"{comparison['plan1']['total_cost']:.2f}")
        st.metric("Строки", f"{comparison['plan1']['total_rows']:,}")
        st.metric("Предупреждения", len(comparison['plan1']['warnings']))

    with col2:
        st.markdown("#### 💾 Сохраненный план")
        st.metric("Стоимость", f"{comparison['plan2']['total_cost']:.2f}")
        st.metric("Строки", f"{comparison['plan2']['total_rows']:,}")
        st.metric("Предупреждения", len(comparison['plan2']['warnings']))

    # Различия
    st.markdown("#### 🔄 Различия")
    diff = comparison['differences']

    if diff['cost_diff'] > 0:
        st.warning(f"⚠️ Текущий план дороже на {diff['cost_diff']:.2f}")
    elif diff['cost_diff'] < 0:
        st.success(f"✅ Текущий план дешевле на {abs(diff['cost_diff']):.2f}")
    else:
        st.info("ℹ️ Стоимость планов одинакова")


def _show_mock_explain_analysis():
    """Отображает mock данные для explain анализа."""
    st.markdown("### 📝 Ввод SQL запроса (Mock)")

    st.text_area(
        "SQL запрос",
        value="SELECT * FROM users WHERE created_at > '2024-01-01'",
        height=200,
        disabled=True
    )

    st.markdown("### 📊 План выполнения (Mock данные)")

    # Mock план
    mock_plan = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "users",
            "Total Cost": 1500.00,
            "Plan Rows": 10000,
            "Startup Cost": 0.00,
            "Actual Rows": 10000,
            "Actual Total Time": 45.123
        }
    }

    with st.expander("📋 JSON план выполнения (Mock)"):
        st.json(mock_plan)

    st.markdown("#### 📈 Сводка плана (Mock)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Общая стоимость", "1500.00")

    with col2:
        st.metric("📊 Строки", "10,000")

    with col3:
        st.metric("🔧 Типы узлов", "1")

    with col4:
        st.metric("⚠️ Предупреждения", "1")

    st.warning("⚠️ Последовательное сканирование таблицы")

    st.markdown("#### 🌳 Дерево плана выполнения (Mock)")

    mock_tree_data = pd.DataFrame({
        'level': [0],
        'node_type': ['Seq Scan'],
        'relation_name': ['users'],
        'total_cost': [1500.00],
        'plan_rows': [10000],
        'actual_rows': [10000],
        'actual_total_time': [45.123]
    })

    st.dataframe(mock_tree_data, width='stretch', hide_index=True)

    st.markdown("### 🤖 AI анализ плана выполнения (Mock)")
    st.info("ℹ️ AI анализ недоступен в mock режиме")
