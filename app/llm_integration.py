"""
Модуль интеграции с внешними LLM для AI-рекомендаций по оптимизации БД.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class LLMRecommendation:
    """Структура AI-рекомендации."""
    type: str = "ai_recommendation"
    priority: str = "medium"
    category: str = "general"
    description: str = ""
    current_query: str = ""
    optimized_query: str = ""
    expected_improvement: str = ""
    reasoning: str = ""
    llm_model: str = ""
    confidence: float = 0.0
    additional_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.additional_suggestions is None:
            self.additional_suggestions = []

class LLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров."""
    
    @abstractmethod
    async def get_recommendations(self, sql_query: str, execution_plan: Dict, 
                                db_schema: Optional[Dict] = None) -> List[LLMRecommendation]:
        """Получить AI-рекомендации для SQL запроса."""
        pass
    
    @abstractmethod
    async def analyze_database_schema(self, schema: Dict) -> List[LLMRecommendation]:
        """Анализ схемы БД и генерация рекомендаций."""
        pass
    
    @abstractmethod
    async def optimize_query(self, sql_query: str, context: Dict) -> str:
        """Оптимизация SQL запроса с помощью AI."""
        pass

class OpenAIProvider(LLMProvider):
    """Интеграция с OpenAI GPT."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = "https://api.openai.com/v1"
        
    async def get_recommendations(self, sql_query: str, execution_plan: Dict, 
                                db_schema: Optional[Dict] = None) -> List[LLMRecommendation]:
        """Получить рекомендации от OpenAI GPT."""
        try:
            prompt = self._build_analysis_prompt(sql_query, execution_plan, db_schema)
            
            response = await self._call_openai_api(prompt)
            
            return self._parse_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций от OpenAI: {e}")
            return []
    
    async def analyze_database_schema(self, schema: Dict) -> List[LLMRecommendation]:
        """Анализ схемы БД с помощью OpenAI."""
        try:
            prompt = self._build_schema_analysis_prompt(schema)
            
            response = await self._call_openai_api(prompt)
            
            return self._parse_schema_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка анализа схемы БД OpenAI: {e}")
            return []
    
    async def optimize_query(self, sql_query: str, context: Dict) -> str:
        """Оптимизация SQL запроса OpenAI."""
        try:
            prompt = self._build_optimization_prompt(sql_query, context)
            
            response = await self._call_openai_api(prompt)
            
            return self._extract_optimized_query(response)
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации запроса OpenAI: {e}")
            return sql_query
    
    def _build_analysis_prompt(self, sql_query: str, execution_plan: Dict, 
                              db_schema: Optional[Dict] = None) -> str:
        """Построение промпта для анализа SQL."""
        prompt = f"""
        Ты - эксперт по оптимизации PostgreSQL. Проанализируй SQL запрос и план выполнения.
        
        SQL запрос:
        {sql_query}
        
        План выполнения:
        {json.dumps(execution_plan, indent=2, ensure_ascii=False)}
        """
        
        if db_schema:
            prompt += f"\nСхема БД:\n{json.dumps(db_schema, indent=2, ensure_ascii=False)}"
        
        prompt += """
        
        Предоставь рекомендации по оптимизации в формате JSON:
        {
          "recommendations": [
            {
              "priority": "high|medium|low",
              "category": "query_optimization|index_optimization|schema_optimization",
              "description": "Описание проблемы",
              "current_query": "Текущий запрос",
              "optimized_query": "Оптимизированный запрос",
              "expected_improvement": "Ожидаемое улучшение",
              "reasoning": "Объяснение рекомендации",
              "confidence": 0.85
            }
          ]
        }
        """
        
        return prompt
    
    def _build_schema_analysis_prompt(self, schema: Dict) -> str:
        """Построение промпта для анализа схемы БД."""
        return f"""
        Ты - эксперт по проектированию БД. Проанализируй схему PostgreSQL.
        
        Схема БД:
        {json.dumps(schema, indent=2, ensure_ascii=False)}
        
        Предоставь рекомендации по улучшению схемы в формате JSON:
        {{
          "recommendations": [
            {{
              "priority": "high|medium|low",
              "category": "normalization|data_types|indexing|partitioning",
              "description": "Описание улучшения",
              "suggestion": "Конкретное предложение",
              "expected_benefit": "Ожидаемая польза",
              "reasoning": "Объяснение",
              "confidence": 0.85
            }}
          ]
        }}
        """
    
    def _build_optimization_prompt(self, sql_query: str, context: Dict) -> str:
        """Построение промпта для оптимизации запроса."""
        return f"""
        Ты - эксперт по SQL. Оптимизируй следующий запрос:
        
        Запрос:
        {sql_query}
        
        Контекст:
        {json.dumps(context, indent=2, ensure_ascii=False)}
        
        Верни только оптимизированный SQL запрос без дополнительных комментариев.
        """
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Вызов OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def _parse_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций из ответа OpenAI."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "general"),
                    description=rec.get("description", ""),
                    current_query=rec.get("current_query", ""),
                    optimized_query=rec.get("optimized_query", ""),
                    expected_improvement=rec.get("expected_improvement", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0)
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций OpenAI: {e}")
            return []
    
    def _parse_schema_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций по схеме БД."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "schema_optimization"),
                    description=rec.get("description", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0),
                    additional_suggestions=[rec.get("suggestion", "")]
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций по схеме: {e}")
            return []
    
    def _extract_optimized_query(self, response: str) -> str:
        """Извлечение оптимизированного запроса из ответа."""
        # Убираем лишние символы и форматирование
        query = response.strip()
        if query.startswith("```sql"):
            query = query[7:]
        if query.endswith("```"):
            query = query[:-3]
        
        return query.strip()

class AnthropicProvider(LLMProvider):
    """Интеграция с Anthropic Claude."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        
    async def get_recommendations(self, sql_query: str, execution_plan: Dict, 
                                db_schema: Optional[Dict] = None) -> List[LLMRecommendation]:
        """Получить рекомендации от Anthropic Claude."""
        try:
            prompt = self._build_analysis_prompt(sql_query, execution_plan, db_schema)
            
            response = await self._call_anthropic_api(prompt)
            
            return self._parse_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций от Anthropic: {e}")
            return []
    
    async def analyze_database_schema(self, schema: Dict) -> List[LLMRecommendation]:
        """Анализ схемы БД с помощью Anthropic."""
        try:
            prompt = self._build_schema_analysis_prompt(schema)
            
            response = await self._call_anthropic_api(prompt)
            
            return self._parse_schema_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка анализа схемы БД Anthropic: {e}")
            return []
    
    async def optimize_query(self, sql_query: str, context: Dict) -> str:
        """Оптимизация SQL запроса Anthropic."""
        try:
            prompt = self._build_optimization_prompt(sql_query, context)
            
            response = await self._call_anthropic_api(prompt)
            
            return self._extract_optimized_query(response)
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации запроса Anthropic: {e}")
            return sql_query
    
    def _build_analysis_prompt(self, sql_query: str, execution_plan: Dict, 
                              db_schema: Optional[Dict] = None) -> str:
        """Построение промпта для анализа SQL."""
        prompt = f"""
        <system>
        Ты - эксперт по оптимизации PostgreSQL. Проанализируй SQL запрос и план выполнения.
        </system>
        
        <user>
        SQL запрос:
        {sql_query}
        
        План выполнения:
        {json.dumps(execution_plan, indent=2, ensure_ascii=False)}
        """
        
        if db_schema:
            prompt += f"\nСхема БД:\n{json.dumps(db_schema, indent=2, ensure_ascii=False)}"
        
        prompt += """
        
        Предоставь рекомендации по оптимизации в формате JSON:
        {
          "recommendations": [
            {
              "priority": "high|medium|low",
              "category": "query_optimization|index_optimization|schema_optimization",
              "description": "Описание проблемы",
              "current_query": "Текущий запрос",
              "optimized_query": "Оптимизированный запрос",
              "expected_improvement": "Ожидаемое улучшение",
              "reasoning": "Объяснение рекомендации",
              "confidence": 0.85
            }
          ]
        }
        </user>
        """
        
        return prompt
    
    def _build_schema_analysis_prompt(self, schema: Dict) -> str:
        """Построение промпта для анализа схемы БД."""
        return f"""
        <system>
        Ты - эксперт по проектированию БД. Проанализируй схему PostgreSQL.
        </system>
        
        <user>
        Схема БД:
        {json.dumps(schema, indent=2, ensure_ascii=False)}
        
        Предоставь рекомендации по улучшению схемы в формате JSON:
        {{
          "recommendations": [
            {{
              "priority": "high|medium|low",
              "category": "normalization|data_types|indexing|partitioning",
              "description": "Описание улучшения",
              "suggestion": "Конкретное предложение",
              "expected_benefit": "Ожидаемая польза",
              "reasoning": "Объяснение",
              "confidence": 0.85
            }}
          ]
        }}
        </user>
        """
    
    def _build_optimization_prompt(self, sql_query: str, context: Dict) -> str:
        """Построение промпта для оптимизации запроса."""
        return f"""
        <system>
        Ты - эксперт по SQL. Оптимизируй следующий запрос.
        </system>
        
        <user>
        Запрос:
        {sql_query}
        
        Контекст:
        {json.dumps(context, indent=2, ensure_ascii=False)}
        
        Верни только оптимизированный SQL запрос без дополнительных комментариев.
        </user>
        """
    
    async def _call_anthropic_api(self, prompt: str) -> str:
        """Вызов Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        
        return response.json()["content"][0]["text"]
    
    def _parse_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций из ответа Anthropic."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "general"),
                    description=rec.get("description", ""),
                    current_query=rec.get("current_query", ""),
                    optimized_query=rec.get("optimized_query", ""),
                    expected_improvement=rec.get("expected_improvement", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0)
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций Anthropic: {e}")
            return []
    
    def _parse_schema_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций по схеме БД."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "schema_optimization"),
                    description=rec.get("description", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0),
                    additional_suggestions=[rec.get("suggestion", "")]
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций по схеме: {e}")
            return []
    
    def _extract_optimized_query(self, response: str) -> str:
        """Извлечение оптимизированного запроса из ответа."""
        # Убираем лишние символы и форматирование
        query = response.strip()
        if query.startswith("```sql"):
            query = query[7:]
        if query.endswith("```"):
            query = query[:-3]
        
        return query.strip()

class LocalLLMProvider(LLMProvider):
    """Интеграция с локальными LLM (Ollama, LM Studio)."""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        
    async def get_recommendations(self, sql_query: str, execution_plan: Dict, 
                                db_schema: Optional[Dict] = None) -> List[LLMRecommendation]:
        """Получить рекомендации от локальной LLM."""
        try:
            prompt = self._build_analysis_prompt(sql_query, execution_plan, db_schema)
            
            response = await self._call_local_api(prompt)
            
            return self._parse_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций от локальной LLM: {e}")
            return []
    
    async def analyze_database_schema(self, schema: Dict) -> List[LLMRecommendation]:
        """Анализ схемы БД с помощью локальной LLM."""
        try:
            prompt = self._build_schema_analysis_prompt(schema)
            
            response = await self._call_local_api(prompt)
            
            return self._parse_schema_recommendations(response)
            
        except Exception as e:
            logger.error(f"Ошибка анализа схемы БД локальной LLM: {e}")
            return []
    
    async def optimize_query(self, sql_query: str, context: Dict) -> str:
        """Оптимизация SQL запроса локальной LLM."""
        try:
            prompt = self._build_optimization_prompt(sql_query, context)
            
            response = await self._call_local_api(prompt)
            
            return self._extract_optimized_query(response)
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации запроса локальной LLM: {e}")
            return sql_query
    
    def _build_analysis_prompt(self, sql_query: str, execution_plan: Dict, 
                              db_schema: Optional[Dict] = None) -> str:
        """Построение промпта для анализа SQL."""
        prompt = f"""
        Ты - эксперт по оптимизации PostgreSQL. Проанализируй SQL запрос и план выполнения.
        
        SQL запрос:
        {sql_query}
        
        План выполнения:
        {json.dumps(execution_plan, indent=2, ensure_ascii=False)}
        """
        
        if db_schema:
            prompt += f"\nСхема БД:\n{json.dumps(db_schema, indent=2, ensure_ascii=False)}"
        
        prompt += """
        
        Предоставь рекомендации по оптимизации в формате JSON:
        {
          "recommendations": [
            {
              "priority": "high|medium|low",
              "category": "query_optimization|index_optimization|schema_optimization",
              "description": "Описание проблемы",
              "current_query": "Текущий запрос",
              "optimized_query": "Оптимизированный запрос",
              "expected_improvement": "Ожидаемое улучшение",
              "reasoning": "Объяснение рекомендации",
              "confidence": 0.85
            }
          ]
        }
        """
        
        return prompt
    
    def _build_schema_analysis_prompt(self, schema: Dict) -> str:
        """Построение промпта для анализа схемы БД."""
        return f"""
        Ты - эксперт по проектированию БД. Проанализируй схему PostgreSQL.
        
        Схема БД:
        {json.dumps(schema, indent=2, ensure_ascii=False)}
        
        Предоставь рекомендации по улучшению схемы в формате JSON:
        {{
          "recommendations": [
            {{
              "priority": "high|medium|low",
              "category": "normalization|data_types|indexing|partitioning",
              "description": "Описание улучшения",
              "suggestion": "Конкретное предложение",
              "expected_benefit": "Ожидаемая польза",
              "reasoning": "Объяснение",
              "confidence": 0.85
            }}
          ]
        }}
        """
    
    def _build_optimization_prompt(self, sql_query: str, context: Dict) -> str:
        """Построение промпта для оптимизации запроса."""
        return f"""
        Ты - эксперт по SQL. Оптимизируй следующий запрос:
        
        Запрос:
        {sql_query}
        
        Контекст:
        {json.dumps(context, indent=2, ensure_ascii=False)}
        
        Верни только оптимизированный SQL запрос без дополнительных комментариев.
        """
    
    async def _call_local_api(self, prompt: str) -> str:
        """Вызов локального LLM API."""
        # Попробуем Ollama формат
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60
            )
            
            response.raise_for_status()
            
            return response.json()["response"]
            
        except Exception:
            # Попробуем LM Studio формат
            try:
                data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=data,
                    timeout=60
                )
                
                response.raise_for_status()
                
                return response.json()["choices"][0]["message"]["content"]
                
            except Exception as e:
                logger.error(f"Ошибка вызова локального LLM API: {e}")
                raise
    
    def _parse_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций из ответа локальной LLM."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "general"),
                    description=rec.get("description", ""),
                    current_query=rec.get("current_query", ""),
                    optimized_query=rec.get("optimized_query", ""),
                    expected_improvement=rec.get("expected_improvement", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0)
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций локальной LLM: {e}")
            return []
    
    def _parse_schema_recommendations(self, response: str) -> List[LLMRecommendation]:
        """Парсинг рекомендаций по схеме БД."""
        try:
            data = json.loads(response)
            recommendations = []
            
            for rec in data.get("recommendations", []):
                recommendation = LLMRecommendation(
                    priority=rec.get("priority", "medium"),
                    category=rec.get("category", "schema_optimization"),
                    description=rec.get("description", ""),
                    reasoning=rec.get("reasoning", ""),
                    llm_model=self.model,
                    confidence=rec.get("confidence", 0.0),
                    additional_suggestions=[rec.get("suggestion", "")]
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка парсинга рекомендаций по схеме: {e}")
            return []
    
    def _extract_optimized_query(self, response: str) -> str:
        """Извлечение оптимизированного запроса из ответа."""
        # Убираем лишние символы и форматирование
        query = response.strip()
        if query.startswith("```sql"):
            query = query[7:]
        if query.endswith("```"):
            query = query[:-3]
        
        return query.strip()

class LLMIntegration:
    """Основной класс интеграции с LLM."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Инициализация LLM провайдеров."""
        # OpenAI
        if self.config.get("openai_api_key"):
            self.providers["openai"] = OpenAIProvider(
                api_key=self.config["openai_api_key"],
                model=self.config.get("openai_model", "gpt-4"),
                temperature=self.config.get("openai_temperature", 0.7)
            )
        
        # Anthropic
        if self.config.get("anthropic_api_key"):
            self.providers["anthropic"] = AnthropicProvider(
                api_key=self.config["anthropic_api_key"],
                model=self.config.get("anthropic_model", "claude-3-sonnet")
            )
        
        # Локальные модели
        if self.config.get("local_llm_url") and self.config.get("local_llm_model"):
            self.providers["local"] = LocalLLMProvider(
                base_url=self.config["local_llm_url"],
                model=self.config["local_llm_model"]
            )
    
    async def get_recommendations(self, sql_query: str, execution_plan: Dict, 
                                db_schema: Optional[Dict] = None, 
                                provider: str = "auto") -> List[LLMRecommendation]:
        """Получить AI-рекомендации."""
        if not self.providers:
            logger.warning("Нет доступных LLM провайдеров")
            return []
        
        if provider == "auto":
            # Используем первый доступный провайдер
            provider = list(self.providers.keys())[0]
        
        if provider not in self.providers:
            logger.error(f"Провайдер {provider} не найден")
            return []
        
        try:
            return await self.providers[provider].get_recommendations(
                sql_query, execution_plan, db_schema
            )
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций от {provider}: {e}")
            return []
    
    async def analyze_database_schema(self, schema: Dict, 
                                    provider: str = "auto") -> List[LLMRecommendation]:
        """Анализ схемы БД с помощью AI."""
        if not self.providers:
            logger.warning("Нет доступных LLM провайдеров")
            return []
        
        if provider == "auto":
            provider = list(self.providers.keys())[0]
        
        if provider not in self.providers:
            logger.error(f"Провайдер {provider} не найден")
            return []
        
        try:
            return await self.providers[provider].analyze_database_schema(schema)
        except Exception as e:
            logger.error(f"Ошибка анализа схемы БД {provider}: {e}")
            return []
    
    async def optimize_query(self, sql_query: str, context: Dict, 
                           provider: str = "auto") -> str:
        """Оптимизация SQL запроса с помощью AI."""
        if not self.providers:
            logger.warning("Нет доступных LLM провайдеров")
            return sql_query
        
        if provider == "auto":
            provider = list(self.providers.keys())[0]
        
        if provider not in self.providers:
            logger.error(f"Провайдер {provider} не найден")
            return sql_query
        
        try:
            return await self.providers[provider].optimize_query(sql_query, context)
        except Exception as e:
            logger.error(f"Ошибка оптимизации запроса {provider}: {e}")
            return sql_query
    
    def get_available_providers(self) -> List[str]:
        """Получить список доступных провайдеров."""
        return list(self.providers.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """Проверить доступность провайдера."""
        return provider in self.providers
