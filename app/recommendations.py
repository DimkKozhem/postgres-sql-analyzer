"""Модуль для генерации рекомендаций по оптимизации SQL-запросов."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import re


class Priority(Enum):
    """Приоритеты рекомендаций."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(Enum):
    """Категории рекомендаций."""
    INDEX = "index"
    JOIN = "join"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    QUERY_STRUCTURE = "query_structure"
    STATISTICS = "statistics"


@dataclass
class Recommendation:
    """Рекомендация по оптимизации."""
    id: str
    title: str
    description: str
    priority: Priority
    category: Category
    potential_improvement: str
    sql_example: Optional[str] = None
    ddl_example: Optional[str] = None
    configuration_example: Optional[str] = None
    estimated_impact: Optional[str] = None


class RecommendationEngine:
    """Движок для генерации рекомендаций."""
    
    def __init__(self):
        self.recommendations: List[Recommendation] = []
        self._initialize_recommendations()
    
    def _initialize_recommendations(self):
        """Инициализирует базовые рекомендации."""
        self.recommendations = [
            # Рекомендации по индексам
            Recommendation(
                id="seq_scan_to_index",
                title="Заменить последовательное сканирование на индексное",
                description="Обнаружено последовательное сканирование таблицы. Создание индекса может значительно ускорить запрос.",
                priority=Priority.HIGH,
                category=Category.INDEX,
                potential_improvement="10x-100x",
                sql_example="-- Текущий запрос:\nSELECT * FROM users WHERE email = 'user@example.com';\n\n-- Рекомендуемый индекс:\nCREATE INDEX idx_users_email ON users(email);",
                estimated_impact="Высокий - создание индекса по условию WHERE"
            ),
            
            Recommendation(
                id="composite_index",
                title="Создать составной индекс",
                description="Запрос использует несколько условий WHERE. Составной индекс может улучшить производительность.",
                priority=Priority.MEDIUM,
                category=Category.INDEX,
                potential_improvement="2x-10x",
                sql_example="-- Текущий запрос:\nSELECT * FROM orders WHERE user_id = 123 AND status = 'pending';\n\n-- Рекомендуемый индекс:\nCREATE INDEX idx_orders_user_status ON orders(user_id, status);",
                estimated_impact="Средний - оптимизация составных условий"
            ),
            
            # Рекомендации по соединениям
            Recommendation(
                id="nested_loop_to_hash_join",
                title="Оптимизировать вложенные циклы",
                description="Обнаружены вложенные циклы для соединения таблиц. Добавление индексов или изменение порядка соединений может улучшить производительность.",
                priority=Priority.HIGH,
                category=Category.JOIN,
                potential_improvement="5x-50x",
                sql_example="-- Добавить индекс для внешнего ключа:\nCREATE INDEX idx_orders_user_id ON orders(user_id);\n\n-- Или изменить порядок соединений в запросе",
                estimated_impact="Высокий - оптимизация алгоритма соединения"
            ),
            
            Recommendation(
                id="hash_join_optimization",
                title="Оптимизировать хеш-соединения",
                description="Хеш-соединения требуют значительной памяти. Увеличение work_mem может улучшить производительность.",
                priority=Priority.MEDIUM,
                category=Category.JOIN,
                potential_improvement="2x-5x",
                configuration_example="-- Увеличить work_mem:\nSET work_mem = '64MB';  -- или больше в зависимости от размера данных",
                estimated_impact="Средний - оптимизация использования памяти"
            ),
            
            # Рекомендации по памяти
            Recommendation(
                id="sort_optimization",
                title="Оптимизировать операции сортировки",
                description="Обнаружены операции сортировки. Увеличение work_mem или создание индексов может улучшить производительность.",
                priority=Priority.MEDIUM,
                category=Category.MEMORY,
                potential_improvement="2x-10x",
                configuration_example="-- Увеличить work_mem для сортировки:\nSET work_mem = '32MB';",
                sql_example="-- Создать индекс для избежания сортировки:\nCREATE INDEX idx_users_name ON users(name);",
                estimated_impact="Средний - оптимизация операций сортировки"
            ),
            
            Recommendation(
                id="hash_aggregate_optimization",
                title="Оптимизировать хеш-агрегацию",
                description="Хеш-агрегация требует значительной памяти. Увеличение work_mem может улучшить производительность.",
                priority=Priority.MEDIUM,
                category=Category.MEMORY,
                potential_improvement="2x-5x",
                configuration_example="-- Увеличить work_mem для агрегации:\nSET work_mem = '64MB';",
                estimated_impact="Средний - оптимизация агрегатных операций"
            ),
            
            # Рекомендации по конфигурации
            Recommendation(
                id="work_mem_optimization",
                title="Оптимизировать work_mem",
                description="Текущее значение work_mem может быть недостаточным для эффективного выполнения запроса.",
                priority=Priority.LOW,
                category=Category.CONFIGURATION,
                potential_improvement="1.5x-3x",
                configuration_example="-- Рекомендуемое значение work_mem:\nSET work_mem = '128MB';  -- для сложных запросов",
                estimated_impact="Низкий - тонкая настройка параметров"
            ),
            
            Recommendation(
                id="shared_buffers_optimization",
                title="Оптимизировать shared_buffers",
                description="Увеличение shared_buffers может улучшить кэширование и уменьшить I/O операции.",
                priority=Priority.LOW,
                category=Category.CONFIGURATION,
                potential_improvement="1.2x-2x",
                configuration_example="-- Рекомендуемое значение shared_buffers:\nSET shared_buffers = '256MB';  -- 25% от доступной RAM",
                estimated_impact="Низкий - улучшение кэширования"
            ),
            
            # Рекомендации по структуре запроса
            Recommendation(
                id="limit_optimization",
                title="Добавить LIMIT для ограничения результатов",
                description="Запрос может возвращать большое количество строк. Добавление LIMIT может улучшить производительность.",
                priority=Priority.MEDIUM,
                category=Category.QUERY_STRUCTURE,
                potential_improvement="2x-10x",
                sql_example="-- Добавить LIMIT:\nSELECT * FROM users WHERE active = true LIMIT 100;",
                estimated_impact="Средний - ограничение объема возвращаемых данных"
            ),
            
            Recommendation(
                id="cte_optimization",
                title="Оптимизировать CTE (Common Table Expressions)",
                description="CTE могут быть неэффективными для больших наборов данных. Рассмотрите использование подзапросов или временных таблиц.",
                priority=Priority.LOW,
                category=Category.QUERY_STRUCTURE,
                potential_improvement="1.5x-3x",
                sql_example="-- Вместо CTE использовать подзапрос:\nSELECT * FROM (\n  SELECT user_id, COUNT(*) as order_count\n  FROM orders\n  GROUP BY user_id\n) user_stats WHERE order_count > 10;",
                estimated_impact="Низкий - оптимизация структуры запроса"
            ),
            
            # Рекомендации по статистике
            Recommendation(
                id="update_statistics",
                title="Обновить статистику таблиц",
                description="Статистика таблиц может быть устаревшей, что приводит к неоптимальным планам выполнения.",
                priority=Priority.LOW,
                category=Category.STATISTICS,
                potential_improvement="1.2x-2x",
                sql_example="-- Обновить статистику:\nANALYZE users;\nANALYZE orders;",
                estimated_impact="Низкий - улучшение качества планировщика"
            )
        ]
    
    def analyze_plan(self, plan_data: Dict[str, Any], metrics: Dict[str, Any], config: Dict[str, Any]) -> List[Recommendation]:
        """Анализирует план выполнения и генерирует рекомендации."""
        applicable_recommendations = []
        
        # Анализируем каждый узел плана
        self._analyze_plan_node(plan_data.get('Plan', {}), applicable_recommendations, metrics, config)
        
        # Анализируем общие метрики
        self._analyze_metrics(metrics, applicable_recommendations, config)
        
        # Сортируем по приоритету
        applicable_recommendations.sort(key=lambda r: self._priority_score(r.priority), reverse=True)
        
        return applicable_recommendations
    
    def _analyze_plan_node(self, node: Dict[str, Any], recommendations: List[Recommendation], metrics: Dict[str, Any], config: Dict[str, Any]):
        """Рекурсивно анализирует узлы плана."""
        if not node:
            return
        
        node_type = node.get('Node Type', '')
        
        # Проверяем конкретные типы узлов
        if 'Seq Scan' in node_type:
            self._check_seq_scan_recommendations(node, recommendations, metrics)
        
        elif 'Nested Loop' in node_type:
            self._check_nested_loop_recommendations(node, recommendations, metrics)
        
        elif 'Sort' in node_type:
            self._check_sort_recommendations(node, recommendations, config)
        
        elif 'Hash' in node_type:
            self._check_hash_recommendations(node, recommendations, config)
        
        # Рекурсивно анализируем дочерние узлы
        if 'Plans' in node:
            for child in node['Plans']:
                self._analyze_plan_node(child, recommendations, metrics, config)
    
    def _check_seq_scan_recommendations(self, node: Dict[str, Any], recommendations: List[Recommendation], metrics: Dict[str, Any]):
        """Проверяет рекомендации для последовательного сканирования."""
        relation_name = node.get('Relation Name', '')
        plan_rows = node.get('Plan Rows', 0)
        
        # Если таблица большая, рекомендуем создать индекс
        if plan_rows > 10000:  # Порог для "большой" таблицы
            seq_scan_rec = next((r for r in self.recommendations if r.id == "seq_scan_to_index"), None)
            if seq_scan_rec:
                # Клонируем рекомендацию с конкретными деталями
                specific_rec = Recommendation(
                    id=f"seq_scan_{relation_name}",
                    title=f"Создать индекс для таблицы {relation_name}",
                    description=f"Таблица {relation_name} сканируется последовательно ({plan_rows:,} строк). Создание индекса может значительно ускорить запрос.",
                    priority=Priority.HIGH,
                    category=Category.INDEX,
                    potential_improvement="10x-100x",
                    sql_example=f"-- Создать индекс для таблицы {relation_name}:\nCREATE INDEX idx_{relation_name}_id ON {relation_name}(id);",
                    estimated_impact="Высокий - создание индекса для большой таблицы"
                )
                recommendations.append(specific_rec)
    
    def _check_nested_loop_recommendations(self, node: Dict[str, Any], recommendations: List[Recommendation], metrics: Dict[str, Any]):
        """Проверяет рекомендации для вложенных циклов."""
        nested_loop_rec = next((r for r in self.recommendations if r.id == "nested_loop_to_hash_join"), None)
        if nested_loop_rec:
            recommendations.append(nested_loop_rec)
    
    def _check_sort_recommendations(self, node: Dict[str, Any], recommendations: List[Recommendation], config: Dict[str, Any]):
        """Проверяет рекомендации для операций сортировки."""
        plan_rows = node.get('Plan Rows', 0)
        work_mem = config.get('work_mem', 4)
        
        # Если сортировка большая, рекомендуем увеличить work_mem
        if plan_rows > 10000 and work_mem < 32:
            sort_rec = next((r for r in self.recommendations if r.id == "sort_optimization"), None)
            if sort_rec:
                recommendations.append(sort_rec)
    
    def _check_hash_recommendations(self, node: Dict[str, Any], recommendations: List[Recommendation], config: Dict[str, Any]):
        """Проверяет рекомендации для хеш-операций."""
        plan_rows = node.get('Plan Rows', 0)
        work_mem = config.get('work_mem', 4)
        
        # Если хеш-операция большая, рекомендуем увеличить work_mem
        if plan_rows > 10000 and work_mem < 64:
            hash_rec = next((r for r in self.recommendations if r.id == "hash_aggregate_optimization"), None)
            if hash_rec:
                recommendations.append(hash_rec)
    
    def _analyze_metrics(self, metrics: Dict[str, Any], recommendations: List[Recommendation], config: Dict[str, Any]):
        """Анализирует общие метрики запроса."""
        estimated_time = metrics.get('estimated_time_ms', 0)
        estimated_io = metrics.get('estimated_io_mb', 0)
        total_cost = metrics.get('total_cost', 0)
        
        # Если запрос медленный, добавляем общие рекомендации
        if estimated_time > 100:  # Порог для "медленного" запроса
            limit_rec = next((r for r in self.recommendations if r.id == "limit_optimization"), None)
            if limit_rec:
                recommendations.append(limit_rec)
        
        # Если I/O высокий, рекомендуем оптимизировать shared_buffers
        if estimated_io > 100:  # Порог для "высокого" I/O
            shared_buffers_rec = next((r for r in self.recommendations if r.id == "shared_buffers_optimization"), None)
            if shared_buffers_rec:
                recommendations.append(shared_buffers_rec)
        
        # Если стоимость запроса высокая, рекомендуем обновить статистику
        if total_cost > 1000:  # Порог для "дорогого" запроса
            stats_rec = next((r for r in self.recommendations if r.id == "update_statistics"), None)
            if stats_rec:
                recommendations.append(stats_rec)
    
    def _priority_score(self, priority: Priority) -> int:
        """Возвращает числовой score для приоритета."""
        return {
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }[priority]
    
    def get_recommendations_by_category(self, category: Category) -> List[Recommendation]:
        """Возвращает рекомендации по категории."""
        return [r for r in self.recommendations if r.category == category]
    
    def get_recommendations_by_priority(self, priority: Priority) -> List[Recommendation]:
        """Возвращает рекомендации по приоритету."""
        return [r for r in self.recommendations if r.priority == priority]
