#!/usr/bin/env python3
"""Тесты для модуля exceptions."""

import pytest
from app.exceptions import (
    SQLAnalyzerError, ValidationError, DatabaseConnectionError,
    SQLExecutionError, LLMIntegrationError, ConfigurationError,
    handle_database_error, handle_sql_error, handle_llm_error,
    safe_execute, ErrorContext
)


class TestSQLAnalyzerError:
    """Тесты для базового исключения SQLAnalyzerError."""
    
    def test_creation_basic(self):
        """Тест создания базового исключения."""
        error = SQLAnalyzerError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
    
    def test_creation_with_details(self):
        """Тест создания исключения с деталями."""
        details = {"key": "value"}
        error = SQLAnalyzerError("Test error", details)
        assert error.details == details
    
    def test_to_dict(self):
        """Тест преобразования в словарь."""
        error = SQLAnalyzerError("Test error", {"key": "value"})
        result = error.to_dict()
        
        assert result["error_type"] == "SQLAnalyzerError"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}


class TestValidationError:
    """Тесты для ValidationError."""
    
    def test_creation(self):
        """Тест создания ValidationError."""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        
        error = ValidationError("Validation failed", errors, warnings)
        
        assert error.validation_errors == errors
        assert error.warnings == warnings
        assert error.details["validation_errors"] == errors
        assert error.details["warnings"] == warnings


class TestDatabaseConnectionError:
    """Тесты для DatabaseConnectionError."""
    
    def test_creation_basic(self):
        """Тест создания базовой ошибки подключения."""
        error = DatabaseConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.dsn is None
        assert error.original_error is None
    
    def test_creation_with_dsn(self):
        """Тест создания ошибки с DSN."""
        dsn = "postgresql://localhost/test"
        error = DatabaseConnectionError("Connection failed", dsn)
        
        assert error.dsn == dsn
        assert error.details["dsn_provided"] is True
    
    def test_creation_with_original_error(self):
        """Тест создания ошибки с исходным исключением."""
        original = Exception("Original error")
        error = DatabaseConnectionError("Connection failed", original_error=original)
        
        assert error.original_error == original
        assert error.details["original_error"] == "Original error"


class TestSQLExecutionError:
    """Тесты для SQLExecutionError."""
    
    def test_creation_with_sql(self):
        """Тест создания ошибки с SQL."""
        sql = "SELECT * FROM users;"
        error = SQLExecutionError("SQL failed", sql)
        
        assert error.sql == sql
        assert error.details["sql_length"] == len(sql)


class TestLLMIntegrationError:
    """Тесты для LLMIntegrationError."""
    
    def test_creation_with_provider(self):
        """Тест создания ошибки с провайдером."""
        error = LLMIntegrationError("LLM failed", "openai")
        
        assert error.provider == "openai"
        assert error.details["provider"] == "openai"


class TestConfigurationError:
    """Тесты для ConfigurationError."""
    
    def test_creation_with_config_key(self):
        """Тест создания ошибки с ключом конфигурации."""
        error = ConfigurationError("Invalid config", "work_mem", 64)
        
        assert error.config_key == "work_mem"
        assert error.invalid_value == 64
        assert error.details["config_key"] == "work_mem"
        assert error.details["invalid_value"] == "64"
        assert error.details["value_type"] == "int"


class TestErrorHandlers:
    """Тесты для обработчиков ошибок."""
    
    def test_handle_database_error_connection_refused(self):
        """Тест обработки ошибки 'connection refused'."""
        original = Exception("connection refused")
        result = handle_database_error(original)
        
        assert isinstance(result, DatabaseConnectionError)
        assert "подключиться" in result.message.lower()
    
    def test_handle_database_error_authentication(self):
        """Тест обработки ошибки аутентификации."""
        original = Exception("authentication failed")
        result = handle_database_error(original)
        
        assert isinstance(result, DatabaseConnectionError)
        assert "аутентификац" in result.message.lower()
    
    def test_handle_sql_error_syntax(self):
        """Тест обработки синтаксической ошибки SQL."""
        original = Exception("syntax error")
        result = handle_sql_error(original)
        
        assert isinstance(result, SQLExecutionError)
        assert "синтаксическая" in result.message.lower()
    
    def test_handle_llm_error_api_key(self):
        """Тест обработки ошибки API ключа."""
        original = Exception("api key invalid")
        result = handle_llm_error(original, "openai")
        
        assert isinstance(result, LLMIntegrationError)
        assert "api ключа" in result.message.lower()
        assert result.provider == "openai"


class TestSafeExecute:
    """Тесты для safe_execute."""
    
    def test_safe_execute_success(self):
        """Тест успешного выполнения."""
        def test_func(x):
            return x * 2
        
        result = safe_execute(test_func, 5)
        assert result == 10
    
    def test_safe_execute_with_exception(self):
        """Тест выполнения с исключением."""
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            safe_execute(test_func)
    
    def test_safe_execute_with_error_handler(self):
        """Тест выполнения с обработчиком ошибок."""
        def test_func():
            raise ValueError("Test error")
        
        def error_handler(e):
            return f"Handled: {str(e)}"
        
        result = safe_execute(test_func, error_handler=error_handler)
        assert result == "Handled: Test error"
    
    def test_safe_execute_with_default_return(self):
        """Тест выполнения с возвратом по умолчанию."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, default_return="default")
        assert result == "default"


class TestErrorContext:
    """Тесты для ErrorContext."""
    
    def test_creation(self):
        """Тест создания контекста ошибок."""
        ctx = ErrorContext("test_operation", param1="value1")
        
        assert ctx.operation == "test_operation"
        assert ctx.context_data == {"param1": "value1"}
        assert ctx.errors == []
        assert ctx.warnings == []
    
    def test_add_error(self):
        """Тест добавления ошибки."""
        ctx = ErrorContext("test")
        ctx.add_error("Test error")
        
        assert ctx.errors == ["Test error"]
        assert ctx.has_errors() is True
    
    def test_add_warning(self):
        """Тест добавления предупреждения."""
        ctx = ErrorContext("test")
        ctx.add_warning("Test warning")
        
        assert ctx.warnings == ["Test warning"]
        assert ctx.has_warnings() is True
    
    def test_to_dict(self):
        """Тест преобразования в словарь."""
        ctx = ErrorContext("test", param="value")
        ctx.add_error("error")
        ctx.add_warning("warning")
        
        result = ctx.to_dict()
        
        assert result["operation"] == "test"
        assert result["context_data"] == {"param": "value"}
        assert result["errors"] == ["error"]
        assert result["warnings"] == ["warning"]
    
    def test_context_manager_success(self):
        """Тест успешного использования как контекстный менеджер."""
        with ErrorContext("test") as ctx:
            ctx.add_warning("test warning")
        
        assert ctx.warnings == ["test warning"]
    
    def test_context_manager_with_exception(self):
        """Тест использования с исключением."""
        with pytest.raises(SQLAnalyzerError):
            with ErrorContext("test"):
                raise ValueError("test error")
    
    def test_context_manager_with_sql_analyzer_error(self):
        """Тест использования с SQLAnalyzerError (не преобразуется)."""
        original_error = SQLAnalyzerError("original")
        
        with pytest.raises(SQLAnalyzerError) as exc_info:
            with ErrorContext("test"):
                raise original_error
        
        assert exc_info.value == original_error
