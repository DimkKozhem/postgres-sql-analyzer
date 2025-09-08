# 🏗️ Структура проекта PostgreSQL SQL Analyzer

Этот документ описывает структуру проекта и назначение каждого компонента.

## 📁 Общая структура

```
postgres-sql-analyzer/
├── 📁 app/                    # Основной код приложения
├── 📁 config/                 # Конфигурационные файлы
├── 📁 docs/                   # Документация проекта
├── 📁 scripts/                # Скрипты запуска и деплоя
├── 📁 tests/                  # Тесты
│   ├── 📁 unit/               # Unit тесты
│   └── 📁 integration/        # Интеграционные тесты
├── 📁 stubs/                  # Type stubs для psycopg2
├── 📁 venv/                   # Виртуальное окружение Python
├── 📄 .env                    # Переменные окружения (не в git)
├── 📄 .gitignore              # Игнорируемые файлы
├── 📄 docker-compose.yml      # Docker Compose конфигурация
├── 📄 Dockerfile              # Docker образ
├── 📄 Makefile                # Команды для разработки
├── 📄 pyproject.toml          # Конфигурация Python проекта
├── 📄 pytest.ini             # Конфигурация тестов
├── 📄 requirements.txt        # Основные зависимости
├── 📄 requirements-dev.txt    # Зависимости для разработки
└── 📄 README.md               # Основной README
```

## 📁 app/ - Основной код приложения

```
app/
├── 📄 __init__.py             # Инициализация пакета
├── 📄 analyzer.py             # Основной класс анализатора
├── 📄 cli.py                  # CLI интерфейс
├── 📄 config.py               # Конфигурация приложения
├── 📄 database.py             # Работа с базой данных
├── 📄 llm_integration.py      # Интеграция с LLM
├── 📄 plan_parser.py          # Парсинг планов выполнения
├── 📄 recommendations.py      # Генерация рекомендаций
├── 📄 ssh_tunnel.py           # SSH туннелирование
├── 📄 streamlit_app.py        # Streamlit веб-интерфейс
└── 📁 ui/                     # UI компоненты
    ├── 📄 __init__.py
    ├── 📄 examples.py         # Вкладка примеров
    ├── 📄 execution_plans.py  # Вкладка планов выполнения
    ├── 📄 help.py             # Вкладка справки
    ├── 📄 sql_analysis.py     # Вкладка анализа SQL
    ├── 📄 statistics.py       # Вкладка статистики
    └── 📄 styles.py           # Стили интерфейса
```

## 📁 docs/ - Документация

```
docs/
├── 📄 INDEX.md                # Индекс документации
├── 📄 README.md               # Основная документация
├── 📄 QUICK_DEPLOY.md         # Быстрый старт
├── 📄 ENV_SETUP.md            # Настройка переменных окружения
├── 📄 SSH_SETUP.md            # Настройка SSH
├── 📄 DEPLOY_INSTRUCTIONS.md  # Инструкции по деплою
└── 📄 PROJECT_STRUCTURE.md    # Этот файл
```

## 📁 tests/ - Тесты

```
tests/
├── 📄 __init__.py
├── 📁 unit/                   # Unit тесты
│   ├── 📄 __init__.py
│   ├── 📄 test_analyzer.py    # Тесты анализатора
│   └── 📄 test_llm_integration.py # Тесты LLM интеграции
└── 📁 integration/            # Интеграционные тесты
    ├── 📄 __init__.py
    ├── 📄 test_db_connection.py # Тесты подключения к БД
    ├── 📄 test_simple_db_connection.py # Простые тесты БД
    └── 📄 test_ssh_db_connection.py # Тесты SSH подключения
```

## 📁 scripts/ - Скрипты

```
scripts/
├── 📄 deploy.sh               # Скрипт деплоя
├── 📄 deploy_simple.sh        # Простой деплой
└── 📄 run_streamlit.py        # Запуск Streamlit приложения
```

## 📁 config/ - Конфигурация

```
config/
├── 📄 env_template.txt        # Шаблон переменных окружения
└── 📄 production_config.py    # Продакшн конфигурация
```

## 🔧 Основные компоненты

### 📄 analyzer.py
**Основной класс анализатора SQL-запросов**
- `SQLAnalyzer` - главный класс для анализа
- `AnalysisResult` - результат анализа
- Методы анализа, экспорта, конфигурации

### 📄 database.py
**Работа с базой данных PostgreSQL**
- `DatabaseConnection` - подключение к БД
- Выполнение EXPLAIN запросов
- Получение статистики pg_stat_statements
- Валидация SQL запросов

### 📄 ssh_tunnel.py
**SSH туннелирование для безопасного подключения**
- `SSHTunnel` - управление SSH туннелями
- Контекстные менеджеры для туннелей
- Тестирование подключений

### 📄 streamlit_app.py
**Веб-интерфейс на Streamlit**
- Главная страница приложения
- Настройки подключения
- Интеграция с UI компонентами

### 📁 ui/ - UI компоненты
**Модульные компоненты интерфейса**
- `sql_analysis.py` - анализ SQL запросов
- `statistics.py` - статистика производительности
- `execution_plans.py` - планы выполнения
- `examples.py` - примеры запросов
- `help.py` - справка
- `styles.py` - стили и утилиты

## ⚙️ Конфигурационные файлы

### 📄 config.py
**Настройки приложения**
- Параметры PostgreSQL
- SSH настройки
- LLM конфигурация
- Пороги анализа

### 📄 .env
**Переменные окружения** (не в git)
- API ключи
- Настройки БД
- SSH параметры

### 📄 pyproject.toml
**Конфигурация Python проекта**
- Зависимости
- Настройки тестов
- Конфигурация инструментов

### 📄 Makefile
**Команды для разработки**
- Установка зависимостей
- Запуск тестов
- Линтинг кода
- Сборка Docker

## 🐳 Docker конфигурация

### 📄 Dockerfile
**Docker образ приложения**
- Базовый образ Python
- Установка зависимостей
- Настройка окружения

### 📄 docker-compose.yml
**Docker Compose конфигурация**
- Сервисы приложения
- Сетевые настройки
- Переменные окружения

## 🧪 Тестирование

### 📄 pytest.ini
**Конфигурация pytest**
- Маркеры тестов
- Настройки покрытия
- Фильтры предупреждений

### 📁 tests/
**Тестовые файлы**
- Unit тесты
- Интеграционные тесты
- Моки и фикстуры

## 📦 Зависимости

### 📄 requirements.txt
**Основные зависимости**
- Streamlit
- psycopg2
- pydantic
- plotly

### 📄 requirements-dev.txt
**Зависимости для разработки**
- pytest
- black, flake8, isort
- mypy
- bandit, safety

## 🚀 Скрипты запуска

### 📄 run_streamlit.py
**Скрипт запуска Streamlit приложения**
- Проверка зависимостей
- Настройка окружения
- Запуск приложения

## 📝 Документация

### 📁 docs/
**Вся документация проекта**
- README с полным описанием
- Инструкции по установке
- Руководства по настройке
- Инструкции по деплою

## 🔍 Поиск по структуре

Для быстрого поиска компонентов:

- **Анализ SQL** → `app/analyzer.py`, `app/ui/sql_analysis.py`
- **База данных** → `app/database.py`, `app/ssh_tunnel.py`
- **Интерфейс** → `app/streamlit_app.py`, `app/ui/`
- **Конфигурация** → `app/config.py`, `config/`, `.env`
- **Unit тесты** → `tests/unit/`
- **Интеграционные тесты** → `tests/integration/`
- **Скрипты** → `scripts/`
- **Документация** → `docs/`
- **Docker** → `Dockerfile`, `docker-compose.yml`

---

**📚 Эта структура обеспечивает модульность, тестируемость и простоту сопровождения проекта.**
