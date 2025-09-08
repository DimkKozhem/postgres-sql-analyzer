#!/bin/bash
# start_app.sh - Скрипт для запуска PostgreSQL SQL Analyzer

echo "🚀 Запуск PostgreSQL SQL Analyzer..."

# Проверить, что мы в правильной директории
if [ ! -f "app/streamlit_app.py" ]; then
    echo "❌ Ошибка: Запустите скрипт из корневой директории проекта"
    echo "   cd /home/dimk/postgres-sql-analyzer"
    exit 1
fi

# Активировать виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Проверить SSH подключение
echo "🔐 Проверка SSH подключения..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa skripka@193.246.150.18 "echo 'SSH OK'" || {
    echo "❌ SSH подключение не удалось"
    echo "   Проверьте SSH ключ и доступность сервера"
    exit 1
}

# Остановить существующие SSH туннели
echo "🔄 Остановка существующих туннелей..."
pkill -f "ssh.*5433.*skripka@193.246.150.18" 2>/dev/null || true

# Проверить, что порт 5433 свободен
if lsof -i :5433 >/dev/null 2>&1; then
    echo "⚠️  Порт 5433 занят. Попытка освободить..."
    sudo lsof -i :5433 | grep LISTEN | awk '{print $2}' | xargs -r sudo kill -9
    sleep 2
fi

# Проверить, что порт 8505 свободен
if lsof -i :8505 >/dev/null 2>&1; then
    echo "⚠️  Порт 8505 занят. Попытка освободить..."
    sudo lsof -i :8505 | grep LISTEN | awk '{print $2}' | xargs -r sudo kill -9
    sleep 2
fi

echo "✅ Окружение подготовлено"
echo "🌐 Приложение будет доступно по адресу: http://localhost:8505"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo ""

# Запустить приложение
echo "🚀 Запуск приложения..."
python scripts/run_streamlit.py
