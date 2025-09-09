#!/usr/bin/env python3
"""
Модуль метрик для PostgreSQL SQL Analyzer.
Обеспечивает сбор и экспорт метрик производительности.
"""

import time
import psutil
import threading
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Метрика производительности."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryMetrics:
    """Метрики SQL запросов."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    slow_queries: int = 0
    expensive_queries: int = 0


class MetricsCollector:
    """Сборщик метрик производительности."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.query_metrics = QueryMetrics()
        self.llm_metrics = defaultdict(int)
        self.system_metrics = {}
        self.lock = threading.Lock()

        # Инициализация базовых метрик
        self._init_base_metrics()

    def _init_base_metrics(self):
        """Инициализация базовых метрик."""
        self.record_metric("app_startup", 1.0, {"component": "application"})
        self.record_metric("app_uptime", 0.0, {"component": "application"})

    def record_metric(self, name: str, value: float,
                      labels: Dict[str, str] = None,
                      metadata: Dict[str, Any] = None):
        """Записывает метрику."""
        try:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                metadata=metadata or {}
            )

            with self.lock:
                self.metrics_history.append(metric)

            logger.debug(f"Метрика записана: {name} = {value}")

        except Exception as e:
            logger.error(f"Ошибка записи метрики {name}: {e}")

    def record_query_metric(self, execution_time: float, success: bool,
                            is_slow: bool = False, is_expensive: bool = False):
        """Записывает метрики SQL запроса."""
        try:
            with self.lock:
                self.query_metrics.total_queries += 1

                if success:
                    self.query_metrics.successful_queries += 1
                else:
                    self.query_metrics.failed_queries += 1

                self.query_metrics.total_execution_time += execution_time
                self.query_metrics.avg_execution_time = (
                    self.query_metrics.total_execution_time
                    / self.query_metrics.total_queries
                )

                if is_slow:
                    self.query_metrics.slow_queries += 1

                if is_expensive:
                    self.query_metrics.expensive_queries += 1

            # Записываем детальную метрику
            self.record_metric(
                "sql_query_execution_time",
                execution_time,
                {
                    "success": str(success),
                    "slow": str(is_slow),
                    "expensive": str(is_expensive)
                }
            )

        except Exception as e:
            logger.error(f"Ошибка записи метрик запроса: {e}")

    def record_llm_metric(self, provider: str, operation: str,
                          response_time: float, success: bool):
        """Записывает метрики LLM операций."""
        try:
            with self.lock:
                self.llm_metrics[f"{provider}_{operation}_total"] += 1

                if success:
                    self.llm_metrics[f"{provider}_{operation}_success"] += 1
                else:
                    self.llm_metrics[f"{provider}_{operation}_failed"] += 1

            # Записываем детальную метрику
            self.record_metric(
                "llm_operation_response_time",
                response_time,
                {
                    "provider": provider,
                    "operation": operation,
                    "success": str(success)
                }
            )

        except Exception as e:
            logger.error(f"Ошибка записи метрик LLM: {e}")

    def update_system_metrics(self):
        """Обновляет системные метрики."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            self.system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "timestamp": datetime.now()
            }

            # Записываем системные метрики
            self.record_metric("system_cpu_percent", cpu_percent, {"component": "system"})
            self.record_metric("system_memory_percent", memory.percent, {"component": "system"})
            self.record_metric("system_disk_percent", disk.percent, {"component": "system"})

        except Exception as e:
            logger.error(f"Ошибка обновления системных метрик: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Возвращает сводку метрик."""
        try:
            with self.lock:
                # Обновляем время работы
                uptime = time.time() - self._get_startup_time()

                summary = {
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": uptime,
                    "uptime_formatted": str(timedelta(seconds=int(uptime))),
                    "total_metrics_recorded": len(self.metrics_history),
                    "query_metrics": {
                        "total_queries": self.query_metrics.total_queries,
                        "successful_queries": self.query_metrics.successful_queries,
                        "failed_queries": self.query_metrics.failed_queries,
                        "success_rate": (
                            self.query_metrics.successful_queries
                            / max(self.query_metrics.total_queries, 1) * 100
                        ),
                        "avg_execution_time": self.query_metrics.avg_execution_time,
                        "slow_queries": self.query_metrics.slow_queries,
                        "expensive_queries": self.query_metrics.expensive_queries
                    },
                    "llm_metrics": dict(self.llm_metrics),
                    "system_metrics": self.system_metrics,
                    "recent_metrics": self._get_recent_metrics(10)
                }

                return summary

        except Exception as e:
            logger.error(f"Ошибка получения сводки метрик: {e}")
            return {}

    def _get_recent_metrics(self, count: int) -> List[Dict[str, Any]]:
        """Получает последние метрики."""
        try:
            with self.lock:
                recent = list(self.metrics_history)[-count:]
                return [
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "labels": m.labels
                    }
                    for m in recent
                ]
        except Exception as e:
            logger.error(f"Ошибка получения последних метрик: {e}")
            return []

    def _get_startup_time(self) -> float:
        """Получает время запуска приложения."""
        try:
            for metric in self.metrics_history:
                if metric.name == "app_startup":
                    return metric.timestamp.timestamp()
        except Exception:
            pass
        return time.time()

    def export_prometheus_format(self) -> str:
        """Экспортирует метрики в формате Prometheus."""
        try:
            lines = []

            # Системные метрики
            if self.system_metrics:
                lines.append("# HELP system_cpu_percent CPU usage percentage")
                lines.append("# TYPE system_cpu_percent gauge")
                lines.append(f"system_cpu_percent {self.system_metrics.get('cpu_percent', 0)}")

                lines.append("# HELP system_memory_percent Memory usage percentage")
                lines.append("# TYPE system_memory_percent gauge")
                lines.append(f"system_memory_percent {self.system_metrics.get('memory_percent', 0)}")

                lines.append("# HELP system_disk_percent Disk usage percentage")
                lines.append("# TYPE system_disk_percent gauge")
                lines.append(f"system_disk_percent {self.system_metrics.get('disk_percent', 0)}")

            # Метрики запросов
            lines.append("# HELP sql_queries_total Total number of SQL queries")
            lines.append("# TYPE sql_queries_total counter")
            lines.append(f"sql_queries_total {self.query_metrics.total_queries}")

            lines.append("# HELP sql_queries_successful Total number of successful SQL queries")
            lines.append("# TYPE sql_queries_successful counter")
            lines.append(f"sql_queries_successful {self.query_metrics.successful_queries}")

            lines.append("# HELP sql_queries_failed Total number of failed SQL queries")
            lines.append("# TYPE sql_queries_failed counter")
            lines.append(f"sql_queries_failed {self.query_metrics.failed_queries}")

            lines.append("# HELP sql_query_execution_time_seconds Average SQL query execution time")
            lines.append("# TYPE sql_query_execution_time_seconds gauge")
            lines.append(f"sql_query_execution_time_seconds {self.query_metrics.avg_execution_time}")

            # Метрики LLM
            for key, value in self.llm_metrics.items():
                lines.append(f"# HELP llm_{key} LLM operation metric")
                lines.append(f"# TYPE llm_{key} counter")
                lines.append(f"llm_{key} {value}")

            # Время работы приложения
            uptime = time.time() - self._get_startup_time()
            lines.append("# HELP app_uptime_seconds Application uptime in seconds")
            lines.append("# TYPE app_uptime_seconds gauge")
            lines.append(f"app_uptime_seconds {uptime}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Ошибка экспорта метрик Prometheus: {e}")
            return ""

    def export_json_format(self) -> str:
        """Экспортирует метрики в формате JSON."""
        try:
            summary = self.get_metrics_summary()
            return json.dumps(summary, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Ошибка экспорта метрик JSON: {e}")
            return "{}"

    def clear_old_metrics(self, hours_to_keep: int = 24):
        """Очищает старые метрики."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_to_keep)

            with self.lock:
                # Фильтруем метрики по времени
                filtered_metrics = [
                    m for m in self.metrics_history
                    if m.timestamp > cutoff_time
                ]

                # Очищаем и добавляем отфильтрованные
                self.metrics_history.clear()
                for metric in filtered_metrics:
                    self.metrics_history.append(metric)

                deleted_count = len(filtered_metrics) - len(self.metrics_history)
                logger.info(f"Очищено {deleted_count} старых метрик")

        except Exception as e:
            logger.error(f"Ошибка очистки старых метрик: {e}")

    def start_periodic_collection(self, interval_seconds: int = 60):
        """Запускает периодический сбор метрик."""
        def collect_loop():
            while True:
                try:
                    self.update_system_metrics()
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Ошибка периодического сбора метрик: {e}")
                    time.sleep(interval_seconds)

        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        logger.info(f"Запущен периодический сбор метрик каждые {interval_seconds} секунд")


# Глобальный экземпляр
metrics_collector = MetricsCollector()


def record_query_metric(execution_time: float, success: bool,
                        is_slow: bool = False, is_expensive: bool = False):
    """Синхронная функция для записи метрик запроса."""
    metrics_collector.record_query_metric(execution_time, success, is_slow, is_expensive)


def record_llm_metric(provider: str, operation: str,
                      response_time: float, success: bool):
    """Синхронная функция для записи метрик LLM."""
    metrics_collector.record_llm_metric(provider, operation, response_time, success)


def get_metrics_summary() -> Dict[str, Any]:
    """Синхронная функция для получения сводки метрик."""
    return metrics_collector.get_metrics_summary()


def export_prometheus_metrics() -> str:
    """Синхронная функция для экспорта метрик Prometheus."""
    return metrics_collector.export_prometheus_format()
