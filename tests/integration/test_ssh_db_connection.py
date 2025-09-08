#!/usr/bin/env python3
"""Скрипт для тестирования подключения к БД через SSH туннель."""

import os
import sys
import logging
from pathlib import Path

# Добавляем путь к модулям приложения
sys.path.insert(0, str(Path(__file__).parent))

from app.ssh_tunnel import test_ssh_connection, test_db_connection, ssh_tunnel_context
from app.config import settings
from app.analyzer import SQLAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ssh_tunnel():
    """Тестирует SSH туннель."""
    print("🔐 Тестирование SSH подключения...")
    
    if not settings.SSH_HOST or not settings.SSH_USER:
        print("❌ SSH настройки не заданы")
        print("   Установите переменные окружения:")
        print("   - SQL_ANALYZER_SSH_HOST")
        print("   - SQL_ANALYZER_SSH_USER")
        print("   - SQL_ANALYZER_SSH_KEY_PATH")
        return False
    
    print(f"   SSH хост: {settings.SSH_HOST}")
    print(f"   SSH пользователь: {settings.SSH_USER}")
    print(f"   SSH ключ: {settings.SSH_KEY_PATH}")
    
    if test_ssh_connection():
        print("✅ SSH подключение успешно!")
        return True
    else:
        print("❌ Ошибка SSH подключения")
        return False


def test_database_connection():
    """Тестирует подключение к базе данных."""
    print("\n🗄️ Тестирование подключения к базе данных...")
    
    if not settings.DB_HOST or not settings.DB_NAME or not settings.DB_USER:
        print("❌ Настройки базы данных не заданы")
        print("   Установите переменные окружения:")
        print("   - SQL_ANALYZER_DB_HOST")
        print("   - SQL_ANALYZER_DB_NAME")
        print("   - SQL_ANALYZER_DB_USER")
        print("   - SQL_ANALYZER_DB_PASSWORD")
        return False
    
    print(f"   БД хост: {settings.DB_HOST}")
    print(f"   БД порт: {settings.DB_PORT}")
    print(f"   БД имя: {settings.DB_NAME}")
    print(f"   БД пользователь: {settings.DB_USER}")
    
    if test_db_connection():
        print("✅ Подключение к базе данных успешно!")
        return True
    else:
        print("❌ Ошибка подключения к базе данных")
        return False


def test_ssh_tunnel_with_db():
    """Тестирует SSH туннель с подключением к БД."""
    print("\n🔗 Тестирование SSH туннеля с БД...")
    
    try:
        with ssh_tunnel_context():
            if test_db_connection():
                print("✅ SSH туннель с БД работает успешно!")
                return True
            else:
                print("❌ Ошибка подключения к БД через SSH туннель")
                return False
    except Exception as e:
        print(f"❌ Ошибка SSH туннеля: {e}")
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
        result = analyzer.analyze_sql(test_sql)
        
        if result.is_valid:
            print("✅ SQL анализатор работает успешно!")
            print(f"   Время анализа: {result.analysis_time:.3f} сек")
            if result.metrics:
                print(f"   Ожидаемое время выполнения: {result.metrics.estimated_time_ms:.2f} мс")
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
    print("🐘 PostgreSQL SQL Analyzer - Тест подключения")
    print("=" * 50)
    
    # Проверяем наличие .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ Файл .env не найден")
        print("   Скопируйте env_template.txt в .env и настройте переменные")
        return
    
    print(f"📁 Используется файл конфигурации: {env_file.absolute()}")
    
    # Тестируем компоненты
    tests = [
        ("SSH подключение", test_ssh_tunnel),
        ("Подключение к БД", test_database_connection),
        ("SSH туннель с БД", test_ssh_tunnel_with_db),
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
    print("\n" + "=" * 50)
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
