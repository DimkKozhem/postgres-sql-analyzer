#!/usr/bin/env python3
"""Скрипт для запуска Streamlit приложения PostgreSQL SQL Analyzer."""

import subprocess
import sys
import os

def main():
    """Запускает Streamlit приложение."""
    # Активируем виртуальное окружение
    venv_python = os.path.join("venv", "bin", "python")
    
    if not os.path.exists(venv_python):
        print("❌ Виртуальное окружение не найдено. Сначала создайте его:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Запускаем Streamlit
    print("🚀 Запуск PostgreSQL SQL Analyzer...")
    print("📱 Откройте браузер: http://localhost:8501")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    try:
        subprocess.run([
            venv_python, "-m", "streamlit", "run", 
            "app/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
