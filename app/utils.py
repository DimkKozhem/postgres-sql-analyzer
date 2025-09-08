"""Общие утилиты для PostgreSQL SQL Analyzer."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UIComponents:
    """Класс для общих UI компонентов."""

    @staticmethod
    def show_metric_card(title: str, value: Union[str, int, float],
                         delta: Optional[str] = None,
                         help_text: Optional[str] = None) -> None:
        """Отображает карточку с метрикой."""
        st.metric(
            label=title,
            value=value,
            delta=delta,
            help=help_text
        )

    @staticmethod
    def show_info_box(message: str, icon: str = "ℹ️") -> None:
        """Отображает информационное сообщение."""
        st.info(f"{icon} {message}")

    @staticmethod
    def show_warning_box(message: str, icon: str = "⚠️") -> None:
        """Отображает предупреждение."""
        st.warning(f"{icon} {message}")

    @staticmethod
    def show_error_box(message: str, icon: str = "❌") -> None:
        """Отображает ошибку."""
        st.error(f"{icon} {message}")

    @staticmethod
    def show_success_box(message: str, icon: str = "✅") -> None:
        """Отображает успешное сообщение."""
        st.success(f"{icon} {message}")

    @staticmethod
    def create_columns(num_columns: int) -> List[Any]:
        """Создает колонки Streamlit."""
        return st.columns(num_columns)

    @staticmethod
    def show_expander(
            title: str,
            content: str,
            expanded: bool = False) -> None:
        """Отображает раскрывающийся блок."""
        with st.expander(title, expanded=expanded):
            st.write(content)


class DataVisualization:
    """Класс для визуализации данных."""

    @staticmethod
    def create_line_chart(
            data: pd.DataFrame,
            x: str,
            y: str,
            title: str,
            color: Optional[str] = None) -> go.Figure:
        """Создает линейный график."""
        fig = px.line(data, x=x, y=y, title=title, color=color)
        fig.update_layout(
            xaxis_title=x,
            yaxis_title=y,
            hovermode='x unified'
        )
        return fig

    @staticmethod
    def create_bar_chart(data: pd.DataFrame, x: str, y: str,
                         title: str, color: Optional[str] = None) -> go.Figure:
        """Создает столбчатый график."""
        fig = px.bar(data, x=x, y=y, title=title, color=color)
        fig.update_layout(
            xaxis_title=x,
            yaxis_title=y,
            hovermode='x unified'
        )
        return fig

    @staticmethod
    def create_pie_chart(data: pd.DataFrame, names: str, values: str,
                         title: str) -> go.Figure:
        """Создает круговую диаграмму."""
        fig = px.pie(data, names=names, values=values, title=title)
        return fig

    @staticmethod
    def create_heatmap(data: pd.DataFrame, title: str) -> go.Figure:
        """Создает тепловую карту."""
        fig = px.imshow(data, title=title, aspect="auto")
        return fig


class MockDataGenerator:
    """Класс для генерации mock данных."""

    @staticmethod
    def generate_query_metrics(count: int = 10) -> List[Dict[str, Any]]:
        """Генерирует mock метрики запросов."""
        import random

        metrics = []
        for i in range(count):
            metrics.append({
                'query_id': f"query_{i + 1}",
                'query_text': f"SELECT * FROM table_{i + 1} WHERE id = ?",
                'execution_time': random.uniform(10, 1000),
                'total_time': random.uniform(100, 10000),
                'rows': random.randint(1, 10000),
                'calls': random.randint(1, 1000),
                'mean_time': random.uniform(5, 500),
                'stddev_time': random.uniform(1, 100),
                'min_time': random.uniform(1, 50),
                'max_time': random.uniform(100, 2000)
            })
        return metrics

    @staticmethod
    def generate_database_info() -> Dict[str, Any]:
        """Генерирует mock информацию о базе данных."""
        return {
            'version': 'PostgreSQL 15.4',
            'tables': [
                {'name': 'users', 'rows': 10000, 'size': '50 MB'},
                {'name': 'orders', 'rows': 50000, 'size': '200 MB'},
                {'name': 'products', 'rows': 1000, 'size': '10 MB'}
            ],
            'indexes': [
                {'name': 'idx_users_email', 'table': 'users', 'size': '5 MB'},
                {'name': 'idx_orders_date', 'table': 'orders', 'size': '20 MB'}
            ],
            'relationships': [
                {'table': 'orders', 'foreign_table': 'users', 'column': 'user_id'},
                {'table': 'orders', 'foreign_table': 'products', 'column': 'product_id'}
            ],
            'connection_info': {
                'database': 'postgres',
                'user': 'readonly_user',
                'host': 'localhost',
                'port': 5433
            },
            'total_size': 260,
            'table_count': 3,
            'index_count': 2
        }

    @staticmethod
    def generate_execution_plan() -> Dict[str, Any]:
        """Генерирует mock план выполнения."""
        return {
            'query_plan': [
                {
                    'Node Type': 'Seq Scan',
                    'Relation Name': 'users',
                    'Cost': 100.0,
                    'Rows': 1000,
                    'Width': 50
                },
                {
                    'Node Type': 'Hash Join',
                    'Cost': 200.0,
                    'Rows': 500,
                    'Width': 100
                }
            ],
            'total_cost': 200.0,
            'total_rows': 500,
            'execution_time': 150.5,
            'warnings': ['Высокая стоимость сканирования']
        }

    @staticmethod
    def generate_recommendations() -> List[Dict[str, Any]]:
        """Генерирует mock рекомендации."""
        return [{'title': 'Добавить индекс',
                 'description': 'Рекомендуется добавить индекс на колонку email',
                 'priority': 'high',
                 'category': 'performance',
                 'impact': 'high',
                 'effort': 'low',
                 'sql_example': 'CREATE INDEX idx_users_email ON users(email);'},
                {'title': 'Оптимизировать запрос',
                 'description': 'Использовать LIMIT для ограничения результатов',
                 'priority': 'medium',
                 'category': 'performance',
                 'impact': 'medium',
                 'effort': 'low',
                 'sql_example': 'SELECT * FROM users LIMIT 100;'}]


class DataProcessor:
    """Класс для обработки данных."""

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Форматирует байты в читаемый вид."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    @staticmethod
    def format_duration(milliseconds: float) -> str:
        """Форматирует время в читаемый вид."""
        if milliseconds < 1000:
            return f"{milliseconds:.1f} мс"
        elif milliseconds < 60000:
            return f"{milliseconds / 1000:.1f} с"
        else:
            return f"{milliseconds / 60000:.1f} мин"

    @staticmethod
    def format_number(number: Union[int, float]) -> str:
        """Форматирует число с разделителями."""
        return f"{number:,}"

    @staticmethod
    def calculate_percentile(data: List[float], percentile: float) -> float:
        """Вычисляет процентиль."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    @staticmethod
    def group_by_time_interval(data: pd.DataFrame,
                               time_column: str,
                               interval: str = '1H') -> pd.DataFrame:
        """Группирует данные по временным интервалам."""
        data[time_column] = pd.to_datetime(data[time_column])
        return data.groupby(pd.Grouper(key=time_column, freq=interval)).sum()


class ExportUtils:
    """Класс для экспорта данных."""

    @staticmethod
    def export_to_markdown(data: Dict[str, Any], title: str) -> str:
        """Экспортирует данные в Markdown."""
        markdown = f"# {title}\n\n"
        markdown += f"**Дата создания:** {
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for key, value in data.items():
            markdown += f"## {key}\n\n"
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            markdown += f"- **{k}:** {v}\n"
                    else:
                        markdown += f"- {item}\n"
            elif isinstance(value, dict):
                for k, v in value.items():
                    markdown += f"- **{k}:** {v}\n"
            else:
                markdown += f"{value}\n"
            markdown += "\n"

        return markdown

    @staticmethod
    def export_to_json(data: Dict[str, Any]) -> str:
        """Экспортирует данные в JSON."""
        import json
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def export_to_csv(data: pd.DataFrame, filename: str) -> bytes:
        """Экспортирует DataFrame в CSV."""
        return data.to_csv(index=False).encode('utf-8')


class ValidationUtils:
    """Класс для валидации данных."""

    @staticmethod
    def validate_sql_query(query: str) -> Tuple[bool, str]:
        """Валидирует SQL запрос."""
        if not query or not query.strip():
            return False, "Запрос не может быть пустым"

        # Проверка на опасные операции
        dangerous_keywords = [
            'DROP',
            'DELETE',
            'UPDATE',
            'INSERT',
            'ALTER',
            'CREATE',
            'TRUNCATE']
        query_upper = query.upper().strip()

        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Запрос содержит опасную операцию: {keyword}"

        return True, "Запрос валиден"

    @staticmethod
    def validate_database_connection(dsn: str) -> Tuple[bool, str]:
        """Валидирует подключение к базе данных."""
        try:
            import psycopg2
            conn = psycopg2.connect(dsn)
            conn.close()
            return True, "Подключение успешно"
        except Exception as e:
            return False, f"Ошибка подключения: {str(e)}"

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Валидирует конфигурацию."""
        required_fields = ['host', 'port', 'database', 'user']

        for field in required_fields:
            if field not in config or not config[field]:
                return False, f"Отсутствует обязательное поле: {field}"

        return True, "Конфигурация валидна"


class CacheUtils:
    """Класс для работы с кэшем."""

    @staticmethod
    def get_cache_key(*args: Any) -> str:
        """Генерирует ключ кэша."""
        return "_".join(str(arg) for arg in args)

    @staticmethod
    def is_cache_valid(timestamp: float, ttl: int) -> bool:
        """Проверяет валидность кэша."""
        return (datetime.now().timestamp() - timestamp) < ttl

    @staticmethod
    def clear_old_cache(cache: Dict[str, Tuple[Any, float]], ttl: int) -> None:
        """Очищает устаревший кэш."""
        current_time = datetime.now().timestamp()
        keys_to_remove = [
            key for key, (_, timestamp) in cache.items()
            if (current_time - timestamp) > ttl
        ]
        for key in keys_to_remove:
            del cache[key]


# Глобальные экземпляры утилит
ui = UIComponents()
viz = DataVisualization()
mock = MockDataGenerator()
processor = DataProcessor()
exporter = ExportUtils()
validator = ValidationUtils()
cache_utils = CacheUtils()
