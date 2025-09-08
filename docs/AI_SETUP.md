# 🤖 Настройка AI для PostgreSQL SQL Analyzer

## 📋 Обзор

PostgreSQL SQL Analyzer поддерживает интеграцию с различными AI провайдерами для генерации умных рекомендаций по оптимизации SQL запросов.

## 🎯 Поддерживаемые провайдеры

### 1. **OpenAI** (рекомендуется)
- **Модели**: gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Рекомендуемая модель**: `gpt-4o-mini` (баланс качества и стоимости)
- **API**: https://platform.openai.com/

### 2. **Anthropic**
- **Модели**: claude-3-5-sonnet, claude-3-opus, claude-3-sonnet, claude-3-haiku
- **API**: https://console.anthropic.com/

### 3. **Локальные LLM**
- **Ollama**: llama3.1, llama3, codellama, mistral, qwen
- **URL**: http://localhost:11434

## ⚙️ Настройка OpenAI

### 1. Получение API ключа
1. Зарегистрируйтесь на https://platform.openai.com/
2. Перейдите в раздел "API Keys"
3. Создайте новый API ключ
4. Скопируйте ключ (начинается с `sk-proj-`)

### 2. Настройка в .env файле
```bash
# OpenAI настройки
SQL_ANALYZER_OPENAI_API_KEY=sk-proj-your-api-key-here
SQL_ANALYZER_OPENAI_MODEL=gpt-4o-mini
SQL_ANALYZER_OPENAI_TEMPERATURE=0.7
SQL_ANALYZER_ENABLE_AI_RECOMMENDATIONS=true
SQL_ANALYZER_AI_PROVIDER=openai
SQL_ANALYZER_AI_CONFIDENCE_THRESHOLD=0.7
```

### 3. Настройка в интерфейсе
В боковой панели Streamlit:
1. **Провайдер AI**: Выберите "OpenAI"
2. **OpenAI API Key**: Введите ваш API ключ
3. **Модель OpenAI**: Выберите `gpt-4o-mini`
4. **Температура**: Установите `0.7`

## ⚙️ Настройка Anthropic

### 1. Получение API ключа
1. Зарегистрируйтесь на https://console.anthropic.com/
2. Перейдите в раздел "API Keys"
3. Создайте новый API ключ
4. Скопируйте ключ

### 2. Настройка в .env файле
```bash
# Anthropic настройки
SQL_ANALYZER_ANTHROPIC_API_KEY=your-anthropic-key-here
SQL_ANALYZER_ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
SQL_ANALYZER_ENABLE_AI_RECOMMENDATIONS=true
SQL_ANALYZER_AI_PROVIDER=anthropic
```

### 3. Настройка в интерфейсе
В боковой панели Streamlit:
1. **Провайдер AI**: Выберите "Anthropic"
2. **Anthropic API Key**: Введите ваш API ключ
3. **Модель Anthropic**: Выберите `claude-3-5-sonnet-20240620`

## ⚙️ Настройка локального LLM

### 1. Установка Ollama
```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama
ollama serve

# Установка модели
ollama pull llama3.1:8b
```

### 2. Настройка в .env файле
```bash
# Локальный LLM настройки
SQL_ANALYZER_LOCAL_LLM_URL=http://localhost:11434
SQL_ANALYZER_LOCAL_LLM_MODEL=llama3.1:8b
SQL_ANALYZER_ENABLE_AI_RECOMMENDATIONS=true
SQL_ANALYZER_AI_PROVIDER=local
```

### 3. Настройка в интерфейсе
В боковой панели Streamlit:
1. **Провайдер AI**: Выберите "Локальный LLM"
2. **URL локального LLM**: `http://localhost:11434`
3. **Модель локального LLM**: Выберите `llama3.1:8b`

## 🧪 Тестирование AI

### Проверка настроек
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Тестировать AI настройки
python -c "
from app.config import settings
from app.llm_integration import LLMIntegration

print('🤖 Тестирование AI настроек')
print(f'OpenAI API Key: {settings.OPENAI_API_KEY[:20]}...' if settings.OPENAI_API_KEY else 'OpenAI API Key: НЕ ЗАДАН')
print(f'OpenAI Model: {settings.OPENAI_MODEL}')
print(f'Enable AI: {settings.ENABLE_AI_RECOMMENDATIONS}')

try:
    llm = LLMIntegration({
        'openai_api_key': settings.OPENAI_API_KEY,
        'openai_model': settings.OPENAI_MODEL,
        'ai_provider': settings.AI_PROVIDER
    })
    print('✅ AI интеграция работает')
except Exception as e:
    print(f'❌ Ошибка AI: {e}')
"
```

### Тестирование в приложении
1. Запустите приложение: `./start_app.sh`
2. Откройте браузер: http://localhost:8505
3. В боковой панели выберите провайдера AI
4. Введите SQL запрос в вкладке "Анализ SQL"
5. Проверьте, что AI рекомендации генерируются

## 📊 Параметры AI

### Температура (Temperature)
- **0.0**: Детерминированные ответы
- **0.7**: Баланс креативности и точности (рекомендуется)
- **1.0**: Креативные ответы
- **2.0**: Очень креативные ответы

### Порог уверенности (Confidence Threshold)
- **0.5**: Показывать все рекомендации
- **0.7**: Показывать уверенные рекомендации (рекомендуется)
- **0.9**: Показывать только очень уверенные рекомендации

## 💰 Стоимость использования

### OpenAI
- **gpt-4o-mini**: $0.15/1M токенов (рекомендуется)
- **gpt-4o**: $2.50/1M токенов
- **gpt-4-turbo**: $10/1M токенов
- **gpt-4**: $30/1M токенов

### Anthropic
- **claude-3-5-sonnet**: $3/1M токенов
- **claude-3-opus**: $15/1M токенов
- **claude-3-sonnet**: $3/1M токенов
- **claude-3-haiku**: $0.25/1M токенов

### Локальный LLM
- **Бесплатно** (требует локальные ресурсы)

## 🔒 Безопасность

### Рекомендации по безопасности
1. **Не коммитьте API ключи** в Git
2. **Используйте переменные окружения** для хранения ключей
3. **Ограничьте права API ключей** в настройках провайдера
4. **Мониторьте использование** через дашборды провайдеров
5. **Регулярно ротируйте ключи**

### Настройка ограничений
```bash
# Ограничить использование OpenAI
export OPENAI_USAGE_LIMIT=1000  # $10 в месяц

# Ограничить количество запросов
export AI_MAX_REQUESTS_PER_HOUR=100
```

## 🐛 Устранение неполадок

### Проблема: "Invalid API key"
```bash
# Проверить API ключ
echo $SQL_ANALYZER_OPENAI_API_KEY

# Проверить формат ключа
# OpenAI: sk-proj-...
# Anthropic: sk-ant-...
```

### Проблема: "Rate limit exceeded"
```bash
# Увеличить интервал между запросами
export AI_REQUEST_DELAY=2  # секунды

# Уменьшить температуру для более предсказуемых ответов
export SQL_ANALYZER_OPENAI_TEMPERATURE=0.3
```

### Проблема: "Connection timeout"
```bash
# Проверить интернет соединение
ping api.openai.com

# Увеличить таймаут
export AI_TIMEOUT=30  # секунды
```

## 📈 Оптимизация производительности

### Рекомендации
1. **Используйте gpt-4o-mini** для баланса скорости и качества
2. **Кэшируйте результаты** для повторных запросов
3. **Ограничьте длину промптов** для экономии токенов
4. **Используйте локальные модели** для конфиденциальных данных

### Настройка кэширования
```bash
# Включить кэширование AI ответов
export AI_ENABLE_CACHE=true
export AI_CACHE_TTL=3600  # 1 час
```

---

**🎉 AI настройки готовы! Теперь вы можете получать умные рекомендации по оптимизации SQL запросов.**
