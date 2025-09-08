"""Модуль для вкладки примеров."""

import streamlit as st

from app.analyzer import SQLAnalyzer


def show_examples_tab(
        dsn,
        mock_mode,
        work_mem,
        shared_buffers,
        effective_cache_size,
        custom_config):
    """Показывает вкладку с примерами с улучшенным дизайном."""
    st.markdown("## 📋 Примеры запросов")

    try:
        analyzer = SQLAnalyzer(dsn)
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
                if st.button(
                        f"🔍 Анализировать пример {
                            i + 1}",
                        key=f"analyze_{i}"):
                    try:
                        with st.spinner("🔍 Анализирую пример..."):
                            # Анализируем пример
                            result = analyzer.analyze_sql(
                                example['sql'], custom_config)

                            # Показываем краткие результаты
                            st.success("✅ Анализ примера завершен!")

                            if result.metrics:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(
                                        "⏱️ Время", f"{
                                            result.metrics.estimated_time_ms:.2f} мс")
                                with col2:
                                    st.metric(
                                        "💾 I/O", f"{result.metrics.estimated_io_mb:.2f} MB")
                                with col3:
                                    st.metric(
                                        "🧠 Память", f"{
                                            result.metrics.estimated_memory_mb:.2f} MB")

                            if result.recommendations:
                                st.markdown(
                                    f"**💡 Рекомендации:** {len(result.recommendations)} найдено")
                                # Показываем первые 3
                                for rec in result.recommendations[:3]:
                                    st.write(
                                        f"• {
                                            rec.title} ({
                                            rec.priority.value})")

                    except Exception as e:
                        st.error(f"❌ Ошибка анализа примера: {e}")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки примеров: {e}")
