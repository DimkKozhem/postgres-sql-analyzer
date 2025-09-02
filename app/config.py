"""Конфигурация приложения PostgreSQL SQL Analyzer."""

from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Параметры PostgreSQL
    DEFAULT_WORK_MEM: int = 4  # MB
    DEFAULT_SHARED_BUFFERS: int = 128  # MB
    DEFAULT_EFFECTIVE_CACHE_SIZE: int = 4  # GB
    
    # Пороги для анализа
    LARGE_TABLE_THRESHOLD: int = 1000000  # строк
    EXPENSIVE_QUERY_THRESHOLD: float = 1000.0  # cost
    SLOW_QUERY_THRESHOLD: float = 100.0  # ms
    
    # Настройки анализа
    MAX_EXPLAIN_DEPTH: int = 10
    ENABLE_PG_STAT_STATEMENTS: bool = True
    
    # Mock режим
    MOCK_MODE: bool = False
    
    # LLM настройки
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-sonnet"
    
    LOCAL_LLM_URL: str = ""
    LOCAL_LLM_MODEL: str = "llama2"
    
    # Настройки AI-рекомендаций
    ENABLE_AI_RECOMMENDATIONS: bool = False
    AI_PROVIDER: str = "auto"  # auto, openai, anthropic, local
    AI_CONFIDENCE_THRESHOLD: float = 0.7
    
    model_config = {"env_prefix": "SQL_ANALYZER_"}


# Глобальный экземпляр настроек
settings = Settings()


def get_default_config() -> Dict[str, Any]:
    """Возвращает конфигурацию по умолчанию."""
    return {
        "work_mem": settings.DEFAULT_WORK_MEM,
        "shared_buffers": settings.DEFAULT_SHARED_BUFFERS,
        "effective_cache_size": settings.DEFAULT_EFFECTIVE_CACHE_SIZE,
        "large_table_threshold": settings.LARGE_TABLE_THRESHOLD,
        "expensive_query_threshold": settings.EXPENSIVE_QUERY_THRESHOLD,
        "slow_query_threshold": settings.SLOW_QUERY_THRESHOLD,
        "enable_ai_recommendations": settings.ENABLE_AI_RECOMMENDATIONS,
        "ai_provider": settings.AI_PROVIDER,
        "ai_confidence_threshold": settings.AI_CONFIDENCE_THRESHOLD,
        "openai_api_key": settings.OPENAI_API_KEY,
        "openai_model": settings.OPENAI_MODEL,
        "openai_temperature": settings.OPENAI_TEMPERATURE,
        "anthropic_api_key": settings.ANTHROPIC_API_KEY,
        "anthropic_model": settings.ANTHROPIC_MODEL,
        "local_llm_url": settings.LOCAL_LLM_URL,
        "local_llm_model": settings.LOCAL_LLM_MODEL,
    }
