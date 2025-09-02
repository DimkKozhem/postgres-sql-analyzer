#!/usr/bin/env python3
"""Исправленный скрипт для запуска PostgreSQL SQL Analyzer."""
import sys
import os
import subprocess

def main():
    if not os.path.exists("app/streamlit_app.py"):
        print("❌ Ошибка: app/streamlit_app.py не найден")
        print("   Убедитесь, что вы находитесь в корневой директории проекта")
        sys.exit(1)
    
    venv_python = os.path.join("venv", "bin", "python")
    if not os.path.exists(venv_python):
        print("❌ Виртуальное окружение не найдено")
        print("   Создайте его: python3 -m venv venv")
        print("   Активируйте: source venv/bin/activate")
        print("   Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
    
    print("🚀 Запуск PostgreSQL SQL Analyzer...")
    print("📱 Откройте браузер: http://localhost:8505")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    # Добавляем текущую директорию в PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = os.getcwd() + ':' + env.get('PYTHONPATH', '')
    
    try:
        subprocess.run([
            venv_python, "-m", "streamlit", "run", 
            "app/streamlit_app.py",
            "--server.port", "8505",
            "--server.address", "0.0.0.0"
        ], check=True, cwd=os.getcwd(), env=env)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
