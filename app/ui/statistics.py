"""Модуль для вкладки 'Статистика'."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def show_statistics_tab(dsn: str, mock_mode: bool = False):
    """Отображает вкладку 'Статистика'."""
    st.markdown("## 📊 Статистика")

    if mock_mode:
        st.info("🎭 Mock режим: отображаются тестовые данные")
        _show_mock_statistics()
        return

    try:
        # Получаем статистику
        stats_data = _get_statistics_data(dsn)

        # Отображаем общую статистику
        _show_general_statistics(stats_data)

        # Отображаем статистику запросов
        _show_query_statistics(stats_data)

        # Отображаем статистику подключений
        _show_connection_statistics(stats_data)

        # Отображаем графики нагрузки
        _show_load_charts(stats_data)

    except Exception as e:
        st.error(f"Ошибка получения статистики: {str(e)}")
        logger.error(f"Ошибка в show_statistics_tab: {e}")


def _get_statistics_data(dsn: str) -> Dict[str, Any]:
    """Получает статистику базы данных."""
    stats_data = {
        'general': {},
        'queries': [],
        'connections': [],
        'load_metrics': []
    }

    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)

        with conn.cursor() as cur:
            # Общая статистика
            cur.execute("""
                SELECT 
                    (SELECT count(*) FROM pg_stat_activity) as active_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_in_transaction
            """)
            result = cur.fetchone()
            if result:
                stats_data['general'] = dict(result)

            # Статистика запросов (PostgreSQL 17 совместимость)
            cur.execute("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read,
                    shared_blks_dirtied,
                    shared_blks_written,
                    temp_blks_read,
                    temp_blks_written,
                    wal_records,
                    wal_bytes
                FROM pg_stat_statements 
                ORDER BY total_exec_time DESC 
                LIMIT 20
            """)
            queries = cur.fetchall()
            stats_data['queries'] = [dict(query) for query in queries]

            # Статистика подключений
            cur.execute("""
                SELECT 
                    datname,
                    usename,
                    application_name,
                    client_addr,
                    state,
                    query_start,
                    state_change,
                    backend_start,
                    query
                FROM pg_stat_activity 
                WHERE datname IS NOT NULL
                ORDER BY query_start DESC NULLS LAST
            """)
            connections = cur.fetchall()
            stats_data['connections'] = [dict(conn) for conn in connections]

            # Метрики нагрузки из pg_stat_statements
            cur.execute("""
                SELECT 
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    shared_blks_hit,
                    shared_blks_read,
                    temp_blks_read,
                    temp_blks_written
                FROM pg_stat_statements 
                WHERE calls > 0
                ORDER BY total_exec_time DESC
                LIMIT 100
            """)
            load_metrics = cur.fetchall()
            stats_data['load_metrics'] = [dict(metric) for metric in load_metrics]

        conn.close()

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        # Возвращаем пустые данные вместо исключения
        pass

    return stats_data


def _show_general_statistics(stats_data: Dict[str, Any]):
    """Отображает общую статистику."""
    st.markdown("### 📈 Общая статистика")

    general = stats_data.get('general', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🔗 Активные подключения",
            value=general.get('active_connections', 0)
        )

    with col2:
        st.metric(
            label="⚡ Активные запросы",
            value=general.get('active_queries', 0)
        )

    with col3:
        st.metric(
            label="😴 Неактивные подключения",
            value=general.get('idle_connections', 0)
        )

    with col4:
        st.metric(
            label="⏳ В транзакции",
            value=general.get('idle_in_transaction', 0)
        )


def _show_query_statistics(stats_data: Dict[str, Any]):
    """Отображает статистику запросов."""
    st.markdown("### 🔍 Статистика запросов")

    queries = stats_data.get('queries', [])

    if not queries:
        st.info("ℹ️ Нет данных о запросах (pg_stat_statements не доступен)")
        return

    # Создаем DataFrame
    queries_df = pd.DataFrame(queries)

    # Топ запросов по времени выполнения
    if not queries_df.empty:
        st.markdown("#### ⏱️ Топ запросов по времени выполнения")

        # Создаем график времени выполнения
        top_queries = queries_df.head(10).copy()
        top_queries['query_short'] = top_queries['query'].str[:50] + '...'

        fig_time = px.bar(
            top_queries,
            x='mean_exec_time',
            y='query_short',
            orientation='h',
            title="Среднее время выполнения запросов (мс)",
            labels={'mean_exec_time': 'Время (мс)', 'query_short': 'Запрос'},
            color='mean_exec_time',
            color_continuous_scale='Reds'
        )
        fig_time.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            margin=dict(l=20, r=100, t=50, b=50)  # Увеличиваем отступы
        )
        fig_time.update_traces(
            hovertemplate='<b>%{y}</b><br>Среднее время: %{x:.1f} мс<extra></extra>',
            text=[f"{x:.1f} мс" for x in top_queries['mean_exec_time']],  # Добавляем текст с временем
            textposition='outside',
            textfont=dict(size=13, color='white', family='Arial')  # Белые цифры, увеличенный размер
        )
        st.plotly_chart(fig_time, width='stretch')

        # Топ запросов по количеству вызовов
        st.markdown("#### 📞 Топ запросов по количеству вызовов")

        # Создаем улучшенный график с дополнительной информацией
        calls_queries = queries_df.head(10).copy()
        calls_queries['query_short'] = calls_queries['query'].str[:45] + '...'

        # Добавляем процент от общего количества вызовов
        total_calls = calls_queries['calls'].sum()
        calls_queries['calls_percentage'] = (calls_queries['calls'] / total_calls * 100).round(1)

        # Создаем график с дополнительными метриками
        fig_calls = px.bar(
            calls_queries,
            x='calls',
            y='query_short',
            orientation='h',
            title="Количество вызовов запросов",
            labels={'calls': 'Количество вызовов', 'query_short': 'Запрос'},
            color='calls',
            color_continuous_scale='Blues'
        )

        # Улучшаем отображение
        fig_calls.update_layout(
            height=600,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            title_font_size=16,
            font=dict(size=12),
            margin=dict(l=20, r=100, t=50, b=50)  # Увеличиваем отступы для текста
        )

        # Обновляем подсказки с дополнительной информацией
        fig_calls.update_traces(
            hovertemplate='<b>%{y}</b><br>'
            + 'Вызовов: %{x:,}<br>'
            + 'Процент от общего: %{customdata[0]}%<br>'
            + 'Среднее время: %{customdata[1]:.1f} мс<br>'
            + 'Общее время: %{customdata[2]:.1f} мс<extra></extra>',
            customdata=list(zip(
                calls_queries['calls_percentage'],
                calls_queries['mean_exec_time'],
                calls_queries['total_exec_time']
            ))
        )

        # Убираем цифры с количеством, оставляем только проценты
        fig_calls.update_traces(
            text=None,  # Убираем текст с количеством
            textposition=None
        )

        # Добавляем аннотации только с процентами
        max_calls = max(calls_queries['calls'])
        for i, row in calls_queries.iterrows():
            fig_calls.add_annotation(
                x=row['calls'] + max_calls * 0.03,  # Увеличиваем отступ
                y=row['query_short'],
                text=f"{row['calls_percentage']:.1f}%",  # Только проценты
                showarrow=False,
                font=dict(size=13, color='#333333', family='Arial'),  # Увеличиваем размер процентов
                xanchor='left',
                bgcolor='rgba(255,255,255,0.95)',  # Еще более непрозрачный фон
                bordercolor='rgba(0,0,0,0.3)',
                borderwidth=1
            )

        st.plotly_chart(fig_calls, width='stretch')

        # Добавляем круговую диаграмму распределения вызовов
        st.markdown("##### 🥧 Распределение вызовов")

        # Создаем круговую диаграмму для топ-5 запросов
        pie_data = calls_queries.head(5).copy()
        pie_data['query_label'] = pie_data['query'].str[:30] + '...'

        fig_pie = px.pie(
            pie_data,
            values='calls',
            names='query_label',
            title="Топ-5 запросов по количеству вызовов",
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont=dict(size=14, family='Arial'),  # Увеличиваем размер надписей
            hovertemplate='<b>%{label}</b><br>'
                         + 'Вызовов: %{value}<br>'
                         + 'Процент: %{percent}<extra></extra>'
        )

        fig_pie.update_layout(
            height=500,  # Увеличиваем высоту диаграммы
            showlegend=True,
            font=dict(size=14, family='Arial'),  # Увеличиваем размер шрифта
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01,
                font=dict(size=12, family='Arial')  # Увеличиваем размер легенды
            )
        )

        st.plotly_chart(fig_pie, width='stretch')

        # Добавляем дополнительную статистику по вызовам
        col1, col2, col3 = st.columns(3)

        with col1:
            most_called = calls_queries.iloc[0]
            st.metric(
                "🔥 Самый частый запрос",
                f"{most_called['calls']:,} вызовов",
                help=f"Среднее время: {most_called['mean_exec_time']:.1f} мс"
            )

        with col2:
            avg_calls = calls_queries['calls'].mean()
            st.metric(
                "📊 Среднее количество вызовов",
                f"{avg_calls:.0f}",
                help="Среднее по топ-10 запросам"
            )

        with col3:
            top_3_percentage = calls_queries.head(3)['calls_percentage'].sum()
            st.metric(
                "🎯 Топ-3 запросов",
                f"{top_3_percentage:.1f}% от общего",
                help="Процент вызовов от топ-3 запросов"
            )

        # Таблица с детальной информацией
        st.markdown("#### 📋 Детальная статистика запросов")

        # Создаем улучшенную таблицу
        display_df = queries_df.copy()

        # Сокращаем длинные запросы для отображения
        display_df['query_short'] = display_df['query'].str[:80] + '...'

        # Добавляем вычисляемые колонки
        display_df['cache_hit_ratio'] = (display_df['shared_blks_hit']
                                         / (display_df['shared_blks_hit'] + display_df['shared_blks_read'] + 1) * 100).round(1)
        display_df['total_time_minutes'] = (display_df['total_exec_time'] / 1000 / 60).round(2)
        display_df['avg_rows_per_call'] = (display_df['rows'] / display_df['calls']).round(0)

        # Сортируем по общему времени выполнения
        display_df = display_df.sort_values('total_exec_time', ascending=False)

        # Отображаем таблицу с улучшенной конфигурацией
        st.dataframe(
            display_df[['query_short', 'calls', 'total_time_minutes', 'mean_exec_time',
                       'avg_rows_per_call', 'cache_hit_ratio', 'shared_blks_hit', 'shared_blks_read']],
            width='stretch',
            hide_index=True,
            column_config={
                'query_short': st.column_config.TextColumn(
                    'Запрос',
                    width='large',
                    help='SQL запрос (сокращенный)'
                ),
                'calls': st.column_config.NumberColumn(
                    'Вызовы',
                    format='%d',
                    help='Количество выполнений запроса'
                ),
                'total_time_minutes': st.column_config.NumberColumn(
                    'Общее время (мин)',
                    format='%.2f',
                    help='Общее время выполнения в минутах'
                ),
                'mean_exec_time': st.column_config.NumberColumn(
                    'Среднее время (мс)',
                    format='%.1f',
                    help='Среднее время выполнения в миллисекундах'
                ),
                'avg_rows_per_call': st.column_config.NumberColumn(
                    'Строк/вызов',
                    format='%.0f',
                    help='Среднее количество строк на вызов'
                ),
                'cache_hit_ratio': st.column_config.NumberColumn(
                    'Кэш хит (%)',
                    format='%.1f%%',
                    help='Процент попаданий в кэш'
                ),
                'shared_blks_hit': st.column_config.NumberColumn(
                    'Блоки в кэше',
                    format='%d',
                    help='Количество блоков, прочитанных из кэша'
                ),
                'shared_blks_read': st.column_config.NumberColumn(
                    'Блоки с диска',
                    format='%d',
                    help='Количество блоков, прочитанных с диска'
                )
            }
        )

        # Добавляем сводную статистику
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_calls = display_df['calls'].sum()
            st.metric("📞 Общее количество вызовов", f"{total_calls:,}")

        with col2:
            total_time_minutes = display_df['total_time_minutes'].sum()
            total_time_hours = total_time_minutes / 60

            # Показываем в часах, если больше 1 часа, иначе в минутах
            if total_time_hours >= 1:
                st.metric("⏱️ Общее время выполнения", f"{total_time_hours:.1f} ч")
            else:
                st.metric("⏱️ Общее время выполнения", f"{total_time_minutes:.1f} мин")

        with col3:
            avg_cache_hit = display_df['cache_hit_ratio'].mean()
            st.metric("💾 Средний кэш хит", f"{avg_cache_hit:.1f}%")

        with col4:
            slowest_query_time = display_df['mean_exec_time'].max()
            st.metric("🐌 Самый медленный запрос", f"{slowest_query_time:.1f} мс")

        # LLM анализ запросов
        _show_llm_query_analysis(queries_df)


def _show_connection_statistics(stats_data: Dict[str, Any]):
    """Отображает статистику подключений."""
    st.markdown("### 🔗 Статистика подключений")

    connections = stats_data.get('connections', [])

    if not connections:
        st.info("ℹ️ Нет данных о подключениях")
        return

    # Создаем DataFrame
    connections_df = pd.DataFrame(connections)

    # Статистика по состояниям
    if not connections_df.empty:
        st.markdown("#### 📊 Подключения по состояниям")

        state_counts = connections_df['state'].value_counts()

        fig_states = px.pie(
            values=state_counts.values,
            names=state_counts.index,
            title="Распределение подключений по состояниям"
        )
        st.plotly_chart(fig_states, width='stretch')

        # Таблица активных подключений
        st.markdown("#### 📋 Активные подключения")

        active_connections = connections_df[connections_df['state'] == 'active']

        if not active_connections.empty:
            # Улучшаем отображение времени
            display_connections = active_connections.copy()
            # Исправляем ошибку timezone - приводим к naive datetime
            current_time = datetime.now()
            query_start_times = pd.to_datetime(display_connections['query_start'], utc=True).dt.tz_localize(None)
            display_connections['query_duration'] = (
                current_time - query_start_times
            ).dt.total_seconds().round(1)

            # Сокращаем длинные запросы
            display_connections['query_short'] = display_connections['query'].str[:60] + '...'

            st.dataframe(
                display_connections[['datname', 'usename', 'application_name', 'client_addr',
                                     'query_duration', 'query_short']],
                width='stretch',
                hide_index=True,
                column_config={
                    'datname': st.column_config.TextColumn(
                        'База данных',
                        width='medium',
                        help='Название базы данных'
                    ),
                    'usename': st.column_config.TextColumn(
                        'Пользователь',
                        width='medium',
                        help='Имя пользователя'
                    ),
                    'application_name': st.column_config.TextColumn(
                        'Приложение',
                        width='medium',
                        help='Название приложения'
                    ),
                    'client_addr': st.column_config.TextColumn(
                        'IP адрес',
                        width='medium',
                        help='IP адрес клиента'
                    ),
                    'query_duration': st.column_config.NumberColumn(
                        'Длительность (сек)',
                        format='%.1f',
                        help='Время выполнения текущего запроса'
                    ),
                    'query_short': st.column_config.TextColumn(
                        'Текущий запрос',
                        width='large',
                        help='SQL запрос (сокращенный)'
                    )
                }
            )
        else:
            st.info("ℹ️ Нет активных подключений")

        # Сводная статистика подключений
        st.markdown("#### 📊 Сводная статистика подключений")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_connections = len(connections_df)
            st.metric("🔗 Всего подключений", total_connections)

        with col2:
            active_count = len(connections_df[connections_df['state'] == 'active'])
            st.metric("⚡ Активных", active_count)

        with col3:
            idle_count = len(connections_df[connections_df['state'] == 'idle'])
            st.metric("😴 Неактивных", idle_count)

        with col4:
            idle_in_transaction = len(connections_df[connections_df['state'] == 'idle in transaction'])
            st.metric("⏳ В транзакции", idle_in_transaction)


def _show_load_charts(stats_data: Dict[str, Any]):
    """Строит графики нагрузки."""
    st.markdown("### 📈 Графики нагрузки")

    # Создаем mock данные для демонстрации
    import numpy as np

    # Генерируем данные за последние 24 часа
    hours = 24
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]

    # Mock данные нагрузки
    cpu_usage = np.random.normal(45, 15, hours)
    cpu_usage = np.clip(cpu_usage, 0, 100)

    memory_usage = np.random.normal(60, 10, hours)
    memory_usage = np.clip(memory_usage, 0, 100)

    # Создаем DataFrame
    load_df = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage
    })

    # График нагрузки CPU
    fig_cpu = go.Figure()
    fig_cpu.add_trace(go.Scatter(
        x=load_df['timestamp'],
        y=load_df['cpu_usage'],
        mode='lines+markers',
        name='CPU Usage',
        line=dict(color='#336791', width=2)
    ))
    fig_cpu.update_layout(
        title="Нагрузка CPU (%)",
        xaxis_title="Время",
        yaxis_title="Использование CPU (%)",
        height=300
    )
    st.plotly_chart(fig_cpu, width='stretch')

    # График использования памяти
    fig_memory = go.Figure()
    fig_memory.add_trace(go.Scatter(
        x=load_df['timestamp'],
        y=load_df['memory_usage'],
        mode='lines+markers',
        name='Memory Usage',
        line=dict(color='#4a90a4', width=2)
    ))
    fig_memory.update_layout(
        title="Использование памяти (%)",
        xaxis_title="Время",
        yaxis_title="Использование памяти (%)",
        height=300
    )
    st.plotly_chart(fig_memory, width='stretch')


def _show_mock_statistics():
    """Отображает mock статистику."""
    st.markdown("### 📈 Общая статистика (Mock)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="🔗 Активные подключения", value=12)

    with col2:
        st.metric(label="⚡ Активные запросы", value=3)

    with col3:
        st.metric(label="😴 Неактивные подключения", value=8)

    with col4:
        st.metric(label="⏳ В транзакции", value=1)

    st.markdown("### 🔍 Статистика запросов (Mock)")

    # Mock данные запросов
    mock_queries = pd.DataFrame({
        'query': [
            'SELECT * FROM users WHERE id = $1',
            'SELECT COUNT(*) FROM orders WHERE created_at > $1',
            'UPDATE products SET price = $1 WHERE id = $2',
            'INSERT INTO logs (message, level) VALUES ($1, $2)',
            'SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id'
        ],
        'calls': [1250, 890, 450, 320, 180],
        'total_time': [12500, 8900, 4500, 3200, 1800],
        'mean_time': [10.0, 10.0, 10.0, 10.0, 10.0],
        'rows': [1250, 890, 450, 320, 180]
    })

    st.dataframe(mock_queries, width='stretch', hide_index=True)

    st.markdown("### 🔗 Статистика подключений (Mock)")

    # Mock данные подключений
    mock_sessions = pd.DataFrame({
        'datname': ['postgres', 'postgres', 'postgres', 'postgres'],
        'usename': ['postgres', 'app_user', 'readonly_user', 'admin'],
        'application_name': ['psql', 'web_app', 'analytics', 'backup'],
        'client_addr': ['127.0.0.1', '192.168.1.100', '192.168.1.101', '10.0.0.5'],
        'state': ['active', 'idle', 'active', 'idle in transaction'],
        'query_start': [
            datetime.now() - timedelta(minutes=5),
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=2),
            datetime.now() - timedelta(minutes=15)
        ]
    })

    st.dataframe(mock_sessions, width='stretch', hide_index=True)

    st.markdown("### 📈 Графики нагрузки (Mock)")

    # Mock график
    import numpy as np

    hours = 24
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
    cpu_usage = np.random.normal(45, 15, hours)
    cpu_usage = np.clip(cpu_usage, 0, 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=cpu_usage,
        mode='lines+markers',
        name='CPU Usage',
        line=dict(color='#336791', width=2)
    ))
    fig.update_layout(
        title="Нагрузка CPU (%) - Mock данные",
        xaxis_title="Время",
        yaxis_title="Использование CPU (%)",
        height=400
    )
    st.plotly_chart(fig, width='stretch')


def _show_llm_query_analysis(queries_df: pd.DataFrame):
    """Отображает LLM анализ запросов в автоматическом режиме."""
    st.markdown("#### 🤖 AI Анализ запросов")

    # Проверяем настройки AI
    if not st.session_state.get('enable_ai', False):
        st.info("ℹ️ AI анализ отключен. Включите AI в настройках для анализа запросов.")
        return

    # Автоматический анализ при загрузке страницы
    if 'statistics_analyzed' not in st.session_state:
        with st.spinner("🤖 AI анализирует запросы..."):
            try:
                import asyncio
                from app.llm_integration import LLMIntegration

                # Проверяем наличие API ключа
                api_key = st.session_state.get('openai_api_key', '')
                if not api_key:
                    st.error("""❌ **OpenAI API ключ не настроен**

💡 **Как настроить API ключ:**
1. Откройте sidebar (левая панель)
2. Найдите раздел "🤖 AI настройки"
3. Введите ваш OpenAI API ключ в поле "OpenAI API ключ"

🔗 **Где получить API ключ:**
- Перейдите на https://platform.openai.com/api-keys
- Создайте новый API ключ
- Скопируйте ключ и вставьте в настройки

⚙️ **Текущие настройки:**
- Модель: {st.session_state.get('openai_model', 'gpt-4o-mini')}""")
                    st.session_state['statistics_analyzed'] = True
                    return

                # Берем топ-5 самых медленных запросов для анализа
                top_queries = queries_df.head(5)

                # Подготавливаем данные для анализа
                analysis_data = []
                for _, row in top_queries.iterrows():
                    analysis_data.append({
                        'query': row['query'][:500],  # Ограничиваем длину
                        'calls': row['calls'],
                        'mean_exec_time': row['mean_exec_time'],
                        'total_exec_time': row['total_exec_time'],
                        'rows': row['rows'],
                        'shared_blks_hit': row['shared_blks_hit'],
                        'shared_blks_read': row['shared_blks_read']
                    })

                # Создаем промпт для анализа
                prompt = f"""
                Проанализируй следующие медленные запросы PostgreSQL и дай рекомендации по оптимизации.
                
                Статистика запросов:
                {json.dumps(analysis_data, indent=2, ensure_ascii=False)}
                
                Начни сразу с рекомендаций в формате:
                ### Название рекомендации.
                Приоритет: высокий/средний/низкий
                Категория: query_optimization/index_optimization/configuration_optimization
                Объяснение: Подробное объяснение проблемы и решения
                Ожидаемое улучшение: Описание ожидаемых улучшений
                Уверенность: 0.0-1.0
                ---
                
                Дай 3-5 рекомендаций по оптимизации самых медленных запросов.
                """

                # Инициализируем LLM
                llm_config = {
                    'openai_api_key': api_key,
                    'openai_model': st.session_state.get('openai_model', 'gpt-4o-mini'),
                    'openai_temperature': 0.3,
                    'enable_proxy': st.session_state.get('enable_proxy', True),
                    'proxy_host': st.session_state.get('proxy_host', 'localhost'),
                    'proxy_port': st.session_state.get('proxy_port', 1080)
                }

                llm = LLMIntegration(llm_config)

                # Создаем фиктивный execution_plan для анализа запросов
                mock_execution_plan = {
                    'type': 'query_analysis',
                    'queries': analysis_data,
                    'prompt': prompt
                }

                # Получаем ответ от LLM через правильный метод
                async def get_async_recommendations():
                    return await llm.get_recommendations(
                        sql_query=prompt,
                        execution_plan=mock_execution_plan,
                        db_schema=analysis_data
                    )

                # Запускаем асинхронную функцию
                recommendations = asyncio.run(get_async_recommendations())

                # Сохраняем результат в session_state
                if recommendations:
                    st.session_state['statistics_analysis'] = recommendations
                else:
                    st.error("❌ Не удалось получить рекомендации от AI. Проверьте настройки API ключей и прокси.")

                st.session_state['statistics_analyzed'] = True

            except Exception as e:
                logger.error(f"Ошибка LLM анализа запросов: {e}")
                error_msg = f"❌ Ошибка получения рекомендаций: {str(e)}"

                # Добавляем дополнительную информацию об ошибке
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    error_msg += "\n\n💡 **Проблема:** Неверный API ключ OpenAI"
                    error_msg += "\n🔧 **Решение:** Проверьте API ключ в настройках sidebar"
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    error_msg += "\n\n💡 **Проблема:** API ключ не имеет доступа к OpenAI API"
                    error_msg += "\n🔧 **Решение:** Проверьте права доступа API ключа"
                elif "httpx" in str(e):
                    error_msg += "\n\n💡 **Проблема:** Библиотека httpx не установлена"
                    error_msg += "\n🔧 **Решение:** Установите httpx: `pip install httpx[socks]`"
                elif "proxy" in str(e).lower():
                    error_msg += "\n\n💡 **Проблема:** Прокси не работает"
                    error_msg += "\n🔧 **Решение:** Проверьте настройки прокси в sidebar"
                elif "timeout" in str(e).lower():
                    error_msg += "\n\n💡 **Проблема:** Таймаут подключения"
                    error_msg += "\n🔧 **Решение:** Проверьте интернет-соединение и настройки прокси"
                else:
                    error_msg += "\n\n💡 **Общие рекомендации:**"
                    error_msg += "\n- Проверьте API ключ OpenAI"
                    error_msg += "\n- Убедитесь, что прокси работает (если включен)"
                    error_msg += "\n- Проверьте интернет-соединение"

                st.error(error_msg)
                st.session_state['statistics_analyzed'] = True

    # Отображаем сохраненные рекомендации
    if 'statistics_analysis' in st.session_state:
        st.markdown("#### 🎯 Рекомендации по оптимизации запросов")
        _display_llm_analysis(st.session_state['statistics_analysis'])

    # Кнопка для повторного анализа
    if st.button("🔄 Обновить анализ", help="Повторить AI анализ запросов"):
        st.session_state['statistics_analyzed'] = False
        st.rerun()


def _display_llm_analysis(recommendations):
    """Отображает результат LLM анализа."""
    try:
        if not recommendations:
            st.error("❌ Не удалось получить рекомендации от AI")
            return

        # Отображаем рекомендации
        for rec in recommendations:
            priority = rec.priority if hasattr(rec, 'priority') else 'средний'
            category = rec.category if hasattr(rec, 'category') else 'query_optimization'
            description = rec.description if hasattr(rec, 'description') else ''
            expected_improvement = rec.expected_improvement if hasattr(rec, 'expected_improvement') else ''
            confidence = rec.confidence if hasattr(rec, 'confidence') else 0.5
            reasoning = rec.reasoning if hasattr(rec, 'reasoning') else ''

            # Эмодзи для приоритета
            priority_emoji = "🔴" if priority == "высокий" else "🟡" if priority == "средний" else "🟢"

            st.markdown(f"### {priority_emoji} {description}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Приоритет:** {priority}")
                st.markdown(f"**Категория:** {category}")
            with col2:
                st.markdown(f"**Уверенность:** {confidence:.1%}")

            if reasoning:
                st.markdown(f"**Объяснение:** {reasoning}")

            if expected_improvement:
                st.markdown(f"**Ожидаемое улучшение:** {expected_improvement}")

            st.markdown("---")

    except Exception as e:
        logger.error(f"Ошибка отображения LLM анализа: {e}")
        st.error(f"❌ Ошибка отображения анализа: {str(e)}")
