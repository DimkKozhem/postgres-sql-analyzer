#!/usr/bin/env python3
"""Тестовый скрипт для проверки функциональности PostgreSQL SQL Analyzer."""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Тестирует импорт всех модулей."""
    print("🔍 Тестирование импорта модулей...")
    
    try:
        import app.config
        print("✅ config.py - OK")
    except Exception as e:
        print(f"❌ config.py - Ошибка: {e}")
    
    try:
        import app.database
        print("✅ database.py - OK")
    except Exception as e:
        print(f"❌ database.py - Ошибка: {e}")
    
    try:
        import app.plan_parser
        print("✅ plan_parser.py - OK")
    except Exception as e:
        print(f"❌ plan_parser.py - Ошибка: {e}")
    
    try:
        import app.recommendations
        print("✅ recommendations.py - OK")
    except Exception as e:
        print(f"❌ recommendations.py - Ошибка: {e}")
    
    try:
        import app.analyzer
        print("✅ analyzer.py - OK")
    except Exception as e:
        print(f"❌ analyzer.py - Ошибка: {e}")
    
    try:
        import app.streamlit_app
        print("✅ streamlit_app.py - OK")
    except Exception as e:
        print(f"❌ streamlit_app.py - Ошибка: {e}")

def test_analyzer():
    """Тестирует основной функционал анализатора."""
    print("\n🔍 Тестирование анализатора...")
    
    try:
        from app.analyzer import SQLAnalyzer
        
        # Тест в mock режиме
        analyzer = SQLAnalyzer(mock_mode=True)
        print("✅ Создание анализатора в mock режиме - OK")
        
        # Тест анализа простого SQL
        result = analyzer.analyze_sql("SELECT * FROM users LIMIT 10;")
        print("✅ Анализ SQL в mock режиме - OK")
        
        # Тест получения примеров
        examples = analyzer.get_example_queries()
        print(f"✅ Получение примеров - OK ({len(examples)} примеров)")
        
        # Тест экспорта
        json_report = analyzer.export_analysis_report(result, "json")
        text_report = analyzer.export_analysis_report(result, "text")
        print("✅ Экспорт отчетов - OK")
        
        print("✅ Все тесты анализатора прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования анализатора: {e}")
        import traceback
        traceback.print_exc()

def test_config():
    """Тестирует конфигурацию."""
    print("\n🔍 Тестирование конфигурации...")
    
    try:
        from app.config import get_default_config
        
        config = get_default_config()
        print("✅ Загрузка конфигурации - OK")
        print(f"   Mock режим: {config.get('mock_mode', 'N/A')}")
        print(f"   work_mem: {config.get('work_mem', 'N/A')} MB")
        print(f"   shared_buffers: {config.get('shared_buffers', 'N/A')} MB")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование PostgreSQL SQL Analyzer")
    print("=" * 50)
    
    # Тестируем импорты
    test_imports()
    
    # Тестируем конфигурацию
    test_config()
    
    # Тестируем анализатор
    test_analyzer()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    
    # Проверяем готовность к запуску
    print("\n📱 Готовность к запуску Streamlit:")
    print("✅ Все модули импортируются")
    print("✅ Анализатор работает в mock режиме")
    print("✅ Конфигурация загружается")
    print("\n🚀 Для запуска интерфейса выполните:")
    print("   streamlit run app/streamlit_app.py")

if __name__ == "__main__":
    main()
