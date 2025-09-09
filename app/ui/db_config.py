"""Модуль для вкладки 'Конфигурация БД' с LLM."""

import streamlit as st
import json
import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)


def show_db_config_tab(dsn: str, mock_mode: bool = False):
    """Отображает вкладку 'Конфигурация БД'."""
    st.markdown("## ⚙️ Конфигурация базы данных")

    if mock_mode:
        st.info("🎭 Mock режим: отображаются тестовые данные")
        _show_mock_db_config()
        return

    try:
        # Получаем настройки PostgreSQL
        pg_settings = _get_pg_settings(dsn)

        # Отображаем настройки
        _show_pg_settings(pg_settings)

        # Анализируем критические параметры
        _show_critical_parameters(pg_settings)

        # LLM анализ и рекомендации
        _show_llm_analysis(pg_settings)

        # Экспорт отчета
        _show_export_options(pg_settings)

    except Exception as e:
        st.error(f"❌ Ошибка получения конфигурации БД: {str(e)}")
        logger.error(f"Ошибка в show_db_config_tab: {e}")


def _get_pg_settings(dsn: str) -> List[Dict[str, Any]]:
    """Получает настройки PostgreSQL."""
    import psycopg2

    settings = []

    try:
        # Подключаемся напрямую (без RealDictCursor для избежания проблем)
        conn = psycopg2.connect(dsn)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Получаем все настройки
            cur.execute("""
                    SELECT 
                        name,
                        setting,
                        unit,
                        category,
                        short_desc,
                        context,
                        vartype,
                        min_val,
                        max_val,
                        enumvals,
                        boot_val,
                        reset_val,
                        source,
                        sourcefile,
                        sourceline
                    FROM pg_settings
                    ORDER BY category, name
                """)

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            # Преобразуем в список словарей
            for row in rows:
                settings.append(dict(zip(columns, row)))

        conn.close()

    except Exception as e:
        logger.error(f"Ошибка получения настроек PostgreSQL: {e}")
        raise

    return settings


def _show_pg_settings(settings: List[Dict[str, Any]]):
    """Отображает настройки PostgreSQL."""
    st.markdown("### 🔧 Настройки PostgreSQL")

    if not settings:
        st.warning("⚠️ Настройки не найдены")
        return

    # Создаем DataFrame
    settings_df = pd.DataFrame(settings)

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        categories = ['Все'] + sorted(settings_df['category'].unique().tolist())
        selected_category = st.selectbox("Категория", categories)

    with col2:
        search_term = st.text_input("Поиск по названию", placeholder="work_mem, shared_buffers...")

    # Фильтруем данные
    filtered_df = settings_df.copy()

    if selected_category != 'Все':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    if search_term:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]

    # Отображаем таблицу
    st.dataframe(
        filtered_df[['name', 'setting', 'unit', 'category', 'short_desc']],
        width='stretch',
        hide_index=True,
        column_config={
            'name': 'Параметр',
            'setting': 'Значение',
            'unit': 'Единица',
            'category': 'Категория',
            'short_desc': 'Описание'
        }
    )

    st.info(f"📊 Показано {len(filtered_df)} из {len(settings_df)} параметров")


def _show_critical_parameters(settings: List[Dict[str, Any]]):
    """Отображает критические параметры."""
    st.markdown("### ⚠️ Критические параметры")

    # Определяем критические параметры
    critical_params = [
        'work_mem', 'shared_buffers', 'effective_cache_size',
        'maintenance_work_mem', 'checkpoint_completion_target',
        'wal_buffers', 'max_connections', 'autovacuum',
        'random_page_cost', 'seq_page_cost', 'cpu_tuple_cost',
        'cpu_index_tuple_cost', 'cpu_operator_cost'
    ]

    critical_settings = [s for s in settings if s['name'] in critical_params]

    if not critical_settings:
        st.warning("⚠️ Критические параметры не найдены")
        return

    # Создаем DataFrame для критических параметров
    critical_df = pd.DataFrame(critical_settings)

    # Отображаем с цветовой индикацией
    for _, setting in critical_df.iterrows():
        col1, col2, col3 = st.columns([2, 1, 3])

        with col1:
            st.write(f"**{setting['name']}**")

        with col2:
            # Простая логика для определения статуса
            status = _get_parameter_status(setting)
            if status == 'good':
                st.success(f"✅ {setting['setting']} {setting.get('unit', '')}")
            elif status == 'warning':
                st.warning(f"⚠️ {setting['setting']} {setting.get('unit', '')}")
            else:
                st.error(f"❌ {setting['setting']} {setting.get('unit', '')}")

        with col3:
            st.caption(setting.get('short_desc', 'Нет описания'))


def _get_parameter_status(setting: Dict[str, Any]) -> str:
    """Определяет статус параметра (good/warning/error)."""
    name = setting['name']
    value = setting['setting']

    # Простая логика для определения статуса
    if name == 'work_mem':
        try:
            val = int(value)
            if val < 4:
                return 'warning'
            elif val > 256:
                return 'warning'
            else:
                return 'good'
        except Exception as e:
            logger.error(f"Ошибка обработки параметра {setting['name']}: {e}")
            return 'error'

    elif name == 'shared_buffers':
        try:
            val = int(value)
            if val < 128:
                return 'warning'
            elif val > 2048:
                return 'warning'
            else:
                return 'good'
        except Exception as e:
            logger.error(f"Ошибка обработки параметра {setting['name']}: {e}")
            return 'error'

    elif name == 'max_connections':
        try:
            val = int(value)
            if val > 200:
                return 'warning'
            else:
                return 'good'
        except Exception as e:
            logger.error(f"Ошибка обработки параметра {setting['name']}: {e}")
            return 'error'

    return 'good'


def _show_llm_analysis(settings: List[Dict[str, Any]]):
    """Отображает LLM анализ конфигурации в автоматическом режиме."""
    st.markdown("### 🤖 AI анализ конфигурации")

    # Проверяем, включен ли AI
    if not st.session_state.get('enable_ai', False):
        st.info("ℹ️ AI анализ отключен. Включите AI в настройках для получения рекомендаций.")
        return

    # Автоматический анализ при загрузке страницы
    if 'db_config_analyzed' not in st.session_state:
        with st.spinner("🤖 AI анализирует конфигурацию..."):
            try:
                # Подготавливаем данные для LLM
                critical_settings = _prepare_settings_for_llm(settings)

                # Получаем рекомендации от LLM
                recommendations = _get_llm_recommendations(critical_settings)

                # Сохраняем результат в session_state
                st.session_state['db_config_analysis'] = recommendations
                st.session_state['db_config_analyzed'] = True

            except Exception:
                st.error("❌ Ошибка AI анализа")
                logger.error("Ошибка LLM анализа")
                st.session_state['db_config_analyzed'] = True

    # Отображаем сохраненные рекомендации
    if 'db_config_analysis' in st.session_state:
        _display_llm_recommendations(st.session_state['db_config_analysis'])
    
    # Кнопка для повторного анализа
    if st.button("🔄 Обновить анализ", help="Повторить AI анализ конфигурации"):
        st.session_state['db_config_analyzed'] = False
        st.rerun()


def _prepare_settings_for_llm(settings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Подготавливает настройки для LLM анализа."""
    critical_params = [
        'work_mem', 'shared_buffers', 'effective_cache_size',
        'maintenance_work_mem', 'max_connections', 'autovacuum'
    ]

    critical_settings = {}
    for setting in settings:
        if setting['name'] in critical_params:
            # Очищаем данные от лишних пробелов и None значений
            value = str(setting['setting']).strip() if setting['setting'] is not None else ''
            unit = str(setting.get('unit', '')).strip() if setting.get('unit') is not None else None
            description = str(setting.get('short_desc', '')).strip() if setting.get('short_desc') is not None else ''

            critical_settings[setting['name']] = {
                'value': value,
                'unit': unit,
                'description': description
            }

    return critical_settings


def _get_llm_recommendations(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Получает рекомендации от LLM."""
    try:
        import asyncio
        from app.llm_integration import LLMIntegration

        # Проверяем наличие API ключа
        api_key = st.session_state.get('openai_api_key', '')
        if not api_key:
            return {
                'recommendations': """❌ **OpenAI API ключ не настроен**

💡 **Как настроить API ключ:**
1. Откройте sidebar (левая панель)
2. Найдите раздел "🤖 AI настройки"
3. Введите ваш OpenAI API ключ в поле "OpenAI API ключ"
4. Нажмите кнопку "🔍 Анализировать конфигурацию" снова

🔗 **Где получить API ключ:**
- Перейдите на https://platform.openai.com/api-keys
- Создайте новый API ключ
- Скопируйте ключ и вставьте в настройки

⚙️ **Текущие настройки:**
- Модель: {st.session_state.get('openai_model', 'gpt-4o-mini')}""",
                'settings_analyzed': settings
            }

        # Создаем максимально простой промпт для LLM
        prompt = f"""
        Проанализируй конфигурацию PostgreSQL и дай рекомендации по оптимизации.

        Конфигурация:
        {json.dumps(settings, indent=2, ensure_ascii=False)}

        Начни сразу с рекомендаций в формате:

        ### Название рекомендации.
        Приоритет: высокий/средний/низкий
        Категория: configuration_optimization/maintenance_optimization/query_optimization
        Объяснение: Подробное объяснение проблемы и решения
        Ожидаемое улучшение: Описание ожидаемых улучшений
        Уверенность: 0.0-1.0

        ---

        Дай 3-5 рекомендаций.
        """

        # Инициализируем LLM
        llm_config = {
            'openai_api_key': api_key,
            'openai_model': st.session_state.get('openai_model', 'gpt-4o-mini'),
            'openai_temperature': st.session_state.get('openai_temperature', 0.7),
            'enable_proxy': st.session_state.get('enable_proxy', True),
            'proxy_host': st.session_state.get('proxy_host', 'localhost'),
            'proxy_port': st.session_state.get('proxy_port', 1080)
        }

        # Логируем настройки (без API ключа)
        logger.info(f"LLM конфигурация: модель={llm_config['openai_model']}, "
                    f"прокси={llm_config['enable_proxy']}, "
                    f"хост={llm_config['proxy_host']}:{llm_config['proxy_port']}")

        llm = LLMIntegration(llm_config)

        # Создаем фиктивный execution_plan для анализа конфигурации
        mock_execution_plan = {
            'type': 'configuration_analysis',
            'settings': settings,
            'prompt': prompt
        }

        # Получаем ответ от LLM через правильный метод
        async def get_async_recommendations():
            return await llm.get_recommendations(
                sql_query=prompt,
                execution_plan=mock_execution_plan,
                db_schema=settings
            )

        # Запускаем асинхронную функцию
        recommendations = asyncio.run(get_async_recommendations())

        # Форматируем ответ
        if recommendations:
            formatted_recommendations = "## 🤖 AI Рекомендации по конфигурации PostgreSQL\n\n"
            for rec in recommendations:
                formatted_recommendations += f"### {rec.description}\n"
                formatted_recommendations += f"**Приоритет:** {rec.priority}\n"
                formatted_recommendations += f"**Категория:** {rec.category}\n"
                formatted_recommendations += f"**Объяснение:** {rec.reasoning}\n"
                if rec.expected_improvement:
                    formatted_recommendations += f"**Ожидаемое улучшение:** {rec.expected_improvement}\n"
                formatted_recommendations += f"**Уверенность:** {rec.confidence:.2f}\n\n"
        else:
            formatted_recommendations = "❌ Не удалось получить рекомендации от AI. Проверьте настройки API ключей и прокси."

        return {
            'recommendations': formatted_recommendations,
            'settings_analyzed': settings
        }

    except Exception as e:
        logger.error(f"Ошибка получения LLM рекомендаций: {e}")
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
            error_msg += "\n🔧 **Решение:** Проверьте интернет-соединение и прокси"
        else:
            error_msg += "\n\n💡 **Проблема:** Неизвестная ошибка"
            error_msg += "\n🔧 **Решение:** Проверьте настройки API ключа и прокси"

        return {
            'recommendations': error_msg,
            'settings_analyzed': settings
        }


def _display_llm_recommendations(recommendations: Dict[str, Any]):
    """Отображает рекомендации LLM."""
    # Получаем рекомендации
    recommendations_text = recommendations['recommendations']

    # Проверяем, есть ли уже заголовок в тексте
    has_header = (
        recommendations_text.startswith("## ")
        or "## 🤖 AI Рекомендации" in recommendations_text
        or "🤖 Рекомендации AI" in recommendations_text
        or recommendations_text.startswith("### ")
    )

    if not has_header:
        st.markdown("#### 🎯 Рекомендации по оптимизации")

    # Проверяем, содержит ли текст JSON блоки
    import re
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', recommendations_text, re.DOTALL)

    if json_match:
        # Если есть JSON блок, извлекаем и форматируем его
        try:
            import json
            json_str = json_match.group(1)
            data = json.loads(json_str)

            # Отображаем структурированные рекомендации
            for i, rec in enumerate(data.get("recommendations", []), 1):
                priority_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(rec.get("priority", "medium"), "🟡")

                category_emoji = {
                    "configuration_optimization": "⚙️",
                    "maintenance_optimization": "🔧",
                    "query_optimization": "🔍",
                    "connection_management": "🔗",
                    "general": "📋"
                }.get(rec.get("category", "general"), "📋")

                st.markdown(f"### {priority_emoji} {rec.get('description', 'Рекомендация')}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Приоритет:** {rec.get('priority', 'medium')}")
                    st.markdown(f"**Категория:** {category_emoji} {rec.get('category', 'general')}")
                with col2:
                    st.markdown(f"**Уверенность:** {rec.get('confidence', 0.0):.2f}")

                if rec.get('current_query') and rec.get('current_query') != 'N/A':
                    st.markdown(f"**Текущее значение:** `{rec.get('current_query')}`")

                if rec.get('optimized_query'):
                    st.markdown(f"**Рекомендуемое значение:** `{rec.get('optimized_query')}`")

                if rec.get('expected_improvement'):
                    st.markdown(f"**Ожидаемое улучшение:** {rec.get('expected_improvement')}")

                if rec.get('reasoning'):
                    st.markdown(f"**Объяснение:** {rec.get('reasoning')}")

                st.markdown("---")

        except Exception:
            # Если не удалось парсить JSON, показываем как есть
            st.markdown(recommendations_text)
    else:
        # Если не Markdown и не JSON, парсим структурированный текст
        _parse_structured_text(recommendations_text)

    # Показываем проанализированные настройки
    with st.expander("📋 Проанализированные настройки"):
        settings = recommendations['settings_analyzed']

        # Отображаем в виде таблицы для лучшей читаемости
        if settings:
            st.markdown("**Критические параметры PostgreSQL:**")

            for param_name, param_data in settings.items():
                st.markdown(f"**{param_name}:**")
                st.markdown(f"- Значение: `{param_data['value']}` {param_data['unit'] or ''}")
                st.markdown(f"- Описание: {param_data['description']}")
                st.markdown("---")
        else:
            st.info("Настройки не найдены")


def _parse_structured_text(text: str):
    """Парсит структурированный текст и отображает как Markdown."""
    # Убираем лишние заголовки и дублирования
    text = text.replace("🤖 AI анализ схемы", "").strip()
    text = text.replace("🎯 Рекомендации по оптимизации", "").strip()
    text = text.replace("🤖 Рекомендации AI по настройке PostgreSQL", "").strip()
    text = text.replace("## 🤖 Рекомендации AI по настройке PostgreSQL", "").strip()
    text = text.replace("## 🤖 AI Рекомендации по конфигурации PostgreSQL", "").strip()

    # Убираем дублированные заголовки в тексте
    import re
    text = re.sub(r'## 🤖 Рекомендации AI по настройке PostgreSQL\s*', '', text)
    text = re.sub(r'## 🤖 AI Рекомендации по конфигурации PostgreSQL\s*', '', text)
    text = re.sub(r'🤖 Рекомендации AI по настройке PostgreSQL\s*', '', text)
    text = re.sub(r'### AI рекомендации по конфигурации PostgreSQL\s*', '', text)

    # Разделяем на рекомендации по разделителям "---"
    recommendations = []

    # Сначала пробуем разделить по "---"
    parts = text.split('---')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Убираем лишние символы и эмодзи
        part = re.sub(r'^🟡\s*', '', part)
        part = re.sub(r'^🔴\s*', '', part)
        part = re.sub(r'^🟢\s*', '', part)

        # Пропускаем части, которые содержат только заголовки или мусор
        if (part.strip()
            and not part.startswith('##')
            and not part.startswith('Рекомендации AI')
            and 'Приоритет:' in part  # Должна содержать поле Приоритет
                and len(part.strip()) > 50):  # Минимальная длина для валидной рекомендации
            recommendations.append(part.strip())

    # Если не нашли разделители, пробуем по "Уверенность:"
    if not recommendations:
        current_rec = ""
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Если строка содержит "Уверенность:" - это конец рекомендации
            if "Уверенность:" in line:
                current_rec += line + "\n"
                if current_rec.strip():
                    recommendations.append(current_rec.strip())
                current_rec = ""
            else:
                current_rec += line + "\n"

        # Добавляем последнюю рекомендацию
        if current_rec.strip():
            recommendations.append(current_rec.strip())

    # Отображаем каждую рекомендацию
    for rec_text in recommendations:
        if rec_text.strip():
            _display_single_recommendation_clean(rec_text)


def _display_single_recommendation_clean(text: str):
    """Отображает одну рекомендацию в чистом формате."""
    if not text.strip():
        return

    # Очищаем текст от дублирований и лишних символов
    import re

    # Убираем дублированные поля
    text = re.sub(r'Приоритет:\s*\*\*\s*([^*]+)\s*\*\*', r'Приоритет: \1', text)
    text = re.sub(r'Категория:\s*[📋⚙️]\s*\*\*\s*([^*]+)\s*\*\*', r'Категория: \1', text)
    text = re.sub(r'Объяснение:\s*\*\*\s*([^*]+)\s*\*\*', r'Объяснение: \1', text)
    text = re.sub(r'Ожидаемое улучшение:\s*\*\*\s*([^*]+)\s*\*\*', r'Ожидаемое улучшение: \1', text)

    # Убираем лишние звездочки
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    # Извлекаем заголовок (первое предложение до точки)
    title_match = re.match(r'^([^.]*\.)', text)
    title = title_match.group(1).strip() if title_match else text.split('.')[0].strip()

    # Очищаем заголовок от лишних символов
    title = re.sub(r'^[🟡🔴🟢]\s*', '', title)
    title = title.strip()

    # Определяем приоритет по заголовку
    priority_emoji = "🟡"
    if any(word in title.lower() for word in ['увеличить', 'increase', 'критично', 'critical', 'оптимизация', 'optimization']):
        priority_emoji = "🔴"
    elif any(word in title.lower() for word in ['проверить', 'check', 'рассмотреть', 'consider', 'настройка']):
        priority_emoji = "🟢"

    st.markdown(f"### {priority_emoji} {title}")

    # Извлекаем информацию из текста
    priority_match = re.search(r'Приоритет:\s*([^К\n]+?)(?=\s*Категория:|$)', text)
    category_match = re.search(r'Категория:\s*([^О\n]+?)(?=\s*Объяснение:|$)', text)
    explanation_match = re.search(r'Объяснение:\s*([^О\n]+?)(?=\s*Ожидаемое улучшение:|$)', text)
    improvement_match = re.search(r'Ожидаемое улучшение:\s*([^У\n]+?)(?=\s*Уверенность:|$)', text)
    confidence_match = re.search(r'Уверенность:\s*([0-9.,]+)', text)

    # Отображаем информацию в колонках
    col1, col2 = st.columns(2)

    with col1:
        if priority_match:
            priority = priority_match.group(1).strip()
            st.markdown(f"**Приоритет:** {priority}")

        if category_match:
            category = category_match.group(1).strip()
            category_emoji = "⚙️" if "configuration" in category.lower() or "конфигурация" in category.lower() else "📋"
            st.markdown(f"**Категория:** {category_emoji} {category}")

    with col2:
        if confidence_match:
            confidence = confidence_match.group(1).strip()
            st.markdown(f"**Уверенность:** {confidence}")

    # Отображаем объяснение и ожидаемое улучшение
    if explanation_match:
        explanation = explanation_match.group(1).strip()
        st.markdown(f"**Объяснение:** {explanation}")

    if improvement_match:
        improvement = improvement_match.group(1).strip()
        st.markdown(f"**Ожидаемое улучшение:** {improvement}")

    st.markdown("---")


def _display_single_recommendation_simple(text: str):
    """Отображает одну рекомендацию в простом формате."""
    if not text.strip():
        return

    # Извлекаем заголовок (первое предложение до точки)
    import re
    title_match = re.match(r'^([^.]*\.)', text)
    title = title_match.group(1).strip() if title_match else text.split('.')[0].strip()

    # Определяем приоритет по заголовку
    priority_emoji = "🟡"
    if any(word in title.lower() for word in ['увеличить', 'increase', 'критично', 'critical']):
        priority_emoji = "🔴"
    elif any(word in title.lower() for word in ['проверить', 'check', 'рассмотреть', 'consider']):
        priority_emoji = "🟢"

    st.markdown(f"### {priority_emoji} {title}")

    # Извлекаем информацию из текста
    priority_match = re.search(r'Приоритет:\s*([^К]+?)(?=\s*Категория:|$)', text)
    category_match = re.search(r'Категория:\s*([^О]+?)(?=\s*Объяснение:|$)', text)
    explanation_match = re.search(r'Объяснение:\s*([^О]+?)(?=\s*Ожидаемое улучшение:|$)', text)
    improvement_match = re.search(r'Ожидаемое улучшение:\s*([^У]+?)(?=\s*Уверенность:|$)', text)
    confidence_match = re.search(r'Уверенность:\s*([0-9.,]+)', text)

    # Отображаем информацию в колонках
    col1, col2 = st.columns(2)

    with col1:
        if priority_match:
            priority = priority_match.group(1).strip()
            st.markdown(f"**Приоритет:** {priority}")

        if category_match:
            category = category_match.group(1).strip()
            category_emoji = "⚙️" if "configuration" in category.lower() else "📋"
            st.markdown(f"**Категория:** {category_emoji} {category}")

    with col2:
        if confidence_match:
            confidence = confidence_match.group(1).strip()
            st.markdown(f"**Уверенность:** {confidence}")

    # Отображаем объяснение и ожидаемое улучшение
    if explanation_match:
        explanation = explanation_match.group(1).strip()
        st.markdown(f"**Объяснение:** {explanation}")

    if improvement_match:
        improvement = improvement_match.group(1).strip()
        st.markdown(f"**Ожидаемое улучшение:** {improvement}")

    st.markdown("---")


def _show_export_options(settings: List[Dict[str, Any]]):
    """Отображает опции экспорта отчета."""
    st.markdown("### 📤 Экспорт отчета")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Экспорт в Markdown"):
            _export_to_markdown(settings)

    with col2:
        if st.button("📊 Экспорт в JSON"):
            _export_to_json(settings)

    with col3:
        if st.button("📋 Экспорт в CSV"):
            _export_to_csv(settings)


def _export_to_markdown(settings: List[Dict[str, Any]]):
    """Экспортирует отчет в Markdown."""
    try:
        import pandas as pd

        settings_df = pd.DataFrame(settings)

        # Создаем Markdown отчет
        markdown_content = f"""# Отчет по конфигурации PostgreSQL

## Сводка
- Всего параметров: {len(settings)}
- Категории: {', '.join(settings_df['category'].unique())}

## Критические параметры

"""

        # Добавляем критические параметры
        critical_params = ['work_mem', 'shared_buffers', 'effective_cache_size']
        for param in critical_params:
            param_data = settings_df[settings_df['name'] == param]
            if not param_data.empty:
                setting = param_data.iloc[0]
                markdown_content += f"### {param}\n"
                markdown_content += f"- **Значение:** {setting['setting']} {setting.get('unit', '')}\n"
                markdown_content += f"- **Описание:** {setting.get('short_desc', 'Нет описания')}\n\n"

        # Предоставляем для скачивания
        st.download_button(
            label="💾 Скачать Markdown",
            data=markdown_content,
            file_name="postgresql_config_report.md",
            mime="text/markdown"
        )

    except Exception as e:
        st.error(f"❌ Ошибка экспорта в Markdown: {str(e)}")


def _export_to_json(settings: List[Dict[str, Any]]):
    """Экспортирует отчет в JSON."""
    try:
        json_content = json.dumps(settings, indent=2, ensure_ascii=False, default=str)

        st.download_button(
            label="💾 Скачать JSON",
            data=json_content,
            file_name="postgresql_config_report.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"❌ Ошибка экспорта в JSON: {str(e)}")


def _export_to_csv(settings: List[Dict[str, Any]]):
    """Экспортирует отчет в CSV."""
    try:
        import pandas as pd

        settings_df = pd.DataFrame(settings)
        csv_content = settings_df.to_csv(index=False)

        st.download_button(
            label="💾 Скачать CSV",
            data=csv_content,
            file_name="postgresql_config_report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Ошибка экспорта в CSV: {str(e)}")


def _show_mock_db_config():
    """Отображает mock данные для конфигурации БД."""
    st.markdown("### 🔧 Настройки PostgreSQL (Mock данные)")

    # Mock настройки
    mock_settings = [
        {'name': 'work_mem', 'setting': '4', 'unit': 'MB', 'category': 'Resource Usage',
            'short_desc': 'Sets the base maximum amount of memory to be used by a query operation'},
        {'name': 'shared_buffers', 'setting': '128', 'unit': 'MB', 'category': 'Resource Usage',
            'short_desc': 'Sets the amount of memory the database server uses for shared memory buffers'},
        {'name': 'effective_cache_size', 'setting': '4', 'unit': 'GB', 'category': 'Query Tuning',
            'short_desc': 'Sets the planner\'s assumption about the effective size of the disk cache'},
        {'name': 'max_connections', 'setting': '100', 'unit': '', 'category': 'Connections and Authentication',
            'short_desc': 'Sets the maximum number of concurrent connections'}
    ]

    settings_df = pd.DataFrame(mock_settings)
    st.dataframe(settings_df, width='stretch', hide_index=True)

    st.markdown("### ⚠️ Критические параметры (Mock)")

    for setting in mock_settings:
        col1, col2, col3 = st.columns([2, 1, 3])

        with col1:
            st.write(f"**{setting['name']}**")

        with col2:
            st.success(f"✅ {setting['setting']} {setting['unit']}")

        with col3:
            st.caption(setting['short_desc'])

    st.markdown("### 🤖 AI анализ конфигурации (Mock)")
    st.info("ℹ️ AI анализ недоступен в mock режиме")

    st.markdown("### 📤 Экспорт отчета (Mock)")
    st.info("ℹ️ Экспорт недоступен в mock режиме")
