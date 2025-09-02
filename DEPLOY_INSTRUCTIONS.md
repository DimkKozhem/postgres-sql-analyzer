# 🚀 Инструкция по деплою PostgreSQL SQL Analyzer на сервер

## 📋 Информация о сервере

- **Сервер:** MoreTech_LCT
- **IP адрес:** 31.172.73.121
- **Пользователь:** root
- **Пароль:** KTYLhVsgiAL9t0L3
- **Порт приложения:** 8505

---

## 🎯 Варианты деплоя

### 1. **Автоматический деплой (рекомендуется)**

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите автоматический деплой
./deploy.sh
```

**Что делает автоматический деплой:**
- ✅ Создает архив проекта
- ✅ Загружает на сервер
- ✅ Устанавливает зависимости
- ✅ Создает systemd сервис
- ✅ Настраивает автозапуск
- ✅ Открывает порт в firewall

---

### 2. **Ручной деплой (пошагово)**

#### **Шаг 1: Подготовка проекта**
```bash
# Создайте архив проекта
chmod +x deploy_simple.sh
./deploy_simple.sh
```

#### **Шаг 2: Подключение к серверу**
```bash
ssh root@31.172.73.121
# Пароль: KTYLhVsgiAL9t0L3
```

#### **Шаг 3: Создание директории**
```bash
mkdir -p /opt/postgres-sql-analyzer
cd /opt/postgres-sql-analyzer
```

#### **Шаг 4: Копирование архива (из другой терминальной сессии)**
```bash
scp postgres-sql-analyzer.tar.gz root@31.172.73.121:/opt/postgres-sql-analyzer/
```

#### **Шаг 5: Установка зависимостей**
```bash
# Распаковка
tar -xzf postgres-sql-analyzer.tar.gz
rm postgres-sql-analyzer.tar.gz

# Системные зависимости
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev

# Python окружение
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Шаг 6: Запуск приложения**
```bash
# Прямой запуск
python run_streamlit_fixed.py

# Или в фоне через screen
screen -S sql-analyzer
python run_streamlit_fixed.py
# Ctrl+A, D для отключения от screen
```

---

## 🔧 Настройка продакшена

### **Конфигурация LLM**

#### **OpenAI API**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
export SQL_ANALYZER_AI_PROVIDER="openai"
```

#### **Anthropic API**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
export SQL_ANALYZER_AI_PROVIDER="anthropic"
```

#### **Локальные модели**
```bash
export LOCAL_LLM_URL="http://localhost:11434"
export LOCAL_LLM_MODEL="llama2"
export SQL_ANALYZER_AI_PROVIDER="local"
```

### **Проверка конфигурации**
```bash
python production_config.py
```

---

## 🚀 Создание systemd сервиса

### **Автоматически (через deploy.sh)**
Скрипт создаст сервис автоматически.

### **Вручную**
```bash
cat > /etc/systemd/system/postgres-sql-analyzer.service << 'EOF'
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
EOF

# Активация сервиса
systemctl daemon-reload
systemctl enable postgres-sql-analyzer
systemctl start postgres-sql-analyzer
```

---

## 📊 Управление сервисом

### **Проверка статуса**
```bash
systemctl status postgres-sql-analyzer
```

### **Перезапуск**
```bash
systemctl restart postgres-sql-analyzer
```

### **Просмотр логов**
```bash
journalctl -u postgres-sql-analyzer -f
```

### **Остановка**
```bash
systemctl stop postgres-sql-analyzer
```

---

## 🔒 Безопасность

### **Firewall**
```bash
# Открытие порта 8505
ufw allow 8505/tcp

# Проверка статуса
ufw status
```

### **SSL/TLS (опционально)**
```bash
# Установка certbot
apt-get install -y certbot

# Получение SSL сертификата
certbot certonly --standalone -d your-domain.com
```

---

## 🌐 Доступ к приложению

### **После успешного деплоя:**
- **URL:** http://31.172.73.121:8505
- **Локальный доступ:** http://localhost:8505
- **Сетевой доступ:** http://31.172.73.121:8505

### **Проверка доступности**
```bash
# С сервера
curl -s http://localhost:8505 | head -5

# С внешнего хоста
curl -s http://31.172.73.121:8505 | head -5
```

---

## 🧪 Тестирование деплоя

### **Проверка работы приложения**
1. Откройте браузер: http://31.172.73.121:8505
2. Проверьте Mock режим
3. Протестируйте анализ SQL
4. Проверьте LLM интеграцию (если настроена)

### **Проверка логов**
```bash
# Логи systemd
journalctl -u postgres-sql-analyzer --no-pager -l

# Логи Streamlit
tail -f /opt/postgres-sql-analyzer/streamlit.log
```

---

## 🆘 Решение проблем

### **Порт занят**
```bash
# Поиск процесса
netstat -tlnp | grep 8505
lsof -i :8505

# Убийство процесса
kill -9 <PID>
```

### **Ошибки импорта**
```bash
# Проверка PYTHONPATH
echo $PYTHONPATH

# Установка PYTHONPATH
export PYTHONPATH=/opt/postgres-sql-analyzer:$PYTHONPATH
```

### **Проблемы с зависимостями**
```bash
# Пересоздание venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📈 Мониторинг

### **Системные ресурсы**
```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Сетевые соединения
netstat -tlnp
```

### **Логи приложения**
```bash
# Реальное время
journalctl -u postgres-sql-analyzer -f

# Последние 100 строк
journalctl -u postgres-sql-analyzer -n 100
```

---

## 🎉 Успешный деплой

После успешного деплоя у вас будет:

- ✅ **Работающее приложение** на http://31.172.73.121:8505
- ✅ **Автозапуск** при перезагрузке сервера
- ✅ **Systemd сервис** для управления
- ✅ **Логирование** всех событий
- ✅ **Firewall** настроен
- ✅ **LLM интеграция** готова к настройке

**PostgreSQL SQL Analyzer успешно развернут на продакшен сервере!** 🚀

---

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи:** `journalctl -u postgres-sql-analyzer -f`
2. **Статус сервиса:** `systemctl status postgres-sql-analyzer`
3. **Доступность порта:** `netstat -tlnp | grep 8505`
4. **Создайте issue** в репозитории проекта

**Удачи с деплоем!** 🎯
