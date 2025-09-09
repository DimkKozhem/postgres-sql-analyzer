#!/usr/bin/env python3
"""
Модуль валидации для PostgreSQL SQL Analyzer.
Содержит валидаторы для различных типов входных данных.
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Результат валидации."""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """Валидатор конфигурации."""

    @staticmethod
    def validate_memory_setting(value: int, min_val: int = 1, max_val: int = 1024) -> ValidationResult:
        """Валидирует настройки памяти."""
        errors = []
        warnings = []

        if not isinstance(value, int):
            errors.append(f"Значение должно быть целым числом, получено: {type(value)}")
        elif value < min_val:
            errors.append(f"Значение не может быть меньше {min_val}")
        elif value > max_val:
            warnings.append(f"Значение {value} больше рекомендуемого максимума {max_val}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_threshold(value: float, min_val: float = 0.0, max_val: float = float('inf')) -> ValidationResult:
        """Валидирует пороговые значения."""
        errors = []
        warnings = []

        if not isinstance(value, (int, float)):
            errors.append(f"Значение должно быть числом, получено: {type(value)}")
        elif value < min_val:
            errors.append(f"Значение не может быть меньше {min_val}")
        elif value > max_val:
            errors.append(f"Значение не может быть больше {max_val}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_dsn(dsn: str) -> ValidationResult:
        """Валидирует строку подключения к БД."""
        errors = []
        warnings = []

        if not dsn or not dsn.strip():
            errors.append("DSN не может быть пустым")
            return ValidationResult(is_valid=False, errors=errors)

        # Базовая проверка формата PostgreSQL DSN
        required_parts = ['host', 'dbname']
        dsn_lower = dsn.lower()

        for part in required_parts:
            if part not in dsn_lower:
                warnings.append(f"DSN может не содержать обязательный параметр: {part}")

        # Проверка на потенциально небезопасные параметры
        unsafe_patterns = ['password=', 'pwd=']
        for pattern in unsafe_patterns:
            if pattern in dsn_lower:
                warnings.append("DSN содержит пароль в открытом виде - используйте переменные окружения")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class SQLValidator:
    """Улучшенный валидатор SQL."""

    # Опасные SQL операции
    DANGEROUS_OPERATIONS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
        'TRUNCATE', 'GRANT', 'REVOKE', 'COPY'
    ]

    # Разрешенные операции
    ALLOWED_OPERATIONS = [
        'SELECT', 'WITH', 'EXPLAIN', 'ANALYZE'
    ]

    @staticmethod
    def validate_sql_safety(sql: str) -> ValidationResult:
        """Проверяет безопасность SQL запроса."""
        errors = []
        warnings = []

        if not sql or not sql.strip():
            errors.append("SQL запрос не может быть пустым")
            return ValidationResult(is_valid=False, errors=errors)

        # Нормализуем SQL для анализа
        sql_upper = sql.upper().strip()

        # Убираем комментарии
        sql_clean = re.sub(r'--.*$', '', sql_upper, flags=re.MULTILINE)
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)

        # Проверяем на опасные операции
        for operation in SQLValidator.DANGEROUS_OPERATIONS:
            if re.search(rf'\b{operation}\b', sql_clean):
                errors.append(f"Запрещенная операция: {operation}")

        # Проверяем структуру запроса
        if not any(re.search(rf'\b{op}\b', sql_clean) for op in SQLValidator.ALLOWED_OPERATIONS):
            warnings.append("Запрос не содержит явных разрешенных операций")

        # Проверяем на потенциально проблематические конструкции
        if 'UNION ALL' in sql_clean and sql_clean.count('UNION ALL') > 5:
            warnings.append("Большое количество UNION ALL может снизить производительность")

        if len(sql_clean) > 10000:
            warnings.append("Очень длинный запрос может быть сложен для анализа")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_sql_syntax(sql: str) -> ValidationResult:
        """Базовая проверка синтаксиса SQL."""
        errors = []
        warnings = []

        # Проверка на сбалансированность скобок
        paren_count = sql.count('(') - sql.count(')')
        if paren_count != 0:
            errors.append(f"Несбалансированные скобки (разница: {paren_count})")

        # Проверка на сбалансированность кавычек
        single_quotes = sql.count("'") - sql.count("\\'")
        if single_quotes % 2 != 0:
            errors.append("Несбалансированные одинарные кавычки")

        double_quotes = sql.count('"') - sql.count('\\"')
        if double_quotes % 2 != 0:
            errors.append("Несбалансированные двойные кавычки")

        # Проверка на пустые блоки
        if re.search(r'\(\s*\)', sql):
            warnings.append("Обнаружены пустые скобки")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class LLMConfigValidator:
    """Валидатор конфигурации LLM."""

    @staticmethod
    def validate_api_key(api_key: str, provider: str) -> ValidationResult:
        """Валидирует API ключ."""
        errors = []
        warnings = []

        if not api_key or not api_key.strip():
            errors.append(f"API ключ для {provider} не может быть пустым")
            return ValidationResult(is_valid=False, errors=errors)

        # Проверка формата ключей
        if provider.lower() == 'openai':
            if not api_key.startswith('sk-'):
                warnings.append("OpenAI API ключ обычно начинается с 'sk-'")
            if len(api_key) < 20:
                warnings.append("OpenAI API ключ кажется слишком коротким")

        elif provider.lower() == 'anthropic':
            if not api_key.startswith('sk-ant-'):
                warnings.append("Anthropic API ключ обычно начинается с 'sk-ant-'")

        # Общие проверки безопасности
        if api_key in ['test', 'demo', 'example', '123456']:
            errors.append("Используется тестовый или небезопасный API ключ")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_model_name(model: str, provider: str) -> ValidationResult:
        """Валидирует название модели."""
        errors = []
        warnings = []

        if not model or not model.strip():
            errors.append("Название модели не может быть пустым")
            return ValidationResult(is_valid=False, errors=errors)

        # Проверка известных моделей
        known_models = {
            'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-2.1', 'claude-2.0']
        }

        provider_lower = provider.lower()
        if provider_lower in known_models:
            if model not in known_models[provider_lower]:
                warnings.append(f"Неизвестная модель {model} для провайдера {provider}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_temperature(temperature: float) -> ValidationResult:
        """Валидирует температуру модели."""
        errors = []
        warnings = []

        if not isinstance(temperature, (int, float)):
            errors.append(f"Температура должна быть числом, получено: {type(temperature)}")
        elif temperature < 0.0:
            errors.append("Температура не может быть отрицательной")
        elif temperature > 2.0:
            errors.append("Температура не может быть больше 2.0")
        elif temperature > 1.0:
            warnings.append("Высокая температура (>1.0) может привести к непредсказуемым результатам")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class InputSanitizer:
    """Класс для санитизации входных данных."""

    @staticmethod
    def sanitize_sql(sql: str) -> str:
        """Базовая санитизация SQL."""
        if not sql:
            return ""

        # Убираем потенциально опасные символы в начале и конце
        sql = sql.strip()

        # Ограничиваем длину
        max_length = 50000  # 50KB
        if len(sql) > max_length:
            sql = sql[:max_length]

        return sql

    @staticmethod
    def sanitize_config_value(value: Any, expected_type: type) -> Any:
        """Санитизирует значение конфигурации."""
        if value is None:
            return None

        try:
            if expected_type == int:
                return int(float(value))  # Поддержка float -> int
            elif expected_type == float:
                return float(value)
            elif expected_type == str:
                return str(value).strip()
            elif expected_type == bool:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                else:
                    return bool(value)
            else:
                return value
        except (ValueError, TypeError):
            return None


def validate_config(config: Dict[str, Any]) -> ValidationResult:
    """Валидирует всю конфигурацию."""
    errors = []
    warnings = []

    # Валидация памяти
    for key in ['work_mem', 'shared_buffers']:
        if key in config:
            result = ConfigValidator.validate_memory_setting(config[key])
            errors.extend(result.errors)
            warnings.extend(result.warnings)

    # Валидация порогов
    for key in ['expensive_query_threshold', 'slow_query_threshold', 'ai_confidence_threshold']:
        if key in config:
            result = ConfigValidator.validate_threshold(config[key])
            errors.extend(result.errors)
            warnings.extend(result.warnings)

    # Валидация DSN
    if 'dsn' in config and config['dsn']:
        result = ConfigValidator.validate_dsn(config['dsn'])
        errors.extend(result.errors)
        warnings.extend(result.warnings)

    # Валидация LLM настроек
    if config.get('enable_ai_recommendations'):
        for provider in ['openai', 'anthropic']:
            api_key = config.get(f'{provider}_api_key')
            if api_key:
                result = LLMConfigValidator.validate_api_key(api_key, provider)
                errors.extend(result.errors)
                warnings.extend(result.warnings)

                model = config.get(f'{provider}_model')
                if model:
                    result = LLMConfigValidator.validate_model_name(model, provider)
                    errors.extend(result.errors)
                    warnings.extend(result.warnings)

        temperature = config.get('openai_temperature')
        if temperature is not None:
            result = LLMConfigValidator.validate_temperature(temperature)
            errors.extend(result.errors)
            warnings.extend(result.warnings)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
