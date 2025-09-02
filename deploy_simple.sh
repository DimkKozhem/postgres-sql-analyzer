#!/bin/bash

# 🚀 Упрощенный скрипт деплоя PostgreSQL SQL Analyzer
# Сервер: MoreTech_LCT (31.172.73.121)

echo "🚀 Деплой PostgreSQL SQL Analyzer на сервер 31.172.73.121"
echo ""

# Создание архива
echo "📦 Создание архива проекта..."
tar --exclude='venv' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.idea' \
    --exclude='get-pip.py' \
    --exclude='deploy*.sh' \
    -czf postgres-sql-analyzer.tar.gz .

echo "✅ Архив создан: postgres-sql-analyzer.tar.gz"
echo ""

echo "📤 Теперь выполните следующие команды на сервере:"
echo ""
echo "1. Подключитесь к серверу:"
echo "   ssh root@31.172.73.121"
echo "   Пароль: KTYLhVsgiAL9t0L3"
echo ""
echo "2. Создайте директорию:"
echo "   mkdir -p /opt/postgres-sql-analyzer"
echo "   cd /opt/postgres-sql-analyzer"
echo ""
echo "3. Скопируйте архив (из другой терминальной сессии):"
echo "   scp postgres-sql-analyzer.tar.gz root@31.172.73.121:/opt/postgres-sql-analyzer/"
echo ""
echo "4. На сервере распакуйте и настройте:"
echo "   tar -xzf postgres-sql-analyzer.tar.gz"
echo "   rm postgres-sql-analyzer.tar.gz"
echo "   apt-get update"
echo "   apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install --upgrade pip"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Запустите приложение:"
echo "   python run_streamlit_fixed.py"
echo ""
echo "🌐 Приложение будет доступно по адресу: http://31.172.73.121:8505"
echo ""
echo "💡 Для фонового запуска используйте screen или tmux:"
echo "   screen -S sql-analyzer"
echo "   python run_streamlit_fixed.py"
echo "   Ctrl+A, D (для отключения от screen)"
echo "   screen -r sql-analyzer (для подключения обратно)"
