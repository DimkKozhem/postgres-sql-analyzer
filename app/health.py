#!/usr/bin/env python3
"""
Модуль health checks для PostgreSQL SQL Analyzer.
Обеспечивает мониторинг состояния приложения и зависимостей.
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthStatus:
    """Статус здоровья компонента."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    response_time: float
    details: Dict[str, Any] = None


@dataclass
class SystemMetrics:
    """Системные метрики."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, float]
    timestamp: datetime


class HealthChecker:
    """Основной класс для проверки здоровья приложения."""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = []
    
    async def check_database_connection(self, dsn: str = None) -> HealthStatus:
        """Проверяет подключение к базе данных."""
        start_time = time.time()
        
        try:
            if dsn:
                from app.analyzer import SQLAnalyzer
                analyzer = SQLAnalyzer(dsn, mock_mode=False)
                # Простая проверка подключения
                test_result = analyzer.analyze_sql("SELECT 1 as health_check;")
                response_time = time.time() - start_time
                
                return HealthStatus(
                    name="database_connection",
                    status="healthy",
                    message="База данных доступна",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={"query_time": response_time}
                )
            else:
                return HealthStatus(
                    name="database_connection",
                    status="degraded",
                    message="DSN не настроен",
                    timestamp=datetime.now(),
                    response_time=0.0
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthStatus(
                name="database_connection",
                status="unhealthy",
                message=f"Ошибка подключения: {str(e)}",
                timestamp=datetime.now(),
                response_time=response_time,
                details={"error": str(e)}
            )
    
    async def check_llm_providers(self, config: Dict[str, Any]) -> List[HealthStatus]:
        """Проверяет доступность LLM провайдеров."""
        checks = []
        
        # OpenAI
        if config.get("openai_api_key"):
            start_time = time.time()
            try:
                import openai
                openai.api_key = config["openai_api_key"]
                models = openai.Model.list()
                response_time = time.time() - start_time
                
                checks.append(HealthStatus(
                    name="openai_provider",
                    status="healthy",
                    message="OpenAI API доступен",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={"models_count": len(models.data) if hasattr(models, 'data') else 0}
                ))
            except Exception as e:
                response_time = time.time() - start_time
                checks.append(HealthStatus(
                    name="openai_provider",
                    status="unhealthy",
                    message=f"OpenAI API недоступен: {str(e)}",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={"error": str(e)}
                ))
        
        # Anthropic
        if config.get("anthropic_api_key"):
            start_time = time.time()
            try:
                import requests
                response = requests.get(
                    "https://api.anthropic.com/v1/models",
                    headers={"x-api-key": config["anthropic_api_key"]},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    checks.append(HealthStatus(
                        name="anthropic_provider",
                        status="healthy",
                        message="Anthropic API доступен",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        details={"status_code": response.status_code}
                    ))
                else:
                    checks.append(HealthStatus(
                        name="anthropic_provider",
                        status="unhealthy",
                        message=f"Anthropic API недоступен: {response.status_code}",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        details={"status_code": response.status_code}
                    ))
            except Exception as e:
                response_time = time.time() - start_time
                checks.append(HealthStatus(
                    name="anthropic_provider",
                    status="unhealthy",
                    message=f"Anthropic API недоступен: {str(e)}",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={"error": str(e)}
                ))
        
        # Local LLM
        if config.get("local_llm_url"):
            start_time = time.time()
            try:
                import requests
                response = requests.get(
                    f"{config['local_llm_url']}/api/tags",
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    checks.append(HealthStatus(
                        name="local_llm_provider",
                        status="healthy",
                        message="Локальный LLM доступен",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        details={"status_code": response.status_code}
                    ))
                else:
                    checks.append(HealthStatus(
                        name="local_llm_provider",
                        status="unhealthy",
                        message=f"Локальный LLM недоступен: {response.status_code}",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        details={"status_code": response.status_code}
                    ))
            except Exception as e:
                response_time = time.time() - start_time
                checks.append(HealthStatus(
                    name="local_llm_provider",
                    status="unhealthy",
                    message=f"Локальный LLM недоступен: {str(e)}",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={"error": str(e)}
                ))
        
        return checks
    
    def get_system_metrics(self) -> SystemMetrics:
        """Получает системные метрики."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                timestamp=datetime.now()
            )
        except Exception as e:
            # Fallback если psutil недоступен
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                timestamp=datetime.now()
            )
    
    def get_uptime(self) -> float:
        """Возвращает время работы приложения."""
        return time.time() - self.start_time
    
    async def run_all_checks(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполняет все проверки здоровья."""
        start_time = time.time()
        
        # Системные метрики
        system_metrics = self.get_system_metrics()
        
        # Проверки
        checks = []
        
        # Проверка БД
        db_check = await self.check_database_connection(config.get("dsn") if config else None)
        checks.append(db_check)
        
        # Проверка LLM провайдеров
        if config:
            llm_checks = await self.check_llm_providers(config)
            checks.extend(llm_checks)
        
        # Общий статус
        overall_status = "healthy"
        if any(check.status == "unhealthy" for check in checks):
            overall_status = "unhealthy"
        elif any(check.status == "degraded" for check in checks):
            overall_status = "degraded"
        
        total_time = time.time() - start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "response_time": total_time,
            "checks": [check.__dict__ for check in checks],
            "system_metrics": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
                "network_io": system_metrics.network_io
            }
        }


# Глобальный экземпляр
health_checker = HealthChecker()


def get_health_status(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Синхронная обертка для получения статуса здоровья."""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(health_checker.run_all_checks(config))
    except RuntimeError:
        # Если нет event loop, создаем новый
        return asyncio.run(health_checker.run_all_checks(config))
