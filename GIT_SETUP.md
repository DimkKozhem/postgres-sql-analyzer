# 🔧 Настройка Git и загрузка на GitHub/GitLab

## ✅ Git репозиторий уже настроен локально

Ваш проект уже инициализирован как Git репозиторий и готов к загрузке.

---

## 🚀 Загрузка на GitHub

### **Шаг 1: Создайте новый репозиторий на GitHub**

1. Перейдите на [github.com](https://github.com)
2. Нажмите **"New repository"** или **"+" → "New repository"**
3. Заполните поля:
   - **Repository name:** `postgres-sql-analyzer`
   - **Description:** `PostgreSQL SQL Analyzer with LLM integration - preventive SQL query analysis tool`
   - **Visibility:** ⚠️ **ВАЖНО! Выберите "Private"** ⚠️
   - **Initialize this repository with:** НЕ отмечайте галочки
4. Нажмите **"Create repository"**

### **Шаг 2: Загрузите проект**

```bash
# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваше имя пользователя)
git remote add origin https://github.com/YOUR_USERNAME/postgres-sql-analyzer.git

# Загрузите проект
git push -u origin main
```

---

## 🚀 Загрузка на GitLab

### **Шаг 1: Создайте новый проект на GitLab**

1. Перейдите на [gitlab.com](https://gitlab.com)
2. Нажмите **"New project"**
3. Выберите **"Create blank project"**
4. Заполните поля:
   - **Project name:** `postgres-sql-analyzer`
   - **Description:** `PostgreSQL SQL Analyzer with LLM integration - preventive SQL query analysis tool`
   - **Visibility Level:** ⚠️ **ВАЖНО! Выберите "Private"** ⚠️
5. Нажмите **"Create project"**

### **Шаг 2: Загрузите проект**

```bash
# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваше имя пользователя)
git remote add origin https://gitlab.com/YOUR_USERNAME/postgres-sql-analyzer.git

# Загрузите проект
git push -u origin main
```

---

## 🔐 Настройка приватности

### **GitHub - Приватный репозиторий**
- ✅ Репозиторий виден только вам и приглашенным участникам
- ✅ Код не индексируется поисковыми системами
- ✅ Требуется аутентификация для доступа

### **GitLab - Приватный проект**
- ✅ Проект виден только вам и приглашенным участникам
- ✅ Код защищен от публичного доступа
- ✅ Требуется авторизация для просмотра

---

## 📋 Команды для загрузки

### **Для GitHub:**
```bash
# Добавить удаленный репозиторий
git remote add origin https://github.com/YOUR_USERNAME/postgres-sql-analyzer.git

# Загрузить проект
git push -u origin main

# Проверить статус
git remote -v
git status
```

### **Для GitLab:**
```bash
# Добавить удаленный репозиторий
git remote add origin https://gitlab.com/YOUR_USERNAME/postgres-sql-analyzer.git

# Загрузить проект
git push -u origin main

# Проверить статус
git remote -v
git status
```

---

## 🔑 Аутентификация

### **GitHub:**
- Используйте **Personal Access Token** или **SSH ключи**
- Рекомендуется: Personal Access Token с правами `repo`

### **GitLab:**
- Используйте **Personal Access Token** или **SSH ключи**
- Рекомендуется: Personal Access Token с правами `write_repository`

---

## 📁 Структура проекта в Git

```
postgres-sql-analyzer/
├── app/                    # Основные модули приложения
├── tests/                  # Тесты
├── docs/                   # Документация
├── examples/               # Примеры SQL запросов
├── .github/                # GitHub Actions CI/CD
├── Dockerfile              # Docker контейнер
├── docker-compose.yml      # Docker Compose
├── requirements.txt        # Python зависимости
├── README.md               # Основная документация
├── deploy.sh               # Скрипт автоматического деплоя
└── production_config.py    # Конфигурация для продакшена
```

---

## 🚀 После загрузки

### **Проверьте:**
1. ✅ Репозиторий загружен
2. ✅ Все файлы на месте
3. ✅ Репозиторий приватный
4. ✅ CI/CD настроен (GitHub Actions)

### **Дополнительные настройки:**
- **Issues:** Включены для отслеживания задач
- **Wiki:** Можно включить для документации
- **Projects:** Для управления проектом
- **Security:** Сканирование уязвимостей

---

## 🔒 Безопасность

### **Приватный репозиторий обеспечивает:**
- ✅ Код не виден публично
- ✅ API ключи защищены
- ✅ Конфигурации серверов скрыты
- ✅ Коммерческая тайна сохранена

---

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте права доступа** к репозиторию
2. **Убедитесь, что репозиторий приватный**
3. **Проверьте настройки аутентификации**
4. **Обратитесь к документации** GitHub/GitLab

---

## 🎯 Готово!

**Ваш проект PostgreSQL SQL Analyzer готов к загрузке на Git!**

**Не забудьте:**
- ⚠️ **Выбрать "Private"** при создании репозитория
- 🔑 **Настроить аутентификацию** (токены или SSH)
- 📋 **Следовать инструкциям** для вашей платформы

**Удачи с загрузкой проекта!** 🚀
