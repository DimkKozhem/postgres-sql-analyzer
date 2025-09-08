#!/usr/bin/env python3
"""
Конфигурация для продакшена на сервере MoreTech_LCT
"""

import os
from app.config import Settings

class ProductionSettings(Settings):
    """Настройки для продакшена."""
    
    # Настройки сервера
    SERVER_HOST: str = "0.0.0.0"  # Слушать все интерфейсы
    SERVER_PORT: int = 8505
    SERVER_HEADLESS: bool = True
    
    # Безопасность
    
    # LLM настройки (настройте свои API ключи)
    ENABLE_AI_RECOMMENDATIONS: bool = True
    AI_PROVIDER: str = "openai"  # или "anthropic", "local"
    
    # OpenAI (замените на свои ключи)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    
    # Anthropic (замените на свои ключи)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = "claude-3-sonnet"
    
    # Локальные модели
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama2")
    
    # Пороги для анализа
    LARGE_TABLE_THRESHOLD: int = 1000000
    EXPENSIVE_QUERY_THRESHOLD: float = 1000.0
    SLOW_QUERY_THRESHOLD: float = 100.0
    
    # PostgreSQL настройки по умолчанию
    DEFAULT_WORK_MEM: int = 64  # MB (увеличено для продакшена)
    DEFAULT_SHARED_BUFFERS: int = 512  # MB
    DEFAULT_EFFECTIVE_CACHE_SIZE: int = 8  # GB
    
    model_config = {"env_prefix": "SQL_ANALYZER_"}

# Глобальный экземпляр настроек для продакшена
production_settings = ProductionSettings()

def get_production_config():
    """Возвращает конфигурацию для продакшена."""
    return {
        "server_host": production_settings.SERVER_HOST,
        "server_port": production_settings.SERVER_PORT,
        "server_headless": production_settings.SERVER_HEADLESS,
        "enable_ai_recommendations": production_settings.ENABLE_AI_RECOMMENDATIONS,
        "ai_provider": production_settings.AI_PROVIDER,
        "openai_api_key": production_settings.OPENAI_API_KEY,
        "openai_model": production_settings.OPENAI_MODEL,
        "openai_temperature": production_settings.OPENAI_TEMPERATURE,
        "anthropic_api_key": production_settings.ANTHROPIC_API_KEY,
        "anthropic_model": production_settings.ANTHROPIC_MODEL,
        "local_llm_url": production_settings.LOCAL_LLM_URL,
        "local_llm_model": production_settings.LOCAL_LLM_MODEL,
        "large_table_threshold": production_settings.LARGE_TABLE_THRESHOLD,
        "expensive_query_threshold": production_settings.EXPENSIVE_QUERY_THRESHOLD,
        "slow_query_threshold": production_settings.SLOW_QUERY_THRESHOLD,
        "work_mem": production_settings.DEFAULT_WORK_MEM,
        "shared_buffers": production_settings.DEFAULT_SHARED_BUFFERS,
        "effective_cache_size": production_settings.DEFAULT_EFFECTIVE_CACHE_SIZE,
    }

if __name__ == "__main__":
    print("🚀 Конфигурация для продакшена PostgreSQL SQL Analyzer")
    print("=" * 60)
    
    config = get_production_config()
    for key, value in config.items():
        if "key" in key.lower() and value:
            print(f"{key}: {'*' * len(value)}")
        else:
            print(f"{key}: {value}")
    
    print("\n🌐 Приложение будет доступно по адресу:")
    print(f"   http://{config['server_host']}:{config['server_port']}")
    
    print("\n🔧 Для настройки API ключей используйте переменные окружения:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   export ANTHROPIC_API_KEY='your-key-here'")
    print("   export LOCAL_LLM_URL='http://localhost:11434'")
