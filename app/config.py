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
    
    # Настройки базы данных
    DB_HOST: str = "localhost"
    DB_PORT: int = 5435
    DB_NAME: str = "postgres"
    DB_USER: str = "readonly_user"
    DB_PASSWORD: str = "skripka_user"
    
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
    
    # Настройки прокси для OpenAI
    ENABLE_PROXY: bool = True
    PROXY_HOST: str = "localhost"
    PROXY_PORT: int = 1080
    
    # SSH настройки для туннелирования
    SSH_HOST: str = "193.246.150.18"
    SSH_PORT: int = 22
    SSH_USER: str = "skripka"
    SSH_KEY_PATH: str = "~/.ssh/id_rsa"
    AUTO_CREATE_SSH_TUNNEL: bool = False
    SSH_TIMEOUT: int = 30
    CHECK_DB_CONNECTION_ON_START: bool = True
    
    # Дополнительные пользователи для отладки
    DB_SUPER_USER: str = "postgres"
    DB_SUPER_PASSWORD: str = "skripka_super"
    DB_ADMIN_USER: str = "admin_user"
    DB_ADMIN_PASSWORD: str = "skripka_admin"
    
    # Brave API
    BRAVE_API_KEY: str = ""
    
    model_config = {
        "env_prefix": "SQL_ANALYZER_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }


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
        "enable_proxy": settings.ENABLE_PROXY,
        "proxy_host": settings.PROXY_HOST,
        "proxy_port": settings.PROXY_PORT,
        "db_host": settings.DB_HOST,
        "db_port": settings.DB_PORT,
        "db_name": settings.DB_NAME,
        "db_user": settings.DB_USER,
        "db_password": settings.DB_PASSWORD,
        "db_super_user": settings.DB_SUPER_USER,
        "db_super_password": settings.DB_SUPER_PASSWORD,
        "db_admin_user": settings.DB_ADMIN_USER,
        "db_admin_password": settings.DB_ADMIN_PASSWORD,
        "ssh_host": settings.SSH_HOST,
        "ssh_port": settings.SSH_PORT,
        "ssh_user": settings.SSH_USER,
        "ssh_key_path": settings.SSH_KEY_PATH,
        "auto_create_ssh_tunnel": settings.AUTO_CREATE_SSH_TUNNEL,
        "ssh_timeout": settings.SSH_TIMEOUT,
        "check_db_connection_on_start": settings.CHECK_DB_CONNECTION_ON_START,
        "brave_api_key": settings.BRAVE_API_KEY,
        "mock_mode": settings.MOCK_MODE,
    }
