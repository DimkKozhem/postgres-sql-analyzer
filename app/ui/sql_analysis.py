"""Модуль для вкладки анализа SQL."""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from app.analyzer import SQLAnalyzer


def show_sql_analysis_tab(
        dsn,
        mock_mode,
        work_mem,
        shared_buffers,
        effective_cache_size,
        custom_config):
    """Показывает вкладку анализа SQL с улучшенным дизайном."""

    # Проверка подключения
    if not dsn:
        st.warning(
            "⚠️ Для анализа SQL необходимо подключиться к базе данных. Перейдите в боковую панель и настройте подключение.")
        return

    # Ввод SQL с улучшенным дизайном
    st.markdown("## 🔍 Анализ SQL-запроса")

    col1, col2 = st.columns([3, 1])

    with col1:
        sql_input = st.text_area(
            "Введите SQL-запрос для анализа:",
            height=200,
            placeholder="SELECT u.name, o.total_amount \nFROM users u \nJOIN orders o ON u.id = o.user_id \nWHERE o.total_amount > 1000;",
            help="Поддерживаются SELECT, WITH, JOIN, агрегатные функции и подзапросы")

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
            width='stretch',
            disabled=not sql_input.strip() or not dsn
        )

    # Индикатор загрузки
    if analyze_button and sql_input.strip():
        with st.spinner("🔍 Выполняется анализ SQL-запроса..."):
            time.sleep(0.5)  # Имитация загрузки

    # Анализ SQL
    if analyze_button and sql_input.strip():
        try:
            # Создаем анализатор с конфигурацией
            analyzer = SQLAnalyzer(dsn, custom_config)

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
        high_recs = [
            r for r in result.recommendations if r.priority.value == "high"]
        medium_recs = [
            r for r in result.recommendations if r.priority.value == "medium"]
        low_recs = [
            r for r in result.recommendations if r.priority.value == "low"]

        # Высокий приоритет
        if high_recs:
            st.markdown("### 🚨 Высокий приоритет")
            for rec in high_recs:
                with st.expander(f"🔴 {rec.title}", expanded=True):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(
                        f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if hasattr(rec, 'sql_example') and rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if hasattr(
                            rec,
                            'configuration_example') and rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")

        # Средний приоритет
        if medium_recs:
            st.markdown("### ⚠️ Средний приоритет")
            for rec in medium_recs:
                with st.expander(f"🟡 {rec.title}"):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(
                        f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if hasattr(rec, 'sql_example') and rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if hasattr(
                            rec,
                            'configuration_example') and rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")

        # Низкий приоритет
        if low_recs:
            st.markdown("### ℹ️ Низкий приоритет")
            for rec in low_recs:
                with st.expander(f"🟢 {rec.title}"):
                    st.markdown(f"**Описание:** {rec.description}")
                    st.markdown(
                        f"**Потенциальное улучшение:** {rec.potential_improvement}")
                    if hasattr(rec, 'sql_example') and rec.sql_example:
                        st.markdown("**Пример SQL:**")
                        st.code(rec.sql_example, language="sql")
                    if hasattr(
                            rec,
                            'configuration_example') and rec.configuration_example:
                        st.markdown("**Пример конфигурации:**")
                        st.code(rec.configuration_example, language="sql")

    # Экспорт результатов
    st.markdown("## 📤 Экспорт результатов")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # JSON экспорт
        json_report = analyzer.export_analysis_report(result, "json")
        st.download_button(
            label="📄 Скачать JSON",
            data=json_report,
            file_name=f"sql_analysis_{
                datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width='stretch')

    with col2:
        # Текстовый экспорт
        text_report = analyzer.export_analysis_report(result, "text")
        st.download_button(
            label="📝 Скачать текст",
            data=text_report,
            file_name=f"sql_analysis_{
                datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            width='stretch')

    with col3:
        # Raw EXPLAIN JSON
        if result.explain_json:
            st.download_button(
                label="🔍 Скачать EXPLAIN",
                data=json.dumps(
                    result.explain_json,
                    indent=2),
                file_name=f"explain_{
                    datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width='stretch')

    with col4:
        # PDF экспорт (если доступен)
        st.download_button(
            label="📊 Скачать PDF",
            data="PDF content would go here",
            file_name=f"sql_analysis_{
                datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            width='stretch',
            disabled=True,
            help="PDF экспорт в разработке")

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
                labels={
                    'level': 'Уровень',
                    'cost': 'Стоимость',
                    'type': 'Тип узла'},
                color_discrete_sequence=px.colors.qualitative.Set3)

            fig.update_layout(
                height=400,
                showlegend=True,
                xaxis_title="Уровень плана",
                yaxis_title="Стоимость (cost)"
            )

            st.plotly_chart(fig, width='stretch')

            # Дополнительная информация о плане
            st.markdown("### 📊 Детали плана")
            st.dataframe(
                df[['level', 'type', 'cost', 'rows', 'width']].sort_values('level'),
                width='stretch'
            )

    except Exception as e:
        st.warning(f"⚠️ Не удалось создать визуализацию: {e}")
