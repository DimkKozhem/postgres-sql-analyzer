#!/usr/bin/env python3
"""
Конфигурация логирования для PostgreSQL SQL Analyzer.
Настраивает структурированное логирование с различными уровнями и форматами.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Форматтер для JSON логов."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'sql'):
            log_entry['sql'] = record.sql
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консольного вывода."""
    
    # ANSI цветовые коды
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Форматируем сообщение
        formatted = super().format(record)
        
        return formatted


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False,
    log_dir: str = "logs"
) -> None:
    """
    Настраивает логирование для приложения.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Логировать в файл
        log_to_console: Логировать в консоль
        json_format: Использовать JSON формат для файлов
        log_dir: Директория для лог файлов
    """
    
    # Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Базовая конфигурация
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
            'colored': {
                '()': ColoredFormatter,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'json': {
                '()': JSONFormatter
            }
        },
        'handlers': {},
        'loggers': {
            'app': {
                'level': level,
                'handlers': [],
                'propagate': False
            },
            'app.analyzer': {
                'level': level,
                'handlers': [],
                'propagate': True
            },
            'app.database': {
                'level': level,
                'handlers': [],
                'propagate': True
            },
            'app.llm_integration': {
                'level': level,
                'handlers': [],
                'propagate': True
            },
            'app.health': {
                'level': level,
                'handlers': [],
                'propagate': True
            },
            'app.metrics': {
                'level': level,
                'handlers': [],
                'propagate': True
            },
            'app.backup': {
                'level': level,
                'handlers': [],
                'propagate': True
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': []
        }
    }
    
    # Настраиваем консольный хэндлер
    if log_to_console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'colored',
            'level': level
        }
        config['loggers']['app']['handlers'].append('console')
        config['root']['handlers'].append('console')
    
    # Настраиваем файловые хэндлеры
    if log_to_file:
        # Основной лог файл
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(log_path / 'sql_analyzer.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json' if json_format else 'detailed',
            'level': level,
            'encoding': 'utf-8'
        }
        config['loggers']['app']['handlers'].append('file')
        
        # Лог файл для ошибок
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(log_path / 'errors.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 3,
            'formatter': 'json' if json_format else 'detailed',
            'level': 'ERROR',
            'encoding': 'utf-8'
        }
        config['loggers']['app']['handlers'].append('error_file')
        config['root']['handlers'].append('error_file')
        
        # Лог файл для SQL запросов
        config['handlers']['sql_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(log_path / 'sql_queries.log'),
            'maxBytes': 20 * 1024 * 1024,  # 20MB
            'backupCount': 10,
            'formatter': 'json' if json_format else 'detailed',
            'level': 'DEBUG',
            'encoding': 'utf-8'
        }
        
        # Отдельный логгер для SQL
        config['loggers']['app.sql'] = {
            'level': 'DEBUG',
            'handlers': ['sql_file'],
            'propagate': False
        }
        
        # Лог файл для метрик
        config['handlers']['metrics_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(log_path / 'metrics.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json',  # Метрики всегда в JSON
            'level': 'INFO',
            'encoding': 'utf-8'
        }
        
        config['loggers']['app.metrics']['handlers'] = ['metrics_file']
    
    # Применяем конфигурацию
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Получает настроенный логгер.
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


def log_sql_query(logger: logging.Logger, sql: str, execution_time: float = None, 
                  success: bool = True, error: str = None, **kwargs):
    """
    Логирует SQL запрос со специальными атрибутами.
    
    Args:
        logger: Логгер
        sql: SQL запрос
        execution_time: Время выполнения в секундах
        success: Успешность выполнения
        error: Текст ошибки если есть
        **kwargs: Дополнительные атрибуты
    """
    # Создаем специальный SQL логгер если его нет
    sql_logger = logging.getLogger('app.sql')
    
    # Подготавливаем дополнительные атрибуты
    extra_attrs = {
        'sql': sql[:1000] + '...' if len(sql) > 1000 else sql,  # Обрезаем длинные запросы
        'sql_length': len(sql),
        'success': success,
        **kwargs
    }
    
    if execution_time is not None:
        extra_attrs['execution_time'] = execution_time
    
    if error:
        extra_attrs['error'] = error
    
    # Логируем
    if success:
        if execution_time and execution_time > 1.0:  # Медленный запрос
            sql_logger.warning("Медленный SQL запрос", extra=extra_attrs)
        else:
            sql_logger.info("SQL запрос выполнен", extra=extra_attrs)
    else:
        sql_logger.error("Ошибка выполнения SQL запроса", extra=extra_attrs)


def log_llm_request(logger: logging.Logger, provider: str, operation: str, 
                   response_time: float = None, success: bool = True, 
                   error: str = None, **kwargs):
    """
    Логирует запрос к LLM.
    
    Args:
        logger: Логгер
        provider: Провайдер LLM
        operation: Тип операции
        response_time: Время ответа
        success: Успешность
        error: Ошибка если есть
        **kwargs: Дополнительные атрибуты
    """
    extra_attrs = {
        'llm_provider': provider,
        'llm_operation': operation,
        'success': success,
        **kwargs
    }
    
    if response_time is not None:
        extra_attrs['response_time'] = response_time
    
    if error:
        extra_attrs['error'] = error
    
    if success:
        logger.info(f"LLM запрос к {provider} выполнен", extra=extra_attrs)
    else:
        logger.error(f"Ошибка LLM запроса к {provider}", extra=extra_attrs)


def log_performance_metric(logger: logging.Logger, metric_name: str, 
                          value: float, **kwargs):
    """
    Логирует метрику производительности.
    
    Args:
        logger: Логгер
        metric_name: Название метрики
        value: Значение метрики
        **kwargs: Дополнительные атрибуты
    """
    metrics_logger = logging.getLogger('app.metrics')
    
    extra_attrs = {
        'metric_name': metric_name,
        'metric_value': value,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    metrics_logger.info(f"Метрика: {metric_name} = {value}", extra=extra_attrs)


# Инициализация логирования по умолчанию
def init_default_logging():
    """Инициализирует логирование с настройками по умолчанию."""
    setup_logging(
        level="INFO",
        log_to_file=True,
        log_to_console=True,
        json_format=False
    )


# Контекстный менеджер для логирования операций
class LoggingContext:
    """Контекстный менеджер для логирования операций."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Начало операции: {self.operation}", extra=self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        context_with_duration = {
            **self.context,
            'duration': duration
        }
        
        if exc_type is None:
            self.logger.info(f"Операция завершена: {self.operation}", extra=context_with_duration)
        else:
            context_with_duration['error'] = str(exc_val)
            self.logger.error(f"Операция завершена с ошибкой: {self.operation}", extra=context_with_duration)
        
        return False  # Не подавляем исключения
