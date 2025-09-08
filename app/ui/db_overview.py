"""Модуль для вкладки 'Обзор БД'."""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def show_db_overview_tab(dsn: str, mock_mode: bool = False):
    """Отображает вкладку 'Обзор БД'."""
    st.markdown("## 🗄️ Обзор базы данных")
    
    if mock_mode:
        st.info("🎭 Mock режим: отображаются тестовые данные")
        _show_mock_db_overview()
        return
    
    try:
        # Получаем информацию о базе данных
        db_info = _get_database_info(dsn)
        
        # Отображаем сводку
        _show_database_summary(db_info)
        
        # Отображаем структуру БД
        _show_database_structure(db_info)
        
        # Отображаем ER-диаграмму
        _show_er_diagram(db_info)
        
        # Отображаем версию PostgreSQL и параметры подключения
        _show_connection_info(db_info)
        
    except Exception as e:
        st.error(f"Ошибка получения информации о БД: {str(e)}")
        logger.error(f"Ошибка в show_db_overview_tab: {e}")


def _get_database_info(dsn: str) -> Dict[str, Any]:
    """Получает информацию о базе данных."""
    db_info = {
        'version': None,
        'tables': [],
        'indexes': [],
        'relationships': [],
        'table_count': 0,
        'index_count': 0,
        'total_size': 0,
        'connection_info': {}
    }
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cur:
            # Версия PostgreSQL
            cur.execute("SELECT version();")
            result = cur.fetchone()
            db_info['version'] = result['version'] if result else None
            
            # Информация о подключении
            cur.execute("""
                SELECT 
                    current_database() as database,
                    current_user as user,
                    inet_server_addr() as host,
                    inet_server_port() as port
            """)
            result = cur.fetchone()
            db_info['connection_info'] = dict(result) if result else {}
            
            # Список таблиц
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY size_bytes DESC
            """)
            tables = cur.fetchall()
            db_info['tables'] = [dict(table) for table in tables]
            db_info['table_count'] = len(db_info['tables'])
            
            # Список индексов
            cur.execute("""
                SELECT 
                    schemaname,
                    indexname,
                    tablename,
                    indexdef,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
                FROM pg_indexes 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
            """)
            indexes = cur.fetchall()
            db_info['indexes'] = [dict(index) for index in indexes]
            db_info['index_count'] = len(db_info['indexes'])
            
            # Связи между таблицами
            cur.execute("""
                SELECT 
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name
            """)
            relationships = cur.fetchall()
            db_info['relationships'] = [dict(rel) for rel in relationships]
            
            # Общий размер базы данных
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as total_size")
            result = cur.fetchone()
            db_info['total_size'] = result['total_size'] if result else 'N/A'
            
        conn.close()
                
    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        raise
    
    return db_info


def _show_database_summary(db_info: Dict[str, Any]):
    """Отображает сводку по базе данных."""
    st.markdown("### 📊 Сводка")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Таблицы",
            value=db_info['table_count']
        )
    
    with col2:
        st.metric(
            label="🔍 Индексы",
            value=db_info['index_count']
        )
    
    with col3:
        st.metric(
            label="🔗 Связи",
            value=len(db_info['relationships'])
        )
    
    with col4:
        st.metric(
            label="💾 Размер БД",
            value=db_info['total_size']
        )


def _show_database_structure(db_info: Dict[str, Any]):
    """Отображает структуру базы данных."""
    st.markdown("### 🏗️ Структура базы данных")
    
    # Таблицы
    if db_info['tables']:
        st.markdown("#### 📋 Таблицы")
        
        # Создаем DataFrame для таблиц
        tables_df = pd.DataFrame(db_info['tables'])
        
        # Отображаем таблицы
        st.dataframe(
            tables_df,
            width='stretch',
            hide_index=True
        )
        
        # График размеров таблиц
        if len(tables_df) > 0 and 'size_bytes' in tables_df.columns:
            # Фильтруем таблицы с валидными размерами
            valid_tables = tables_df[tables_df['size_bytes'].notna()]
            if len(valid_tables) > 0:
                fig = px.bar(
                    valid_tables.head(10),
                    x='tablename',
                    y='size_bytes',
                    title="Топ-10 таблиц по размеру",
                    labels={'size_bytes': 'Размер (байты)', 'tablename': 'Таблица'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, width='stretch')
    else:
        st.info("ℹ️ Таблицы не найдены")
    
    # Индексы
    if db_info['indexes']:
        st.markdown("#### 🔍 Индексы")
        
        indexes_df = pd.DataFrame(db_info['indexes'])
        st.dataframe(
            indexes_df,
            width='stretch',
            hide_index=True
        )
    else:
        st.info("ℹ️ Индексы не найдены")


def _show_er_diagram(db_info: Dict[str, Any]):
    """Отображает ER-диаграмму."""
    st.markdown("### 🔗 ER-диаграмма")
    
    if not db_info['relationships']:
        st.info("ℹ️ Связи между таблицами не найдены")
        return
    
    # Создаем простую ER-диаграмму
    relationships_df = pd.DataFrame(db_info['relationships'])
    
    # Группируем по таблицам
    table_connections = {}
    for _, rel in relationships_df.iterrows():
        table = f"{rel['table_schema']}.{rel['table_name']}"
        foreign_table = f"{rel['foreign_table_schema']}.{rel['foreign_table_name']}"
        
        if table not in table_connections:
            table_connections[table] = []
        table_connections[table].append(foreign_table)
    
    # Отображаем связи
    st.markdown("#### Связи между таблицами:")
    for table, connections in table_connections.items():
        st.write(f"**{table}** → {', '.join(connections)}")
    
    # Создаем визуальную диаграмму
    if len(relationships_df) > 0:
        st.markdown("#### Визуальная схема связей:")
        
        # Создаем граф связей
        import plotly.graph_objects as go
        
        # Получаем уникальные таблицы
        all_tables = set()
        for _, rel in relationships_df.iterrows():
            all_tables.add(f"{rel['table_schema']}.{rel['table_name']}")
            all_tables.add(f"{rel['foreign_table_schema']}.{rel['foreign_table_name']}")
        
        all_tables = list(all_tables)
        
        # Создаем позиции для узлов
        import numpy as np
        n_tables = len(all_tables)
        angles = np.linspace(0, 2*np.pi, n_tables, endpoint=False)
        x_pos = np.cos(angles)
        y_pos = np.sin(angles)
        
        # Создаем граф
        fig = go.Figure()
        
        # Добавляем узлы (таблицы)
        fig.add_trace(go.Scatter(
            x=x_pos,
            y=y_pos,
            mode='markers+text',
            marker=dict(size=20, color='lightblue'),
            text=all_tables,
            textposition="middle center",
            name="Таблицы"
        ))
        
        # Добавляем связи
        for _, rel in relationships_df.iterrows():
            table1 = f"{rel['table_schema']}.{rel['table_name']}"
            table2 = f"{rel['foreign_table_schema']}.{rel['foreign_table_name']}"
            
            idx1 = all_tables.index(table1)
            idx2 = all_tables.index(table2)
            
            fig.add_trace(go.Scatter(
                x=[x_pos[idx1], x_pos[idx2]],
                y=[y_pos[idx1], y_pos[idx2]],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False
            ))
        
        fig.update_layout(
            title="ER-диаграмма базы данных",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')


def _show_connection_info(db_info: Dict[str, Any]):
    """Отображает информацию о подключении."""
    st.markdown("### 🔌 Информация о подключении")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🐘 Версия PostgreSQL")
        if db_info['version']:
            st.code(db_info['version'])
        else:
            st.info("Версия не определена")
    
    with col2:
        st.markdown("#### 📡 Параметры подключения")
        if db_info['connection_info']:
            conn_info = db_info['connection_info']
            st.write(f"**База данных:** {conn_info.get('database', 'N/A')}")
            st.write(f"**Пользователь:** {conn_info.get('user', 'N/A')}")
            st.write(f"**Хост:** {conn_info.get('host', 'N/A')}")
            st.write(f"**Порт:** {conn_info.get('port', 'N/A')}")
        else:
            st.info("Информация о подключении недоступна")


def _show_mock_db_overview():
    """Отображает mock данные для обзора БД."""
    st.markdown("### 📊 Сводка (Mock данные)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="📋 Таблицы", value=15)
    
    with col2:
        st.metric(label="🔍 Индексы", value=23)
    
    with col3:
        st.metric(label="🔗 Связи", value=8)
    
    with col4:
        st.metric(label="💾 Размер БД", value="2.5 GB")
    
    st.markdown("### 🏗️ Структура базы данных (Mock)")
    
    # Mock таблицы
    mock_tables = pd.DataFrame({
        'schemaname': ['public', 'public', 'public', 'public', 'public'],
        'tablename': ['users', 'orders', 'products', 'categories', 'payments'],
        'tableowner': ['postgres', 'postgres', 'postgres', 'postgres', 'postgres'],
        'size': ['1.2 GB', '800 MB', '400 MB', '100 MB', '50 MB'],
        'size_bytes': [1200000000, 800000000, 400000000, 100000000, 50000000]
    })
    
    st.dataframe(mock_tables, width='stretch', hide_index=True)
    
    # Mock график
    fig = px.bar(
        mock_tables,
        x='tablename',
        y='size_bytes',
        title="Топ-5 таблиц по размеру (Mock)",
        labels={'size_bytes': 'Размер (байты)', 'tablename': 'Таблица'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width='stretch')
    
    st.markdown("### 🔗 ER-диаграмма (Mock)")
    
    # Mock связи
    mock_relationships = pd.DataFrame({
        'table_schema': ['public', 'public', 'public', 'public'],
        'table_name': ['orders', 'orders', 'products', 'payments'],
        'column_name': ['user_id', 'product_id', 'category_id', 'order_id'],
        'foreign_table_schema': ['public', 'public', 'public', 'public'],
        'foreign_table_name': ['users', 'products', 'categories', 'orders'],
        'foreign_column_name': ['id', 'id', 'id', 'id']
    })
    
    st.markdown("#### Связи между таблицами:")
    st.write("**public.users** → public.orders")
    st.write("**public.products** → public.orders")
    st.write("**public.categories** → public.products")
    st.write("**public.orders** → public.payments")
    
    # Mock визуальная диаграмма
    import plotly.graph_objects as go
    import numpy as np
    
    tables = ['users', 'orders', 'products', 'categories', 'payments']
    n_tables = len(tables)
    angles = np.linspace(0, 2*np.pi, n_tables, endpoint=False)
    x_pos = np.cos(angles)
    y_pos = np.sin(angles)
    
    fig = go.Figure()
    
    # Узлы
    fig.add_trace(go.Scatter(
        x=x_pos,
        y=y_pos,
        mode='markers+text',
        marker=dict(size=20, color='lightblue'),
        text=tables,
        textposition="middle center",
        name="Таблицы"
    ))
    
    # Связи
    connections = [
        (0, 1),  # users -> orders
        (2, 1),  # products -> orders
        (3, 2),  # categories -> products
        (1, 4)   # orders -> payments
    ]
    
    for start, end in connections:
        fig.add_trace(go.Scatter(
            x=[x_pos[start], x_pos[end]],
            y=[y_pos[start], y_pos[end]],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False
        ))
    
    fig.update_layout(
        title="ER-диаграмма базы данных (Mock)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, width='stretch')
    
    st.markdown("### 🔌 Информация о подключении (Mock)")
    st.code("PostgreSQL 15.4 on x86_64-pc-linux-gnu, compiled by gcc")
