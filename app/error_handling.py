"""Модуль для централизованной обработки ошибок."""

import logging
import streamlit as st
from typing import Any, Callable, Optional
from functools import wraps
from psycopg2 import OperationalError, DatabaseError, ProgrammingError

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Ошибка подключения к базе данных."""


class SQLExecutionError(Exception):
    """Ошибка выполнения SQL запроса."""


class ConfigurationError(Exception):
    """Ошибка конфигурации."""


def handle_database_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок базы данных."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as e:
            error_msg = f"Ошибка подключения к БД: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            raise DatabaseConnectionError(error_msg) from e
        except DatabaseError as e:
            error_msg = f"Ошибка базы данных: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            raise SQLExecutionError(error_msg) from e
        except ProgrammingError as e:
            error_msg = f"Ошибка SQL запроса: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            raise SQLExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(f"❌ {error_msg}")
            raise
    return wrapper


def handle_streamlit_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок Streamlit."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Ошибка в интерфейсе: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(f"❌ {error_msg}")
            st.exception(e)
            return None
    return wrapper


def safe_execute(
    func: Callable,
    *args,
    error_message: str = "Произошла ошибка",
    show_error: bool = True,
    log_error: bool = True,
    **kwargs
) -> Optional[Any]:
    """Безопасное выполнение функции с обработкой ошибок."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {str(e)}", exc_info=True)
        if show_error:
            st.error(f"❌ {error_message}: {str(e)}")
        return None


def validate_database_connection(dsn: str) -> tuple[bool, str]:
    """Валидация подключения к базе данных."""
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        conn.close()
        return True, "✅ Подключение успешно"
    except OperationalError as e:
        return False, f"❌ Ошибка подключения: {str(e)}"
    except Exception as e:
        return False, f"❌ Неожиданная ошибка: {str(e)}"


def validate_sql_query(query: str) -> tuple[bool, str]:
    """Валидация SQL запроса."""
    if not query or not query.strip():
        return False, "❌ Запрос не может быть пустым"

    # Базовая проверка на опасные операции
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
            return False, f"❌ Запрос содержит опасную операцию: {keyword}"

    return True, "✅ Запрос валиден"


def log_and_display_error(
    error: Exception,
    context: str = "",
    show_to_user: bool = True,
    log_level: int = logging.ERROR
) -> None:
    """Логирование и отображение ошибки."""
    error_msg = f"{context}: {str(error)}" if context else str(error)

    # Логирование
    logger.log(log_level, error_msg, exc_info=True)

    # Отображение пользователю
    if show_to_user:
        st.error(f"❌ {error_msg}")


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Декоратор для повторных попыток при ошибках."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Попытка {
                                attempt +
                                1} неудачна: {
                                str(e)}. Повтор через {delay}с...")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"Все {max_retries} попыток неудачны")

            raise last_exception
        return wrapper
    return decorator


class ErrorHandler:
    """Класс для централизованной обработки ошибок."""

    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)

    def handle_database_error(
            self,
            error: Exception,
            context: str = "") -> None:
        """Обработка ошибок базы данных."""
        if isinstance(error, OperationalError):
            self.logger.error(
                f"Ошибка подключения к БД {context}: {
                    str(error)}")
            st.error(f"❌ Ошибка подключения к базе данных: {str(error)}")
        elif isinstance(error, DatabaseError):
            self.logger.error(f"Ошибка БД {context}: {str(error)}")
            st.error(f"❌ Ошибка базы данных: {str(error)}")
        elif isinstance(error, ProgrammingError):
            self.logger.error(f"Ошибка SQL {context}: {str(error)}")
            st.error(f"❌ Ошибка SQL запроса: {str(error)}")
        else:
            self.logger.error(
                f"Неожиданная ошибка БД {context}: {
                    str(error)}", exc_info=True)
            st.error(f"❌ Неожиданная ошибка: {str(error)}")

    def handle_streamlit_error(
            self,
            error: Exception,
            context: str = "") -> None:
        """Обработка ошибок Streamlit."""
        self.logger.error(
            f"Ошибка Streamlit {context}: {
                str(error)}", exc_info=True)
        st.error(f"❌ Ошибка интерфейса: {str(error)}")
        st.exception(error)

    def handle_general_error(
            self,
            error: Exception,
            context: str = "") -> None:
        """Обработка общих ошибок."""
        self.logger.error(
            f"Общая ошибка {context}: {
                str(error)}", exc_info=True)
        st.error(f"❌ Ошибка: {str(error)}")


# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()
