# 🔐 Настройка SSH подключения к серверу

Это руководство поможет настроить SSH подключение к серверу `193.246.150.18` для работы с PostgreSQL SQL Analyzer.

## 🎯 Цель

Настроить безопасное подключение к базе данных PostgreSQL через SSH туннель:
```bash
ssh -v -i ~/.ssh/id_rsa skripka@193.246.150.18
```

## 📋 Предварительные требования

- SSH ключ для пользователя `skripka`
- Доступ к серверу `193.246.150.18`
- PostgreSQL на удаленном сервере

## 🔑 Настройка SSH ключей

### 1. Проверка существующих ключей
```bash
ls -la ~/.ssh/
```

### 2. Создание нового SSH ключа (если нужно)
```bash
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
```

### 3. Копирование публичного ключа на сервер
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub skripka@193.246.150.18
```

### 4. Тестирование SSH подключения
```bash
ssh -v -i ~/.ssh/id_rsa skripka@193.246.150.18
```

## ⚙️ Настройка приложения

### 1. Обновление .env файла
```bash
# SSH настройки
SQL_ANALYZER_SSH_HOST=193.246.150.18
SQL_ANALYZER_SSH_PORT=22
SQL_ANALYZER_SSH_USER=skripka
SQL_ANALYZER_SSH_KEY_PATH=~/.ssh/id_rsa
SQL_ANALYZER_AUTO_CREATE_SSH_TUNNEL=true
SQL_ANALYZER_SSH_TIMEOUT=30

# Настройки базы данных
SQL_ANALYZER_DB_HOST=localhost
SQL_ANALYZER_DB_PORT=5433
SQL_ANALYZER_DB_NAME=postgres
SQL_ANALYZER_DB_USER=readonly_user
SQL_ANALYZER_DB_PASSWORD=skripka_user
```

### 2. Настройка в Streamlit интерфейсе

В боковой панели приложения:

1. **Тип подключения**: Выберите "SSH туннель"
2. **SSH хост**: `193.246.150.18`
3. **SSH порт**: `22`
4. **SSH пользователь**: `skripka`
5. **Путь к SSH ключу**: `~/.ssh/id_rsa`
6. **Хост БД**: `localhost` (для SSH туннеля)
7. **Порт БД**: `5433`
8. **База данных**: `postgres`
9. **Пользователь**: `readonly_user`

## 🔧 Принцип работы

### SSH туннелирование
```
Локальная машина → SSH туннель → Сервер 193.246.150.18 → PostgreSQL
     :5433              :22              localhost:5432
```

### Команда SSH туннеля
```bash
ssh -N -L 5433:localhost:5432 -i ~/.ssh/id_rsa skripka@193.246.150.18
```

Где:
- `-N`: Не выполнять удаленные команды
- `-L 5433:localhost:5432`: Локальный порт 5433 → удаленный localhost:5432
- `-i ~/.ssh/id_rsa`: Путь к приватному ключу
- `skripka@193.246.150.18`: Пользователь и хост

## 🧪 Тестирование подключения

### 1. Тест SSH подключения
```bash
ssh -o ConnectTimeout=10 -i ~/.ssh/id_rsa skripka@193.246.150.18 "echo 'SSH connection successful'"
```

### 2. Тест SSH туннеля
```bash
# В одном терминале создаем туннель
ssh -N -L 5433:localhost:5432 -i ~/.ssh/id_rsa skripka@193.246.150.18

# В другом терминале тестируем подключение к БД
psql -h localhost -p 5433 -U readonly_user -d postgres
```

### 3. Тест через приложение
1. Запустите PostgreSQL SQL Analyzer
2. В боковой панели выберите "SSH туннель"
3. Нажмите "🔌 Проверить подключение"

## 🐛 Устранение неполадок

### Проблема: "Permission denied (publickey)"
```bash
# Проверьте права на SSH ключ
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Проверьте, что публичный ключ добавлен на сервер
ssh -i ~/.ssh/id_rsa skripka@193.246.150.18
```

### Проблема: "Connection refused"
```bash
# Проверьте доступность сервера
ping 193.246.150.18

# Проверьте SSH порт
telnet 193.246.150.18 22
```

### Проблема: "Port already in use"
```bash
# Найдите процесс, использующий порт 5433
lsof -i :5433

# Убейте процесс или измените порт в настройках
kill -9 <PID>
```

### Проблема: "Database connection failed"
```bash
# Проверьте, что PostgreSQL запущен на сервере
ssh -i ~/.ssh/id_rsa skripka@193.246.150.18 "sudo systemctl status postgresql"

# Проверьте настройки PostgreSQL
ssh -i ~/.ssh/id_rsa skripka@193.246.150.18 "sudo -u postgres psql -c 'SHOW port;'"
```

## 🔒 Безопасность

### Рекомендации по безопасности
1. **Используйте SSH ключи** вместо паролей
2. **Ограничьте права** SSH ключа
3. **Регулярно обновляйте** SSH ключи
4. **Мониторьте подключения** к серверу
5. **Используйте firewall** для ограничения доступа

### Настройка SSH конфигурации
Создайте файл `~/.ssh/config`:
```
Host postgres-server
    HostName 193.246.150.18
    User skripka
    IdentityFile ~/.ssh/id_rsa
    Port 22
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Теперь можно подключаться просто:
```bash
ssh postgres-server
```

## 📊 Мониторинг

### Проверка активных SSH туннелей
```bash
# Список активных SSH соединений
ps aux | grep ssh

# Проверка портов
netstat -tlnp | grep :5433
```

### Логи SSH подключений
```bash
# Логи SSH на клиенте
tail -f /var/log/auth.log

# Логи SSH на сервере
ssh -i ~/.ssh/id_rsa skripka@193.246.150.18 "sudo tail -f /var/log/auth.log"
```

## 🚀 Автоматизация

### Скрипт для создания SSH туннеля
```bash
#!/bin/bash
# create_ssh_tunnel.sh

SSH_HOST="193.246.150.18"
SSH_USER="skripka"
SSH_KEY="~/.ssh/id_rsa"
LOCAL_PORT="5433"
REMOTE_PORT="5432"

echo "Создание SSH туннеля..."
ssh -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} -i ${SSH_KEY} ${SSH_USER}@${SSH_HOST} &
TUNNEL_PID=$!

echo "SSH туннель создан с PID: $TUNNEL_PID"
echo "Для остановки выполните: kill $TUNNEL_PID"
```

### Автозапуск SSH туннеля
```bash
# Добавьте в crontab для автозапуска
@reboot /path/to/create_ssh_tunnel.sh
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи** приложения
2. **Убедитесь в правильности** SSH ключей
3. **Проверьте доступность** сервера
4. **Обратитесь к администратору** сервера
5. **Создайте issue** в репозитории проекта

---

**🎉 SSH подключение настроено! Теперь вы можете безопасно работать с базой данных через туннель.**