"""Модуль для отображения метрик производительности PostgreSQL."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def show_metrics_tab(dsn: str, mock_mode: bool = False):
    """Показать вкладку с метриками производительности."""
    st.markdown("## 📊 Метрики производительности")
    
    if mock_mode:
        _show_mock_metrics()
        return
    
    try:
        # Получаем метрики из базы данных
        metrics_data = _get_metrics_data(dsn)
        
        if not metrics_data:
            st.warning("⚠️ Не удалось получить метрики из базы данных")
            return
        
        # Отображаем метрики
        _show_system_metrics(metrics_data.get('system_metrics', {}))
        _show_query_metrics(metrics_data.get('query_metrics', []))
        _show_connection_metrics(metrics_data.get('connection_metrics', []))
        
    except Exception as e:
        logger.error(f"Ошибка в show_metrics_tab: {e}")
        st.error(f"❌ Ошибка получения метрик: {e}")


def _get_metrics_data(dsn: str) -> dict:
    """Получить метрики из базы данных."""
    import psycopg2
    
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                metrics_data = {}
                
                # Проверяем доступность pg_stat_statements
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension 
                        WHERE extname = 'pg_stat_statements'
                    )
                """)
                has_pg_stat_statements = cur.fetchone()[0]
                
                if has_pg_stat_statements:
                    # Метрики запросов
                    cur.execute("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            rows,
                            shared_blks_hit,
                            shared_blks_read,
                            temp_blks_written,
                            local_blks_written
                        FROM pg_stat_statements 
                        ORDER BY total_exec_time DESC 
                        LIMIT 50
                    """)
                    metrics_data['query_metrics'] = cur.fetchall()
                
                # Метрики подключений
                cur.execute("""
                    SELECT 
                        state,
                        COUNT(*) as count
                    FROM pg_stat_activity 
                    WHERE state IS NOT NULL
                    GROUP BY state
                """)
                metrics_data['connection_metrics'] = cur.fetchall()
                
                # Системные метрики
                cur.execute("""
                    SELECT 
                        setting as shared_buffers,
                        (SELECT setting FROM pg_settings WHERE name = 'work_mem') as work_mem,
                        (SELECT setting FROM pg_settings WHERE name = 'maintenance_work_mem') as maintenance_work_mem,
                        (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_settings 
                    WHERE name = 'shared_buffers'
                """)
                system_row = cur.fetchone()
                if system_row:
                    metrics_data['system_metrics'] = {
                        'shared_buffers': system_row[0],
                        'work_mem': system_row[1],
                        'maintenance_work_mem': system_row[2],
                        'max_connections': system_row[3]
                    }
                
                return metrics_data
                
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        return {}


def _show_system_metrics(system_metrics: dict):
    """Показать системные метрики."""
    if not system_metrics:
        return
    
    st.markdown("### ⚙️ Системные параметры")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Shared Buffers", system_metrics.get('shared_buffers', 'N/A'))
    
    with col2:
        st.metric("💾 Work Memory", system_metrics.get('work_mem', 'N/A'))
    
    with col3:
        st.metric("🔧 Maintenance Memory", system_metrics.get('maintenance_work_mem', 'N/A'))
    
    with col4:
        st.metric("🔗 Max Connections", system_metrics.get('max_connections', 'N/A'))


def _show_query_metrics(query_metrics: list):
    """Показать метрики запросов."""
    if not query_metrics:
        st.info("ℹ️ Нет данных о запросах (pg_stat_statements не доступен)")
        return
    
    st.markdown("### 📈 Метрики запросов")
    
    # Создаем DataFrame
    columns = [
        'query', 'calls', 'total_exec_time', 'mean_exec_time', 'rows',
        'shared_blks_hit', 'shared_blks_read', 'temp_blks_written', 'local_blks_written'
    ]
    
    df = pd.DataFrame(query_metrics, columns=columns)
    
    # Добавляем вычисляемые колонки
    df['cache_hit_ratio'] = (df['shared_blks_hit'] / (df['shared_blks_hit'] + df['shared_blks_read'])).round(3)
    df['total_time_minutes'] = (df['total_exec_time'] / 60000).round(2)
    
    # Показываем топ-10 запросов
    top_queries = df.head(10)
    
    st.dataframe(
        top_queries[['query', 'calls', 'total_time_minutes', 'mean_exec_time', 'cache_hit_ratio']],
        width='stretch',
        hide_index=True
    )
    
    # График времени выполнения
    if len(top_queries) > 0:
        fig = px.bar(
            top_queries.head(5),
            x='mean_exec_time',
            y='query',
            orientation='h',
            title="Топ-5 запросов по времени выполнения",
            labels={'mean_exec_time': 'Среднее время (мс)', 'query': 'Запрос'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def _show_connection_metrics(connection_metrics: list):
    """Показать метрики подключений."""
    if not connection_metrics:
        st.info("ℹ️ Нет данных о подключениях")
        return
    
    st.markdown("### 🔗 Статистика подключений")
    
    # Создаем DataFrame
    df = pd.DataFrame(connection_metrics, columns=['state', 'count'])
    
    # Показываем таблицу
    st.dataframe(df, width='stretch', hide_index=True)
    
    # Круговая диаграмма
    if len(df) > 0:
        fig = px.pie(
            df,
            values='count',
            names='state',
            title="Распределение состояний подключений"
        )
        st.plotly_chart(fig, use_container_width=True)


def _show_mock_metrics():
    """Показать моковые метрики для демонстрации."""
    st.markdown("### 🎭 Демо-режим: Метрики производительности")
    
    # Системные метрики
    st.markdown("#### ⚙️ Системные параметры")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Shared Buffers", "128MB")
    
    with col2:
        st.metric("💾 Work Memory", "4MB")
    
    with col3:
        st.metric("🔧 Maintenance Memory", "64MB")
    
    with col4:
        st.metric("🔗 Max Connections", "100")
    
    # Метрики запросов
    st.markdown("#### 📈 Метрики запросов")
    
    mock_queries = pd.DataFrame({
        'query': [
            'SELECT * FROM users WHERE id = $1',
            'SELECT COUNT(*) FROM orders WHERE date > $1',
            'UPDATE products SET price = $1 WHERE id = $2',
            'INSERT INTO logs (message) VALUES ($1)',
            'DELETE FROM temp_data WHERE created < $1'
        ],
        'calls': [1250, 890, 450, 320, 180],
        'total_exec_time': [12500, 8900, 4500, 3200, 1800],
        'mean_exec_time': [10.0, 10.0, 10.0, 10.0, 10.0],
        'cache_hit_ratio': [0.95, 0.87, 0.92, 0.89, 0.91]
    })
    
    st.dataframe(mock_queries, width='stretch', hide_index=True)
    
    # График
    fig = px.bar(
        mock_queries,
        x='calls',
        y='query',
        orientation='h',
        title="Топ запросов по количеству вызовов",
        labels={'calls': 'Количество вызовов', 'query': 'Запрос'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Статистика подключений
    st.markdown("#### 🔗 Статистика подключений")
    
    mock_connections = pd.DataFrame({
        'state': ['active', 'idle', 'idle in transaction', 'disabled'],
        'count': [5, 12, 3, 1]
    })
    
    st.dataframe(mock_connections, width='stretch', hide_index=True)
    
    # Круговая диаграмма
    fig = px.pie(
        mock_connections,
        values='count',
        names='state',
        title="Распределение состояний подключений"
    )
    st.plotly_chart(fig, use_container_width=True)
