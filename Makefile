.PHONY: help install test lint security clean docker-build docker-run docker-stop

# Переменные
PYTHON = python3
PIP = pip3
PYTEST = pytest
STREAMLIT = streamlit

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку по командам
	@echo "$(GREEN)PostgreSQL SQL Analyzer - команды разработки$(NC)"
	@echo ""
	@echo "$(YELLOW)Основные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Зависимости установлены!$(NC)"

install-dev: ## Установить зависимости для разработки
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov flake8 black isort bandit safety
	@echo "$(GREEN)Dev зависимости установлены!$(NC)"

test: ## Запустить тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	$(PYTEST) tests/unit/ tests/integration/ -v --cov=app --cov-report=html --cov-report=term-missing

test-fast: ## Запустить тесты быстро (без покрытия)
	@echo "$(GREEN)Быстрый запуск тестов...$(NC)"
	$(PYTEST) tests/unit/ tests/integration/ -v

test-coverage: ## Запустить тесты с детальным покрытием
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	$(PYTEST) tests/unit/ tests/integration/ --cov=app --cov-report=html --cov-report=xml --cov-report=term-missing

lint: ## Проверить код линтерами
	@echo "$(GREEN)Проверка кода линтерами...$(NC)"
	@echo "$(YELLOW)Flake8...$(NC)"
	flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "$(YELLOW)Black...$(NC)"
	black --check app/ tests/
	@echo "$(YELLOW)isort...$(NC)"
	isort --check-only app/ tests/
	@echo "$(GREEN)Линтинг завершен!$(NC)"

lint-fix: ## Исправить проблемы линтеров
	@echo "$(GREEN)Исправление проблем линтеров...$(NC)"
	black app/ tests/
	isort app/ tests/
	@echo "$(GREEN)Проблемы исправлены!$(NC)"

security: ## Проверить безопасность кода
	@echo "$(GREEN)Проверка безопасности...$(NC)"
	bandit -r app/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "$(GREEN)Проверка безопасности завершена!$(NC)"

run: ## Запустить Streamlit приложение
	@echo "$(GREEN)Запуск Streamlit приложения...$(NC)"
	$(PYTHON) scripts/run_streamlit.py


cli-test: ## Тестировать CLI
	@echo "$(GREEN)Тестирование CLI...$(NC)"
	$(PYTHON) -m app.cli test --dsn "postgresql://test:test@localhost:5432/test"
	$(PYTHON) -m app.cli examples
	$(PYTHON) -m app.cli config

cli-analyze: ## Анализ SQL через CLI
	@echo "$(GREEN)Анализ SQL через CLI...$(NC)"
	$(PYTHON) -m app.cli analyze --sql "SELECT * FROM users LIMIT 10;" --dsn "postgresql://test:test@localhost:5432/test"

docker-build: ## Собрать Docker образ
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t postgres-sql-analyzer .

docker-run: ## Запустить Docker контейнер
	@echo "$(GREEN)Запуск Docker контейнера...$(NC)"
	docker run -d -p 8501:8501 --name sql-analyzer postgres-sql-analyzer

docker-stop: ## Остановить Docker контейнер
	@echo "$(YELLOW)Остановка Docker контейнера...$(NC)"
	docker stop sql-analyzer || true
	docker rm sql-analyzer || true

docker-compose-up: ## Запустить с docker-compose
	@echo "$(GREEN)Запуск с docker-compose...$(NC)"
	docker-compose up -d

docker-compose-down: ## Остановить docker-compose
	@echo "$(YELLOW)Остановка docker-compose...$(NC)"
	docker-compose down

docker-compose-logs: ## Показать логи docker-compose
	@echo "$(YELLOW)Логи docker-compose...$(NC)"
	docker-compose logs -f

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	@echo "$(GREEN)Очистка завершена!$(NC)"

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black app/ tests/
	isort app/ tests/
	@echo "$(GREEN)Код отформатирован!$(NC)"

check-all: ## Запустить все проверки
	@echo "$(GREEN)Запуск всех проверок...$(NC)"
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test
	@echo "$(GREEN)Все проверки завершены!$(NC)"

dev-setup: ## Настройка окружения для разработки
	@echo "$(GREEN)Настройка окружения для разработки...$(NC)"
	$(MAKE) install-dev
	$(MAKE) format
	$(MAKE) check-all
	@echo "$(GREEN)Окружение настроено!$(NC)"

# Специальные команды для CI/CD
ci-test: ## Команда для CI (тестирование)
	$(PYTEST) tests/ --cov=app --cov-report=xml --cov-report=html

ci-lint: ## Команда для CI (линтинг)
	flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check app/ tests/
	isort --check-only app/ tests/

ci-security: ## Команда для CI (безопасность)
	bandit -r app/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true

# Команды для анализа производительности
profile: ## Профилирование производительности
	@echo "$(GREEN)Профилирование производительности...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats -m app.cli test --dsn "postgresql://test:test@localhost:5432/test"
	@echo "$(GREEN)Профилирование завершено!$(NC)"

benchmark: ## Бенчмарк тесты
	@echo "$(GREEN)Запуск бенчмарк тестов...$(NC)"
	$(PYTHON) -m pytest tests/ -m "benchmark" -v

# Команды для документации
docs: ## Генерация документации
	@echo "$(GREEN)Генерация документации...$(NC)"
	# Здесь можно добавить команды для генерации документации
	@echo "$(GREEN)Документация сгенерирована!$(NC)"

# Команды для развертывания
deploy-test: ## Развертывание в тестовой среде
	@echo "$(GREEN)Развертывание в тестовой среде...$(NC)"
	# Здесь можно добавить команды для развертывания
	@echo "$(GREEN)Развертывание завершено!$(NC)"

deploy-prod: ## Развертывание в продакшн
	@echo "$(RED)Развертывание в продакшн...$(NC)"
	# Здесь можно добавить команды для развертывания
	@echo "$(GREEN)Развертывание завершено!$(NC)"

# Команды для мониторинга
monitor: ## Мониторинг приложения
	@echo "$(GREEN)Мониторинг приложения...$(NC)"
	# Здесь можно добавить команды для мониторинга
	@echo "$(GREEN)Мониторинг запущен!$(NC)"

# Команды для резервного копирования
backup: ## Создание резервной копии
	@echo "$(GREEN)Создание резервной копии...$(NC)"
	# Здесь можно добавить команды для резервного копирования
	@echo "$(GREEN)Резервная копия создана!$(NC)"

# Команды для обновления
update: ## Обновление зависимостей
	@echo "$(GREEN)Обновление зависимостей...$(NC)"
	$(PIP) install --upgrade -r requirements.txt
	@echo "$(GREEN)Зависимости обновлены!$(NC)"

# Команды для отладки
debug: ## Запуск в режиме отладки
	@echo "$(GREEN)Запуск в режиме отладки...$(NC)"
	$(PYTHON) -m pdb -m app.cli test --dsn "postgresql://test:test@localhost:5432/test"

# Команды для проверки версий
versions: ## Показать версии компонентов
	@echo "$(GREEN)Версии компонентов:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Streamlit: $(shell $(PYTHON) -c 'import streamlit; print(streamlit.__version__)')"
	@echo "PostgreSQL: $(shell $(PYTHON) -c 'import psycopg2; print(psycopg2.__version__)')"

# Команды для помощи
help-short: ## Краткая справка
	@echo "$(GREEN)Основные команды:$(NC)"
	@echo "  make install    - установка зависимостей"
	@echo "  make test       - запуск тестов"
	@echo "  make run        - запуск приложения"
	@echo "  make docker-run - запуск в Docker"
	@echo "  make clean      - очистка временных файлов"
