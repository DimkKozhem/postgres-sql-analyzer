"""Модуль для вкладки планов выполнения."""

import streamlit as st
import json

from app.analyzer import SQLAnalyzer
from app.ui.sql_analysis import create_plan_visualization


def show_execution_plans_tab(dsn, mock_mode):
    """Показывает вкладку с анализом планов выполнения."""
    st.markdown("## 🔍 Анализ планов выполнения")

    if not dsn:
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
        help="Скопируйте результат команды EXPLAIN (FORMAT JSON)")

    if st.button("🔍 Анализировать план", width='stretch'):
        if plan_json.strip():
            try:
                plan_data = json.loads(plan_json)
                st.success("✅ План загружен!")

                # Анализируем план
                analyzer = SQLAnalyzer(dsn)
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
