#!/usr/bin/env python3
"""
Кастомные исключения для PostgreSQL SQL Analyzer.
Определяет специализированные исключения для различных типов ошибок.
"""

from typing import Optional, Dict, Any, List


class SQLAnalyzerError(Exception):
    """Базовое исключение для SQL Analyzer."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует исключение в словарь."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


class ValidationError(SQLAnalyzerError):
    """Исключение валидации входных данных."""

    def __init__(self, message: str, validation_errors: List[str], warnings: Optional[List[str]] = None):
        super().__init__(message)
        self.validation_errors = validation_errors
        self.warnings = warnings or []
        self.details = {
            'validation_errors': validation_errors,
            'warnings': self.warnings
        }


class DatabaseConnectionError(SQLAnalyzerError):
    """Исключение подключения к базе данных."""

    def __init__(self, message: str, dsn: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.dsn = dsn
        self.original_error = original_error
        self.details = {
            'dsn_provided': dsn is not None,
            'original_error': str(original_error) if original_error else None
        }


class SQLExecutionError(SQLAnalyzerError):
    """Исключение выполнения SQL запроса."""

    def __init__(self, message: str, sql: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.sql = sql
        self.original_error = original_error
        self.details = {
            'sql_length': len(sql) if sql else 0,
            'original_error': str(original_error) if original_error else None
        }


class PlanParsingError(SQLAnalyzerError):
    """Исключение парсинга плана выполнения."""

    def __init__(self, message: str, plan_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.plan_data = plan_data
        self.details = {
            'plan_provided': plan_data is not None,
            'plan_keys': list(plan_data.keys()) if plan_data else []
        }


class LLMIntegrationError(SQLAnalyzerError):
    """Исключение интеграции с LLM."""

    def __init__(self, message: str, provider: Optional[str] = None,
                 api_error: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.api_error = api_error
        self.details = {
            'provider': provider,
            'api_error': str(api_error) if api_error else None
        }


class ConfigurationError(SQLAnalyzerError):
    """Исключение конфигурации."""

    def __init__(self, message: str, config_key: Optional[str] = None,
                 invalid_value: Optional[Any] = None):
        super().__init__(message)
        self.config_key = config_key
        self.invalid_value = invalid_value
        self.details = {
            'config_key': config_key,
            'invalid_value': str(invalid_value) if invalid_value is not None else None,
            'value_type': type(invalid_value).__name__ if invalid_value is not None else None
        }


class HealthCheckError(SQLAnalyzerError):
    """Исключение проверки здоровья системы."""

    def __init__(self, message: str, component: Optional[str] = None,
                 check_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.component = component
        self.check_details = check_details or {}
        self.details = {
            'component': component,
            'check_details': self.check_details
        }


class BackupError(SQLAnalyzerError):
    """Исключение операций резервного копирования."""

    def __init__(self, message: str, operation: Optional[str] = None,
                 backup_path: Optional[str] = None):
        super().__init__(message)
        self.operation = operation
        self.backup_path = backup_path
        self.details = {
            'operation': operation,
            'backup_path': backup_path
        }


class MetricsError(SQLAnalyzerError):
    """Исключение сбора метрик."""

    def __init__(self, message: str, metric_name: Optional[str] = None):
        super().__init__(message)
        self.metric_name = metric_name
        self.details = {
            'metric_name': metric_name
        }


# Утилиты для обработки исключений

def handle_database_error(error: Exception, dsn: Optional[str] = None) -> DatabaseConnectionError:
    """Обрабатывает ошибки базы данных."""
    error_message = str(error)

    # Определяем тип ошибки по сообщению
    if "connection refused" in error_message.lower():
        message = "Не удалось подключиться к базе данных. Проверьте, что PostgreSQL запущен и доступен."
    elif "authentication failed" in error_message.lower():
        message = "Ошибка аутентификации. Проверьте учетные данные."
    elif "database" in error_message.lower() and "does not exist" in error_message.lower():
        message = "Указанная база данных не существует."
    elif "timeout" in error_message.lower():
        message = "Превышено время ожидания подключения к базе данных."
    else:
        message = f"Ошибка подключения к базе данных: {error_message}"

    return DatabaseConnectionError(message, dsn, error)


def handle_sql_error(error: Exception, sql: Optional[str] = None) -> SQLExecutionError:
    """Обрабатывает ошибки выполнения SQL."""
    error_message = str(error)

    # Определяем тип ошибки SQL
    if "syntax error" in error_message.lower():
        message = "Синтаксическая ошибка в SQL запросе."
    elif "relation" in error_message.lower() and "does not exist" in error_message.lower():
        message = "Указанная таблица или представление не существует."
    elif "column" in error_message.lower() and "does not exist" in error_message.lower():
        message = "Указанный столбец не существует."
    elif "permission denied" in error_message.lower():
        message = "Недостаточно прав для выполнения запроса."
    else:
        message = f"Ошибка выполнения SQL: {error_message}"

    return SQLExecutionError(message, sql, error)


def handle_llm_error(error: Exception, provider: Optional[str] = None) -> LLMIntegrationError:
    """Обрабатывает ошибки LLM."""
    error_message = str(error)

    if "api key" in error_message.lower():
        message = f"Ошибка API ключа для {provider or 'LLM'}. Проверьте правильность ключа."
    elif "rate limit" in error_message.lower():
        message = f"Превышен лимит запросов к {provider or 'LLM'}. Попробуйте позже."
    elif "quota" in error_message.lower():
        message = f"Исчерпана квота для {provider or 'LLM'}."
    elif "timeout" in error_message.lower():
        message = f"Превышено время ожидания ответа от {provider or 'LLM'}."
    else:
        message = f"Ошибка интеграции с {provider or 'LLM'}: {error_message}"

    return LLMIntegrationError(message, provider, error)


def safe_execute(func, *args, error_handler=None, default_return=None, **kwargs):
    """Безопасное выполнение функции с обработкой ошибок."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            return error_handler(e)
        elif default_return is not None:
            return default_return
        else:
            raise


class ErrorContext:
    """Контекст для отслеживания ошибок."""

    def __init__(self, operation: str, **context_data):
        self.operation = operation
        self.context_data = context_data
        self.errors = []
        self.warnings = []

    def add_error(self, error: str):
        """Добавляет ошибку в контекст."""
        self.errors.append(error)

    def add_warning(self, warning: str):
        """Добавляет предупреждение в контекст."""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Проверяет наличие ошибок."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Проверяет наличие предупреждений."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует контекст в словарь."""
        return {
            'operation': self.operation,
            'context_data': self.context_data,
            'errors': self.errors,
            'warnings': self.warnings
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not isinstance(exc_val, SQLAnalyzerError):
            # Преобразуем обычные исключения в наши кастомные
            if 'database' in str(exc_val).lower() or 'connection' in str(exc_val).lower():
                raise handle_database_error(exc_val)
            elif 'sql' in str(exc_val).lower():
                raise handle_sql_error(exc_val)
            else:
                raise SQLAnalyzerError(f"Ошибка в операции '{self.operation}': {str(exc_val)}")
        return False  # Не подавляем исключения
