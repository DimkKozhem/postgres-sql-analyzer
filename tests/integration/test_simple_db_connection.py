#!/usr/bin/env python3
"""Простой тест подключения к базе данных без SSH."""

import os
import sys
import logging
from pathlib import Path

# Добавляем путь к модулям приложения
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.analyzer import SQLAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Тестирует подключение к базе данных."""
    print("🗄️ Тестирование подключения к базе данных...")
    
    print(f"   БД хост: {settings.DB_HOST}")
    print(f"   БД порт: {settings.DB_PORT}")
    print(f"   БД имя: {settings.DB_NAME}")
    print(f"   БД пользователь: {settings.DB_USER}")
    print(f"   БД пароль: {'*' * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else 'НЕ ЗАДАН'}")
    
    try:
        import psycopg2
        
        conn_string = f"host={settings.DB_HOST} port={settings.DB_PORT} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}"
        print(f"   Строка подключения: {conn_string.replace(settings.DB_PASSWORD, '***') if settings.DB_PASSWORD else conn_string}")
        
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print(f"✅ Подключение к базе данных успешно!")
        print(f"   Версия PostgreSQL: {version[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def test_sql_analyzer():
    """Тестирует SQL анализатор."""
    print("\n🔍 Тестирование SQL анализатора...")
    
    try:
        # Создаем анализатор
        dsn = f"host={settings.DB_HOST} port={settings.DB_PORT} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}"
        analyzer = SQLAnalyzer(dsn)
        
        # Тестируем простой запрос
        test_sql = "SELECT 1 as test_column;"
        print(f"   Тестовый SQL: {test_sql}")
        
        result = analyzer.analyze_sql(test_sql)
        
        if result.is_valid:
            print("✅ SQL анализатор работает успешно!")
            print(f"   Время анализа: {result.analysis_time:.3f} сек")
            if result.metrics:
                print(f"   Ожидаемое время выполнения: {result.metrics.estimated_time_ms:.2f} мс")
                print(f"   Ожидаемое количество строк: {result.metrics.estimated_rows}")
            return True
        else:
            print("❌ Ошибка анализа SQL")
            for error in result.validation_errors:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка SQL анализатора: {e}")
        return False


def main():
    """Основная функция тестирования."""
    print("🐘 PostgreSQL SQL Analyzer - Простой тест подключения")
    print("=" * 60)
    
    # Проверяем наличие .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ Файл .env не найден")
        print("   Скопируйте env_template.txt в .env и настройте переменные")
        return False
    
    print(f"📁 Используется файл конфигурации: {env_file.absolute()}")
    
    # Тестируем компоненты
    tests = [
        ("Подключение к БД", test_database_connection),
        ("SQL анализатор", test_sql_analyzer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        print("   Приложение готово к работе")
    else:
        print("⚠️ Некоторые тесты не пройдены")
        print("   Проверьте настройки и попробуйте снова")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
