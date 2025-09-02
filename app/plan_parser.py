"""Модуль для парсинга и анализа планов выполнения PostgreSQL."""

import json
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
        
        # Оценка на основе количества строк и ширины
        if node.plan_rows > 0 and node.plan_width > 0:
            # Примерная оценка: строки * ширина / 1024 / 1024
            io_mb += (node.plan_rows * node.plan_width) / (1024 * 1024)
        
        # Рекурсивно для дочерних узлов
        for child in node.plans:
            io_mb += self._estimate_io_usage(child, config)
        
        return io_mb
    
    def _estimate_memory_usage(self, node: PlanNode, config: Dict[str, Any]) -> float:
        """Оценивает использование памяти в MB."""
        memory_mb = 0.0
        work_mem = config.get('work_mem', 4)  # MB
        
        # Оценка для различных типов узлов
        if node.node_type in ['Hash', 'Sort', 'Hash Join']:
            # Для операций с хеш-таблицами и сортировкой
            if node.plan_rows > 0 and node.plan_width > 0:
                estimated_memory = (node.plan_rows * node.plan_width) / (1024 * 1024)
                memory_mb += min(estimated_memory, work_mem)
        
        # Рекурсивно для дочерних узлов
        for child in node.plans:
            memory_mb += self._estimate_memory_usage(child, config)
        
        return memory_mb
    
    def _calculate_total_rows(self, node: PlanNode) -> int:
        """Вычисляет общее количество строк."""
        total_rows = node.plan_rows
        
        for child in node.plans:
            total_rows += self._calculate_total_rows(child)
        
        return total_rows
    
    def _extract_scan_types(self, node: PlanNode) -> List[str]:
        """Извлекает типы сканирования."""
        scan_types = []
        
        if 'Scan' in node.node_type:
            scan_types.append(node.node_type)
        
        for child in node.plans:
            scan_types.extend(self._extract_scan_types(child))
        
        return list(set(scan_types))
    
    def _extract_join_types(self, node: PlanNode) -> List[str]:
        """Извлекает типы соединений."""
        join_types = []
        
        if 'Join' in node.node_type:
            join_types.append(node.node_type)
        
        for child in node.plans:
            join_types.extend(self._extract_join_types(child))
        
        return list(set(join_types))
    
    def _get_max_parallel_workers(self, node: PlanNode) -> int:
        """Получает максимальное количество параллельных воркеров."""
        # Простая эвристика: если есть параллельные операции
        if 'Parallel' in node.node_type:
            return 4  # Примерное значение
        return 1
    
    def get_plan_summary(self, plan: PlanNode) -> Dict[str, Any]:
        """Возвращает краткое описание плана."""
        return {
            "total_nodes": self.node_count,
            "max_depth": self.max_depth,
            "root_node_type": plan.node_type,
            "estimated_rows": self._calculate_total_rows(plan),
            "total_cost": self._calculate_total_cost(plan)
        }


class SQLValidator:
    """Валидатор SQL-запросов."""
    
    @staticmethod
    def validate_sql(sql: str) -> Tuple[bool, List[str]]:
        """Проверяет корректность SQL-запроса."""
        errors = []
        
        try:
            # Парсим SQL
            parsed = sqlparse.parse(sql)
            
            if not parsed:
                errors.append("Пустой SQL-запрос")
                return False, errors
            
            # Проверяем на опасные операции
            sql_upper = sql.upper()
            dangerous_operations = [
                'DELETE', 'UPDATE', 'INSERT', 'DROP', 'CREATE', 'ALTER',
                'TRUNCATE', 'GRANT', 'REVOKE', 'VACUUM', 'ANALYZE'
            ]
            
            for op in dangerous_operations:
                if op in sql_upper:
                    errors.append(f"Запрещенная операция: {op}")
            
            # Проверяем базовый синтаксис
            for statement in parsed:
                if statement.get_type() not in ['SELECT', 'WITH']:
                    errors.append(f"Неподдерживаемый тип запроса: {statement.get_type()}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Ошибка парсинга SQL: {str(e)}")
            return False, errors
