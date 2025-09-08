# 🔑 Настройка переменных окружения для LLM

## Быстрая настройка

1. **Файл `.env` уже создан** - отредактируйте его и добавьте свои API ключи
2. **Для тестирования** - используйте тестовую базу данных

## Получение API ключей

### OpenAI
1. Перейдите на https://platform.openai.com/api-keys
2. Создайте новый API ключ
3. Скопируйте ключ в `.env`: `OPENAI_API_KEY=sk-...`

### Anthropic (Claude)
1. Перейдите на https://console.anthropic.com/
2. Создайте новый API ключ
3. Скопируйте ключ в `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Локальные модели (Ollama)
1. Установите Ollama: https://ollama.ai/
2. Запустите модель: `ollama run llama2`
3. Настройте в `.env`:
   ```
   SQL_ANALYZER_LOCAL_LLM_URL=http://localhost:11434
   SQL_ANALYZER_LOCAL_LLM_MODEL=llama2
   ```

## Проверка настройки

```bash
# Запустите приложение
./run_streamlit.py

# В интерфейсе перейдите на вкладку "SQL Анализ"
# Включите "AI-рекомендации" и выберите провайдера
```

## Безопасность

- ✅ Файл `.env` добавлен в `.gitignore`
- ✅ API ключи не попадут в git
- ✅ Используйте тестовую базу данных для тестирования

## Поддерживаемые провайдеры

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-sonnet, Claude-3-haiku
- **Локальные**: Ollama, Llama2, Mistral и др.
