"""Модуль для парсинга и анализа планов выполнения PostgreSQL."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import sqlparse


class NodeType(Enum):
    """Типы узлов плана выполнения."""
    SEQ_SCAN = "Seq Scan"
    INDEX_SCAN = "Index Scan"
    INDEX_ONLY_SCAN = "Index Only Scan"
    BITMAP_HEAP_SCAN = "Bitmap Heap Scan"
    BITMAP_INDEX_SCAN = "Bitmap Index Scan"
    HASH_JOIN = "Hash Join"
    NESTED_LOOP = "Nested Loop"
    MERGE_JOIN = "Merge Join"
    SORT = "Sort"
    HASH = "Hash"
    AGGREGATE = "Aggregate"
    LIMIT = "Limit"
    SUBQUERY_SCAN = "Subquery Scan"
    CTE_SCAN = "CTE Scan"
    MATERIALIZE = "Materialize"
    APPEND = "Append"
    UNION = "Union"


@dataclass
class PlanNode:
    """Представляет узел плана выполнения."""
    node_type: str
    startup_cost: float
    total_cost: float
    plan_rows: int
    plan_width: int
    relation_name: Optional[str] = None
    index_name: Optional[str] = None
    strategy: Optional[str] = None
    join_type: Optional[str] = None
    filter: Optional[str] = None
    plans: Optional[List['PlanNode']] = None

    def __post_init__(self):
        if self.plans is None:
            self.plans = []


@dataclass
class QueryMetrics:
    """Метрики запроса."""
    estimated_time_ms: float
    estimated_io_mb: float
    estimated_memory_mb: float
    estimated_rows: int
    total_cost: float
    max_parallel_workers: int
    scan_types: List[str]
    join_types: List[str]


class PlanParser:
    """Парсер планов выполнения PostgreSQL."""

    def __init__(self):
        self.node_count = 0
        self.max_depth = 0

    def parse_explain_json(self, explain_json: Dict[str, Any]) -> PlanNode:
        """Парсит EXPLAIN JSON в дерево узлов."""
        if not explain_json or 'Plan' not in explain_json:
            raise ValueError("Неверный формат EXPLAIN JSON")

        self.node_count = 0
        self.max_depth = 0
        return self._parse_node(explain_json['Plan'], depth=0)

    def _parse_node(self, node_data: Dict[str, Any], depth: int) -> PlanNode:
        """Рекурсивно парсит узел плана."""
        self.node_count += 1
        self.max_depth = max(self.max_depth, depth)

        # Извлекаем основные параметры
        node = PlanNode(
            node_type=node_data.get('Node Type', 'Unknown'),
            startup_cost=float(node_data.get('Startup Cost', 0)),
            total_cost=float(node_data.get('Total Cost', 0)),
            plan_rows=int(node_data.get('Plan Rows', 0)),
            plan_width=int(node_data.get('Plan Width', 0)),
            relation_name=node_data.get('Relation Name'),
            index_name=node_data.get('Index Name'),
            strategy=node_data.get('Strategy'),
            join_type=node_data.get('Join Type'),
            filter=node_data.get('Filter')
        )

        # Рекурсивно парсим дочерние узлы
        if 'Plans' in node_data:
            node.plans = [
                self._parse_node(child, depth + 1)
                for child in node_data['Plans']
            ]

        return node

    def calculate_metrics(self, plan: PlanNode, config: Dict[str, Any]) -> QueryMetrics:
        """Вычисляет метрики запроса на основе плана."""
        # Базовые метрики
        total_cost = self._calculate_total_cost(plan)
        estimated_time_ms = self._estimate_execution_time(total_cost)
        estimated_io_mb = self._estimate_io_usage(plan, config)
        estimated_memory_mb = self._estimate_memory_usage(plan, config)
        estimated_rows = self._calculate_total_rows(plan)

        # Анализ типов операций
        scan_types = self._extract_scan_types(plan)
        join_types = self._extract_join_types(plan)
        max_parallel_workers = self._get_max_parallel_workers(plan)

        return QueryMetrics(
            estimated_time_ms=estimated_time_ms,
            estimated_io_mb=estimated_io_mb,
            estimated_memory_mb=estimated_memory_mb,
            estimated_rows=estimated_rows,
            total_cost=total_cost,
            max_parallel_workers=max_parallel_workers,
            scan_types=scan_types,
            join_types=join_types
        )

    def _calculate_total_cost(self, node: PlanNode) -> float:
        """Вычисляет общую стоимость запроса."""
        total = node.total_cost

        for child in node.plans:
            total += self._calculate_total_cost(child)

        return total

    def _estimate_execution_time(self, total_cost: float) -> float:
        """Оценивает время выполнения в миллисекундах."""
        # Эвристическая формула: cost * 0.01 ms
        return total_cost * 0.01

    def _estimate_io_usage(self, node: PlanNode, config: Dict[str, Any]) -> float:
        """Оценивает использование I/O в MB."""
        io_mb = 0.0

        # Базовая оценка на основе типа узла и количества строк
        if node.node_type in ["Seq Scan", "Bitmap Heap Scan"]:
            # Последовательное сканирование - читаем всю таблицу
            io_mb += node.plan_rows * node.plan_width / (1024 * 1024)
        elif node.node_type in ["Index Scan", "Index Only Scan"]:
            # Индексное сканирование - меньше I/O
            io_mb += node.plan_rows * node.plan_width / (1024 * 1024) * 0.1

        # Рекурсивно для дочерних узлов
        for child in node.plans:
            io_mb += self._estimate_io_usage(child, config)

        return io_mb

    def _estimate_memory_usage(self, node: PlanNode, config: Dict[str, Any]) -> float:
        """Оценивает использование памяти в MB."""
        memory_mb = 0.0
        work_mem = config.get('work_mem', 4)  # MB

        # Оценка на основе типа операции
        if node.node_type in ["Hash", "Hash Join"]:
            # Хеш-таблицы требуют памяти
            memory_mb += min(node.plan_rows * node.plan_width / (1024 * 1024), work_mem)
        elif node.node_type == "Sort":
            # Сортировка требует памяти
            memory_mb += min(node.plan_rows * node.plan_width / (1024 * 1024), work_mem)
        elif node.node_type == "Materialize":
            # Материализация требует памяти
            memory_mb += node.plan_rows * node.plan_width / (1024 * 1024)

        # Рекурсивно для дочерних узлов
        for child in node.plans:
            memory_mb += self._estimate_memory_usage(child, config)

        return memory_mb

    def _calculate_total_rows(self, node: PlanNode) -> int:
        """Вычисляет общее количество обрабатываемых строк."""
        total_rows = node.plan_rows

        # Для некоторых узлов суммируем дочерние
        if node.node_type in ["Append", "Union"]:
            for child in node.plans:
                total_rows += self._calculate_total_rows(child)
        else:
            # Для большинства узлов берем максимум из дочерних
            for child in node.plans:
                child_rows = self._calculate_total_rows(child)
                total_rows = max(total_rows, child_rows)

        return total_rows

    def _extract_scan_types(self, node: PlanNode) -> List[str]:
        """Извлекает типы сканирования из плана."""
        scan_types = []

        if "Scan" in node.node_type:
            scan_types.append(node.node_type)

        # Рекурсивно для дочерних узлов
        for child in node.plans:
            scan_types.extend(self._extract_scan_types(child))

        return list(set(scan_types))  # Убираем дубликаты

    def _extract_join_types(self, node: PlanNode) -> List[str]:
        """Извлекает типы соединений из плана."""
        join_types = []

        if "Join" in node.node_type:
            join_types.append(node.node_type)

        # Рекурсивно для дочерних узлов
        for child in node.plans:
            join_types.extend(self._extract_join_types(child))

        return list(set(join_types))  # Убираем дубликаты

    def _get_max_parallel_workers(self, node: PlanNode) -> int:
        """Определяет максимальное количество параллельных воркеров."""
        # Простая эвристика - для больших таблиц можем использовать параллелизм
        if node.plan_rows > 100000 and node.node_type == "Seq Scan":
            return min(4, max(1, node.plan_rows // 50000))

        return 1

    def get_plan_summary(self, plan: PlanNode) -> Dict[str, Any]:
        """Возвращает сводку плана выполнения."""
        return {
            "root_node_type": plan.node_type,
            "total_cost": plan.total_cost,
            "estimated_rows": plan.plan_rows,
            "node_count": self.node_count,
            "max_depth": self.max_depth,
            "scan_types": self._extract_scan_types(plan),
            "join_types": self._extract_join_types(plan)
        }


class SQLValidator:
    """Валидатор SQL запросов."""

    # Опасные операции
    DANGEROUS_OPERATIONS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
        'TRUNCATE', 'GRANT', 'REVOKE', 'COPY'
    ]

    def validate_sql(self, sql: str) -> Tuple[bool, List[str]]:
        """Валидирует SQL запрос."""
        errors = []

        if not sql or not sql.strip():
            errors.append("SQL запрос не может быть пустым")
            return False, errors

        # Парсим SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append("Не удалось распарсить SQL запрос")
                return False, errors
        except Exception as e:
            errors.append(f"Ошибка парсинга SQL: {str(e)}")
            return False, errors

        # Проверяем на опасные операции
        sql_upper = sql.upper()
        for operation in self.DANGEROUS_OPERATIONS:
            if operation in sql_upper:
                errors.append(f"Запрещенная операция: {operation}")

        # Проверяем базовую структуру
        if not any(keyword in sql_upper for keyword in ['SELECT', 'WITH', 'EXPLAIN']):
            errors.append("Запрос должен содержать SELECT, WITH или EXPLAIN")

        return len(errors) == 0, errors
