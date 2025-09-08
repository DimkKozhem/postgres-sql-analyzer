"""Основной модуль анализатора SQL-запросов PostgreSQL."""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .database import DatabaseConnection
from .plan_parser import PlanParser, SQLValidator, QueryMetrics
from .recommendations import RecommendationEngine, Recommendation
from .config import get_default_config

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Результат анализа SQL-запроса."""
    sql: str
    is_valid: bool
    validation_errors: List[str]
    explain_json: Optional[Dict[str, Any]]
    plan_summary: Optional[Dict[str, Any]]
    metrics: Optional[QueryMetrics]
    recommendations: List[Recommendation]
    analysis_time: float
    config_used: Dict[str, Any]


class SQLAnalyzer:
    """Основной класс анализатора SQL-запросов."""

    def __init__(self, dsn: str, config: Optional[Dict[str, Any]] = None):
        if not dsn:
            raise ValueError("DSN подключения к базе данных обязателен")

        self.dsn = dsn

        # Инициализируем компоненты
        self.db_connection = DatabaseConnection(dsn)

        self.plan_parser = PlanParser()
        self.recommendation_engine = RecommendationEngine()
        self.sql_validator = SQLValidator()

        # Загружаем конфигурацию по умолчанию
        self.config = get_default_config()

        # Обновляем конфигурацию если передана
        if config:
            self.config.update(config)

        # Инициализируем LLM интеграцию если включена
        self.llm_integration = None
        if self.config.get('enable_ai_recommendations'):
            try:
                from .llm_integration import LLMIntegration
                self.llm_integration = LLMIntegration(self.config)
                logger.info("LLM интеграция инициализирована")
            except ImportError as e:
                logger.warning(f"LLM интеграция недоступна: {e}")
            except Exception as e:
                logger.error(f"Ошибка инициализации LLM: {e}")

    def analyze_sql(self,
                    sql: str,
                    custom_config: Optional[Dict[str,
                                                 Any]] = None) -> AnalysisResult:
        """Анализирует SQL-запрос и возвращает результат анализа."""
        import time
        start_time = time.time()

        # Обновляем конфигурацию
        if custom_config:
            self.config.update(custom_config)

        # Валидируем SQL
        is_valid, validation_errors = self.sql_validator.validate_sql(sql)

        explain_json = None
        plan_summary = None
        metrics = None
        recommendations = []

        if is_valid:
            try:
                # Получаем EXPLAIN JSON
                explain_json = self.db_connection.execute_explain(sql)

                if explain_json:
                    # Парсим план
                    plan = self.plan_parser.parse_explain_json(explain_json)

                    # Получаем сводку плана
                    plan_summary = self.plan_parser.get_plan_summary(plan)

                    # Вычисляем метрики
                    metrics = self.plan_parser.calculate_metrics(
                        plan, self.config)

                    # Генерируем рекомендации
                    recommendations = self.recommendation_engine.analyze_plan(
                        explain_json,
                        metrics.__dict__,
                        self.config
                    )

            except Exception as e:
                logger.error(f"Ошибка анализа SQL: {e}")
                validation_errors.append(f"Ошибка анализа: {str(e)}")
                is_valid = False

        analysis_time = time.time() - start_time

        # Получаем AI-рекомендации если включены
        ai_recommendations = []
        if self.llm_integration and is_valid and explain_json:
            try:
                ai_recommendations = self._get_ai_recommendations(
                    sql, explain_json)
                logger.info(
                    f"Получено {
                        len(ai_recommendations)} AI-рекомендаций")
            except Exception as e:
                logger.error(f"Ошибка получения AI-рекомендаций: {e}")

        # Объединяем обычные и AI-рекомендации
        all_recommendations = recommendations + ai_recommendations

        return AnalysisResult(
            sql=sql,
            is_valid=is_valid,
            validation_errors=validation_errors,
            explain_json=explain_json,
            plan_summary=plan_summary,
            metrics=metrics,
            recommendations=all_recommendations,
            analysis_time=analysis_time,
            config_used=self.config.copy()
        )

    def get_pg_stat_statements(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает статистику из pg_stat_statements."""
        return self.db_connection.get_pg_stat_statements(limit)

    def update_config(self, new_config: Dict[str, Any]):
        """Обновляет конфигурацию анализатора."""
        self.config.update(new_config)
        logger.info(f"Конфигурация обновлена: {new_config}")

    def get_config(self) -> Dict[str, Any]:
        """Возвращает текущую конфигурацию."""
        return self.config.copy()

    def export_analysis_report(
            self,
            result: AnalysisResult,
            format: str = "json") -> str:
        """Экспортирует результат анализа в указанном формате."""
        if format.lower() == "json":
            return self._export_json(result)
        elif format.lower() == "text":
            return self._export_text(result)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    def _export_json(self, result: AnalysisResult) -> str:
        """Экспортирует результат в JSON формате."""
        export_data = {
            "sql": result.sql,
            "is_valid": result.is_valid,
            "validation_errors": result.validation_errors,
            "plan_summary": result.plan_summary,
            "metrics": result.metrics.__dict__ if result.metrics else None,
            "recommendations": [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority.value,
                    "category": rec.category.value,
                    "potential_improvement": rec.potential_improvement,
                    "estimated_impact": rec.estimated_impact
                }
                for rec in result.recommendations
            ],
            "analysis_time": result.analysis_time,
            "config_used": result.config_used
        }

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _export_text(self, result: AnalysisResult) -> str:
        """Экспортирует результат в текстовом формате."""
        lines = []
        lines.append("=" * 80)
        lines.append("ОТЧЕТ ПО АНАЛИЗУ SQL-ЗАПРОСА")
        lines.append("=" * 80)
        lines.append("")

        # SQL запрос
        lines.append("SQL ЗАПРОС:")
        lines.append("-" * 40)
        lines.append(result.sql)
        lines.append("")

        # Валидация
        lines.append("ВАЛИДАЦИЯ:")
        lines.append("-" * 40)
        if result.is_valid:
            lines.append("✓ Запрос валиден")
        else:
            lines.append("✗ Запрос содержит ошибки:")
            for error in result.validation_errors:
                lines.append(f"  - {error}")
        lines.append("")

        # Сводка плана
        if result.plan_summary:
            lines.append("СВОДКА ПЛАНА ВЫПОЛНЕНИЯ:")
            lines.append("-" * 40)
            for key, value in result.plan_summary.items():
                lines.append(f"{key}: {value}")
            lines.append("")

        # Метрики
        if result.metrics:
            lines.append("МЕТРИКИ ЗАПРОСА:")
            lines.append("-" * 40)
            lines.append(
                f"Ожидаемое время выполнения: {
                    result.metrics.estimated_time_ms:.2f} мс")
            lines.append(
                f"Ожидаемое использование I/O: {result.metrics.estimated_io_mb:.2f} MB")
            lines.append(
                f"Ожидаемое использование памяти: {
                    result.metrics.estimated_memory_mb:.2f} MB")
            lines.append(
                f"Ожидаемое количество строк: {
                    result.metrics.estimated_rows:,}")
            lines.append(f"Общая стоимость: {result.metrics.total_cost:.2f}")
            lines.append("")

        # Рекомендации
        if result.recommendations:
            lines.append("РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
            lines.append("-" * 40)

            # Группируем по приоритету
            high_recs = [
                r for r in result.recommendations if r.priority.value == "high"]
            medium_recs = [
                r for r in result.recommendations if r.priority.value == "medium"]
            low_recs = [
                r for r in result.recommendations if r.priority.value == "low"]

            if high_recs:
                lines.append("ВЫСОКИЙ ПРИОРИТЕТ:")
                for rec in high_recs:
                    lines.append(f"  • {rec.title}")
                    lines.append(f"    {rec.description}")
                    lines.append(
                        f"    Потенциальное улучшение: {
                            rec.potential_improvement}")
                    lines.append("")

            if medium_recs:
                lines.append("СРЕДНИЙ ПРИОРИТЕТ:")
                for rec in medium_recs:
                    lines.append(f"  • {rec.title}")
                    lines.append(f"    {rec.description}")
                    lines.append(
                        f"    Потенциальное улучшение: {
                            rec.potential_improvement}")
                    lines.append("")

            if low_recs:
                lines.append("НИЗКИЙ ПРИОРИТЕТ:")
                for rec in low_recs:
                    lines.append(f"  • {rec.title}")
                    lines.append(f"    {rec.description}")
                    lines.append(
                        f"    Потенциальное улучшение: {
                            rec.potential_improvement}")
                    lines.append("")

        # Время анализа
        lines.append("ВРЕМЯ АНАЛИЗА:")
        lines.append("-" * 40)
        lines.append(f"{result.analysis_time:.3f} секунд")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def get_example_queries(self) -> List[Dict[str, str]]:
        """Возвращает примеры тестовых запросов."""
        return [
            {
                "name": "Простой SELECT",
                "description": "Базовый запрос для тестирования",
                "sql": "SELECT * FROM users LIMIT 10;"
            },
            {
                "name": "JOIN с фильтрацией",
                "description": "Запрос с соединением таблиц и условиями WHERE",
                "sql": """
                SELECT u.name, o.order_date, o.total_amount
                FROM users u
                JOIN orders o ON u.id = o.user_id
                WHERE u.active = true AND o.status = 'completed'
                ORDER BY o.order_date DESC
                LIMIT 100;
                """
            },
            {
                "name": "Сложный агрегатный запрос",
                "description": "Запрос с группировкой и агрегатными функциями",
                "sql": """
                WITH user_stats AS (
                    SELECT
                        u.id,
                        u.name,
                        COUNT(o.id) as order_count,
                        SUM(o.total_amount) as total_spent,
                        AVG(o.total_amount) as avg_order_value
                    FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    WHERE u.registration_date >= '2023-01-01'
                    GROUP BY u.id, u.name
                )
                SELECT * FROM user_stats
                WHERE order_count > 5
                ORDER BY total_spent DESC;
                """
            }
        ]

    def analyze_example_query(self, example_index: int) -> AnalysisResult:
        """Анализирует пример запроса по индексу."""
        examples = self.get_example_queries()
        if 0 <= example_index < len(examples):
            return self.analyze_sql(examples[example_index]["sql"])
        else:
            raise ValueError(f"Неверный индекс примера: {example_index}")

    async def _get_ai_recommendations(
            self, sql: str, explain_json: Dict[str, Any]) -> List[Any]:
        """Получает AI-рекомендации от LLM провайдера."""
        if not self.llm_integration:
            return []

        try:
            # Получаем рекомендации от LLM
            recommendations = await self.llm_integration.get_recommendations(
                sql_query=sql,
                execution_plan=explain_json,
                provider=self.config.get('ai_provider', 'auto')
            )

            # Фильтруем по порогу уверенности
            confidence_threshold = self.config.get(
                'ai_confidence_threshold', 0.7)
            filtered_recommendations = [
                rec for rec in recommendations
                if rec.confidence >= confidence_threshold
            ]

            logger.info(
                f"Получено {
                    len(recommendations)} AI-рекомендаций, отфильтровано {
                    len(filtered_recommendations)}")
            return filtered_recommendations

        except Exception as e:
            logger.error(f"Ошибка получения AI-рекомендаций: {e}")
            return []
