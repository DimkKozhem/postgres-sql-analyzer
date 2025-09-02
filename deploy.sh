#!/bin/bash

# 🚀 Скрипт автоматического деплоя PostgreSQL SQL Analyzer на сервер
# Сервер: MoreTech_LCT (31.172.73.121)

set -e  # Остановка при ошибке

echo "🚀 Начинаем деплой PostgreSQL SQL Analyzer на сервер..."

# Конфигурация сервера
SERVER_IP="31.172.73.121"
SERVER_USER="root"
SERVER_PASS="KTYLhVsgiAL9t0L3"
REMOTE_DIR="/opt/postgres-sql-analyzer"
SERVICE_NAME="postgres-sql-analyzer"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📋 Конфигурация деплоя:${NC}"
echo "   Сервер: $SERVER_IP"
echo "   Пользователь: $SERVER_USER"
echo "   Директория: $REMOTE_DIR"
echo "   Сервис: $SERVICE_NAME"
echo ""

# Проверка наличия необходимых файлов
echo -e "${YELLOW}🔍 Проверка файлов проекта...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Файл requirements.txt не найден${NC}"
    exit 1
fi

if [ ! -f "run_streamlit_fixed.py" ]; then
    echo -e "${RED}❌ Файл run_streamlit_fixed.py не найден${NC}"
    exit 1
fi

if [ ! -d "app" ]; then
    echo -e "${RED}❌ Директория app не найдена${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все необходимые файлы найдены${NC}"

# Создание архива проекта
echo -e "${YELLOW}📦 Создание архива проекта...${NC}"
ARCHIVE_NAME="postgres-sql-analyzer.tar.gz"

# Исключаем ненужные файлы
tar --exclude='venv' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.idea' \
    --exclude='get-pip.py' \
    --exclude='deploy.sh' \
    -czf "$ARCHIVE_NAME" .

echo -e "${GREEN}✅ Архив создан: $ARCHIVE_NAME${NC}"

# Загрузка на сервер
echo -e "${YELLOW}📤 Загрузка проекта на сервер...${NC}"

# Используем sshpass для автоматической аутентификации
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass не установлен. Устанавливаем...${NC}"
    sudo apt-get update
    sudo apt-get install -y sshpass
fi

# Создание директории на сервере
echo -e "${YELLOW}📁 Создание директории на сервере...${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
mkdir -p /opt/postgres-sql-analyzer
cd /opt/postgres-sql-analyzer
EOF

# Копирование архива
echo -e "${YELLOW}📋 Копирование архива...${NC}"
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no "$ARCHIVE_NAME" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

# Распаковка и настройка на сервере
echo -e "${YELLOW}🔧 Настройка проекта на сервере...${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /opt/postgres-sql-analyzer

# Распаковка архива
tar -xzf postgres-sql-analyzer.tar.gz
rm postgres-sql-analyzer.tar.gz

# Установка системных зависимостей
echo "📦 Установка системных зависимостей..."
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev

# Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo "📚 Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание systemd сервиса
echo "🔧 Создание systemd сервиса..."
cat > /etc/systemd/system/postgres-sql-analyzer.service << 'SERVICEFILE'
[Unit]
Description=PostgreSQL SQL Analyzer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/postgres-sql-analyzer
Environment=PATH=/opt/postgres-sql-analyzer/venv/bin
ExecStart=/opt/postgres-sql-analyzer/venv/bin/python run_streamlit_fixed.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEFILE

# Перезагрузка systemd и запуск сервиса
echo "🚀 Запуск сервиса..."
systemctl daemon-reload
systemctl enable postgres-sql-analyzer
systemctl start postgres-sql-analyzer

# Проверка статуса
echo "📊 Статус сервиса:"
systemctl status postgres-sql-analyzer --no-pager -l

# Настройка firewall (если нужно)
echo "🔥 Настройка firewall..."
ufw allow 8505/tcp

echo "✅ Деплой завершен!"
echo "🌐 Приложение доступно по адресу: http://31.172.73.121:8505"
EOF

# Очистка локального архива
echo -e "${YELLOW}🧹 Очистка локальных файлов...${NC}"
rm -f "$ARCHIVE_NAME"

echo -e "${GREEN}🎉 Деплой завершен успешно!${NC}"
echo ""
echo -e "${GREEN}📋 Информация о деплое:${NC}"
echo "   Сервер: $SERVER_IP"
echo "   Порт: 8505"
echo "   URL: http://$SERVER_IP:8505"
echo "   Директория: $REMOTE_DIR"
echo "   Сервис: $SERVICE_NAME"
echo ""
echo -e "${YELLOW}🔧 Полезные команды:${NC}"
echo "   Проверить статус: ssh $SERVER_USER@$SERVER_IP 'systemctl status $SERVICE_NAME'"
echo "   Перезапустить: ssh $SERVER_USER@$SERVER_IP 'systemctl restart $SERVICE_NAME'"
echo "   Посмотреть логи: ssh $SERVER_USER@$SERVER_IP 'journalctl -u $SERVICE_NAME -f'"
echo "   Остановить: ssh $SERVER_USER@$SERVER_IP 'systemctl stop $SERVICE_NAME'"
