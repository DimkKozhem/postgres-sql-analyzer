"""Типы данных для PostgreSQL SQL Analyzer."""

from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Literal
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class ConnectionType(Enum):
    """Типы подключения к базе данных."""
    DIRECT = "direct"
    SSH_TUNNEL = "ssh_tunnel"


class LLMProvider(Enum):
    """Провайдеры LLM."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class QueryType(Enum):
    """Типы SQL запросов."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"


class LogLevel(Enum):
    """Уровни логирования."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    host: str
    port: int
    database: str
    user: str
    password: str
    connection_type: ConnectionType = ConnectionType.DIRECT


@dataclass
class SSHConfig:
    """Конфигурация SSH туннеля."""
    host: str
    port: int = 22
    user: str = "root"
    key_path: str = "~/.ssh/id_rsa"
    timeout: int = 30


@dataclass
class LLMConfig:
    """Конфигурация LLM."""
    provider: LLMProvider
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    base_url: Optional[str] = None


@dataclass
class QueryMetrics:
    """Метрики SQL запроса."""
    query_id: str
    query_text: str
    execution_time: float
    total_time: float
    rows: int
    calls: int
    mean_time: float
    stddev_time: float
    min_time: float
    max_time: float


@dataclass
class ExecutionPlan:
    """План выполнения SQL запроса."""
    query_plan: List[Dict[str, Any]]
    total_cost: float
    total_rows: int
    execution_time: Optional[float] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class DatabaseInfo:
    """Информация о базе данных."""
    version: str
    tables: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    connection_info: Dict[str, Any]
    total_size: int
    table_count: int
    index_count: int


@dataclass
class Recommendation:
    """Рекомендация по оптимизации."""
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    category: str  # "performance", "security", "maintenance"
    impact: str  # "high", "medium", "low"
    effort: str  # "high", "medium", "low"
    sql_example: Optional[str] = None


@dataclass
class LogEntry:
    """Запись лога PostgreSQL."""
    timestamp: str
    level: LogLevel
    message: str
    query_id: Optional[str] = None
    duration: Optional[float] = None
    user: Optional[str] = None
    database: Optional[str] = None


@dataclass
class AnalysisResult:
    """Результат анализа SQL запроса."""
    query: str
    execution_plan: Optional[ExecutionPlan]
    recommendations: List[Recommendation]
    metrics: Optional[QueryMetrics]
    warnings: List[str]
    errors: List[str]

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


@dataclass
class CacheConfig:
    """Конфигурация кэширования."""
    enabled: bool = True
    ttl: int = 300  # Time to live in seconds
    max_size: int = 1000
    backend: str = "memory"  # "memory", "redis", "file"


# Типы для функций
DatabaseConnectionFunc = Callable[[], Any]
SQLExecutionFunc = Callable[[str], Optional[Dict[str, Any]]]
AnalysisFunc = Callable[[str], AnalysisResult]
RecommendationFunc = Callable[[str, Dict[str, Any]], List[Recommendation]]

# Типы для данных
QueryData = Union[str, List[str]]
MetricsData = Dict[str, Union[int, float, str]]
ConfigData = Dict[str, Union[str, int, bool, float]]
LogData = List[LogEntry]
StatisticsData = Dict[str, Any]

# Типы для UI
UIComponent = Callable[[], None]
TabFunction = Callable[[str, bool], None]
StatusFunction = Callable[[], Tuple[bool, str]]

# Типы для экспорта
ExportFormat = Literal["json", "csv", "markdown", "pdf"]
ExportData = Dict[str, Any]
ExportResult = Tuple[bool, str, Optional[bytes]]

# Типы для валидации
ValidationResult = Tuple[bool, str]
SQLValidationResult = Tuple[bool, str, Optional[List[str]]]

# Типы для кэширования
CacheKey = Union[str, Tuple[str, ...]]
CacheValue = Any
CacheEntry = Tuple[CacheValue, float]  # (value, timestamp)

# Типы для потоков
StreamData = Union[str, bytes, Dict[str, Any]]
StreamHandler = Callable[[StreamData], None]

# Типы для конфигурации
ConfigSection = Dict[str, Any]
ConfigValidator = Callable[[ConfigSection], ValidationResult]

# Типы для метрик
MetricValue = Union[int, float, str, bool]
MetricData = Dict[str, MetricValue]
MetricSeries = List[MetricData]

# Типы для отчетов
ReportData = Dict[str, Any]
ReportGenerator = Callable[[ReportData], ExportResult]
ReportTemplate = Dict[str, str]

# Типы для безопасности
SecurityLevel = Literal["low", "medium", "high", "critical"]
SecurityCheck = Callable[[str], Tuple[bool, str, SecurityLevel]]

# Типы для мониторинга
HealthStatus = Literal["healthy", "warning", "error", "critical"]
HealthCheck = Callable[[], Tuple[HealthStatus, str, Dict[str, Any]]]

# Типы для уведомлений
NotificationType = Literal["info", "warning", "error", "success"]
Notification = Tuple[NotificationType, str, Optional[str]]

# Типы для тестирования
TestResult = Tuple[bool, str, Optional[Dict[str, Any]]]
TestSuite = List[Callable[[], TestResult]]
TestRunner = Callable[[TestSuite], List[TestResult]]
