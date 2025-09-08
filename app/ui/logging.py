"""Модуль для отображения логов и мониторинга PostgreSQL."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def show_logging_tab(dsn: str, mock_mode: bool = False):
    """Показать вкладку с логами и мониторингом."""
    st.markdown("## 📋 Логи и мониторинг")
    
    if mock_mode:
        _show_mock_logging()
        return
    
    try:
        # Получаем данные логов
        log_data = _get_log_data(dsn)
        
        if not log_data:
            st.warning("⚠️ Не удалось получить данные логов")
            return
        
        # Отображаем различные типы логов
        _show_error_logs(log_data.get('error_logs', []))
        _show_slow_queries(log_data.get('slow_queries', []))
        _show_connection_logs(log_data.get('connection_logs', []))
        
    except Exception as e:
        logger.error(f"Ошибка в show_logging_tab: {e}")
        st.error(f"❌ Ошибка получения логов: {e}")


def _get_log_data(dsn: str) -> dict:
    """Получить данные логов из базы данных."""
    import psycopg2
    
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                log_data = {}
                
                # Проверяем доступность pg_stat_statements
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension 
                        WHERE extname = 'pg_stat_statements'
                    )
                """)
                has_pg_stat_statements = cur.fetchone()[0]
                
                if has_pg_stat_statements:
                    # Медленные запросы (запросы с временем выполнения > 1000ms)
                    cur.execute("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            rows,
                            shared_blks_hit,
                            shared_blks_read
                        FROM pg_stat_statements 
                        WHERE mean_exec_time > 1000
                        ORDER BY total_exec_time DESC 
                        LIMIT 20
                    """)
                    log_data['slow_queries'] = cur.fetchall()
                
                # Активные подключения
                cur.execute("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query_start,
                        state_change,
                        query
                    FROM pg_stat_activity 
                    WHERE state IS NOT NULL
                    ORDER BY query_start DESC
                    LIMIT 50
                """)
                log_data['connection_logs'] = cur.fetchall()
                
                # Системные события (если доступны)
                try:
                    cur.execute("""
                        SELECT 
                            'system' as event_type,
                            now() as event_time,
                            'Database connection established' as message
                        LIMIT 1
                    """)
                    log_data['error_logs'] = cur.fetchall()
                except:
                    log_data['error_logs'] = []
                
                return log_data
                
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        return {}


def _show_error_logs(error_logs: list):
    """Показать логи ошибок."""
    st.markdown("### ❌ Логи ошибок")
    
    if not error_logs:
        st.info("ℹ️ Нет записей об ошибках")
        return
    
    # Создаем DataFrame
    columns = ['event_type', 'event_time', 'message']
    df = pd.DataFrame(error_logs, columns=columns)
    
    # Показываем таблицу
    st.dataframe(df, width='stretch', hide_index=True)


def _show_slow_queries(slow_queries: list):
    """Показать медленные запросы."""
    st.markdown("### 🐌 Медленные запросы")
    
    if not slow_queries:
        st.info("ℹ️ Нет медленных запросов (время выполнения > 1000ms)")
        return
    
    # Создаем DataFrame
    columns = [
        'query', 'calls', 'total_exec_time', 'mean_exec_time', 'rows',
        'shared_blks_hit', 'shared_blks_read'
    ]
    
    df = pd.DataFrame(slow_queries, columns=columns)
    
    # Добавляем вычисляемые колонки
    df['cache_hit_ratio'] = (df['shared_blks_hit'] / (df['shared_blks_hit'] + df['shared_blks_read'])).round(3)
    df['total_time_minutes'] = (df['total_exec_time'] / 60000).round(2)
    
    # Сокращаем длинные запросы для отображения
    df['query_short'] = df['query'].str[:100] + '...'
    
    # Показываем таблицу
    display_columns = ['query_short', 'calls', 'mean_exec_time', 'total_time_minutes', 'cache_hit_ratio']
    st.dataframe(df[display_columns], width='stretch', hide_index=True)
    
    # График времени выполнения
    if len(df) > 0:
        fig = px.bar(
            df.head(10),
            x='mean_exec_time',
            y='query_short',
            orientation='h',
            title="Топ-10 медленных запросов",
            labels={'mean_exec_time': 'Среднее время (мс)', 'query_short': 'Запрос'}
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)


def _show_connection_logs(connection_logs: list):
    """Показать логи подключений."""
    st.markdown("### 🔗 Логи подключений")
    
    if not connection_logs:
        st.info("ℹ️ Нет данных о подключениях")
        return
    
    # Создаем DataFrame
    columns = [
        'pid', 'usename', 'application_name', 'client_addr', 
        'state', 'query_start', 'state_change', 'query'
    ]
    
    df = pd.DataFrame(connection_logs, columns=columns)
    
    # Обрабатываем время
    if not df.empty and 'query_start' in df.columns:
        # Исправляем ошибку timezone - приводим к naive datetime
        current_time = datetime.now()
        query_start_times = pd.to_datetime(df['query_start'], utc=True).dt.tz_localize(None)
        df['duration'] = (current_time - query_start_times).dt.total_seconds().round(1)
    
    # Сокращаем длинные запросы
    if 'query' in df.columns:
        df['query_short'] = df['query'].str[:80] + '...'
    
    # Показываем таблицу
    display_columns = ['pid', 'usename', 'state', 'duration', 'query_short']
    available_columns = [col for col in display_columns if col in df.columns]
    
    st.dataframe(df[available_columns], width='stretch', hide_index=True)
    
    # Статистика по состояниям
    if 'state' in df.columns:
        state_counts = df['state'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Распределение по состояниям")
            st.dataframe(state_counts.reset_index(), width='stretch', hide_index=True)
        
        with col2:
            # Круговая диаграмма
            fig = px.pie(
                values=state_counts.values,
                names=state_counts.index,
                title="Состояния подключений"
            )
            st.plotly_chart(fig, use_container_width=True)


def _show_mock_logging():
    """Показать моковые логи для демонстрации."""
    st.markdown("### 🎭 Демо-режим: Логи и мониторинг")
    
    # Медленные запросы
    st.markdown("#### 🐌 Медленные запросы")
    
    mock_slow_queries = pd.DataFrame({
        'query': [
            'SELECT * FROM large_table WHERE complex_condition = $1',
            'UPDATE huge_table SET column = $1 WHERE id > $2',
            'SELECT COUNT(*) FROM joined_tables WHERE date_range > $1',
            'DELETE FROM old_data WHERE created_at < $1',
            'INSERT INTO logs SELECT * FROM temp_table'
        ],
        'calls': [25, 15, 8, 5, 3],
        'mean_exec_time': [2500, 1800, 1500, 1200, 1000],
        'total_time_minutes': [1.04, 0.45, 0.20, 0.10, 0.05],
        'cache_hit_ratio': [0.85, 0.78, 0.92, 0.88, 0.95]
    })
    
    st.dataframe(mock_slow_queries, width='stretch', hide_index=True)
    
    # График медленных запросов
    fig = px.bar(
        mock_slow_queries,
        x='mean_exec_time',
        y='query',
        orientation='h',
        title="Медленные запросы (время выполнения > 1000ms)",
        labels={'mean_exec_time': 'Среднее время (мс)', 'query': 'Запрос'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Логи подключений
    st.markdown("#### 🔗 Активные подключения")
    
    mock_connections = pd.DataFrame({
        'pid': [12345, 12346, 12347, 12348, 12349],
        'usename': ['app_user', 'admin', 'app_user', 'readonly_user', 'app_user'],
        'state': ['active', 'idle', 'active', 'idle in transaction', 'active'],
        'duration': [120.5, 300.2, 45.8, 180.1, 90.3],
        'query': [
            'SELECT * FROM users WHERE id = $1',
            'SELECT COUNT(*) FROM orders',
            'UPDATE products SET price = $1',
            'BEGIN; SELECT * FROM logs',
            'INSERT INTO sessions VALUES ($1, $2)'
        ]
    })
    
    st.dataframe(mock_connections, width='stretch', hide_index=True)
    
    # Статистика по состояниям
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Распределение по состояниям")
        state_counts = mock_connections['state'].value_counts()
        st.dataframe(state_counts.reset_index(), width='stretch', hide_index=True)
    
    with col2:
        # Круговая диаграмма
        fig = px.pie(
            values=state_counts.values,
            names=state_counts.index,
            title="Состояния подключений"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Логи ошибок
    st.markdown("#### ❌ Последние события")
    
    mock_events = pd.DataFrame({
        'event_type': ['connection', 'query', 'error', 'connection', 'query'],
        'event_time': [
            datetime.now() - timedelta(minutes=5),
            datetime.now() - timedelta(minutes=3),
            datetime.now() - timedelta(minutes=2),
            datetime.now() - timedelta(minutes=1),
            datetime.now() - timedelta(seconds=30)
        ],
        'message': [
            'New connection established from 192.168.1.100',
            'Slow query detected: SELECT * FROM large_table',
            'Connection timeout for user app_user',
            'Connection closed for user admin',
            'Query completed successfully'
        ]
    })
    
    st.dataframe(mock_events, width='stretch', hide_index=True)
