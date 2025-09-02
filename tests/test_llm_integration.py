"""
Тесты для модуля LLM интеграции.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from app.llm_integration import (
    LLMRecommendation, 
    LLMProvider, 
    OpenAIProvider, 
    AnthropicProvider, 
    LocalLLMProvider,
    LLMIntegration
)


class TestLLMRecommendation:
    """Тесты для структуры LLM рекомендации."""
    
    def test_llm_recommendation_creation(self):
        """Тест создания LLM рекомендации."""
        rec = LLMRecommendation(
            priority="high",
            category="query_optimization",
            description="Тестовая рекомендация",
            current_query="SELECT * FROM users",
            optimized_query="SELECT id, name FROM users",
            expected_improvement="50%",
            reasoning="Оптимизация выборки полей",
            llm_model="gpt-4",
            confidence=0.9
        )
        
        assert rec.priority == "high"
        assert rec.category == "query_optimization"
        assert rec.description == "Тестовая рекомендация"
        assert rec.current_query == "SELECT * FROM users"
        assert rec.optimized_query == "SELECT id, name FROM users"
        assert rec.expected_improvement == "50%"
        assert rec.reasoning == "Оптимизация выборки полей"
        assert rec.llm_model == "gpt-4"
        assert rec.confidence == 0.9
        assert rec.additional_suggestions == []
    
    def test_llm_recommendation_defaults(self):
        """Тест значений по умолчанию."""
        rec = LLMRecommendation()
        
        assert rec.type == "ai_recommendation"
        assert rec.priority == "medium"
        assert rec.category == "general"
        assert rec.description == ""
        assert rec.current_query == ""
        assert rec.optimized_query == ""
        assert rec.expected_improvement == ""
        assert rec.reasoning == ""
        assert rec.llm_model == ""
        assert rec.confidence == 0.0
        assert rec.additional_suggestions == []


class TestOpenAIProvider:
    """Тесты для OpenAI провайдера."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4",
            temperature=0.7
        )
    
    @pytest.mark.asyncio
    async def test_get_recommendations_success(self):
        """Тест успешного получения рекомендаций."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendations": [{
                            "priority": "high",
                            "category": "query_optimization",
                            "description": "Тест",
                            "current_query": "SELECT * FROM users",
                            "optimized_query": "SELECT id FROM users",
                            "expected_improvement": "30%",
                            "reasoning": "Оптимизация",
                            "confidence": 0.85
                        }]
                    })
                }
            }]
        }
        
        with patch('app.llm_integration.requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            recommendations = await self.provider.get_recommendations(
                "SELECT * FROM users",
                {"plan": "test"},
                None
            )
            
            assert len(recommendations) == 1
            assert recommendations[0].priority == "high"
            assert recommendations[0].category == "query_optimization"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_error(self):
        """Тест обработки ошибки."""
        with patch('app.llm_integration.requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            recommendations = await self.provider.get_recommendations(
                "SELECT * FROM users",
                {"plan": "test"},
                None
            )
            
            assert recommendations == []
    
    def test_build_analysis_prompt(self):
        """Тест построения промпта для анализа."""
        prompt = self.provider._build_analysis_prompt(
            "SELECT * FROM users",
            {"plan": "test"},
            {"schema": "test"}
        )
        
        assert "SELECT * FROM users" in prompt
        assert "plan" in prompt
        assert "schema" in prompt
        assert "recommendations" in prompt


class TestAnthropicProvider:
    """Тесты для Anthropic провайдера."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.provider = AnthropicProvider(
            api_key="test-key",
            model="claude-3-sonnet"
        )
    
    @pytest.mark.asyncio
    async def test_get_recommendations_success(self):
        """Тест успешного получения рекомендаций."""
        mock_response = {
            "content": [{
                "text": json.dumps({
                    "recommendations": [{
                        "priority": "medium",
                        "category": "index_optimization",
                        "description": "Тест",
                        "current_query": "SELECT * FROM users",
                        "optimized_query": "SELECT id FROM users",
                        "expected_improvement": "40%",
                        "reasoning": "Оптимизация",
                        "confidence": 0.8
                    }]
                })
            }]
        }
        
        with patch('app.llm_integration.requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            recommendations = await self.provider.get_recommendations(
                "SELECT * FROM users",
                {"plan": "test"},
                None
            )
            
            assert len(recommendations) == 1
            assert recommendations[0].priority == "medium"
            assert recommendations[0].category == "index_optimization"
    
    def test_build_analysis_prompt(self):
        """Тест построения промпта для анализа."""
        prompt = self.provider._build_analysis_prompt(
            "SELECT * FROM users",
            {"plan": "test"},
            {"schema": "test"}
        )
        
        assert "<system>" in prompt
        assert "<user>" in prompt
        assert "SELECT * FROM users" in prompt


class TestLocalLLMProvider:
    """Тесты для локального LLM провайдера."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.provider = LocalLLMProvider(
            base_url="http://localhost:11434",
            model="llama2"
        )
    
    @pytest.mark.asyncio
    async def test_call_local_api_ollama_success(self):
        """Тест успешного вызова Ollama API."""
        mock_response = {"response": "test response"}
        
        with patch('app.llm_integration.requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None
            
            response = await self.provider._call_local_api("test prompt")
            
            assert response == "test response"
    
    @pytest.mark.asyncio
    async def test_call_local_api_lm_studio_success(self):
        """Тест успешного вызова LM Studio API."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": "test response"
                }
            }]
        }
        
        with patch('app.llm_integration.requests.post') as mock_post:
            # Первый вызов (Ollama) завершится ошибкой
            mock_post.side_effect = [
                Exception("Ollama error"),
                Mock(json=lambda: mock_response, raise_for_status=lambda: None)
            ]
            
            response = await self.provider._call_local_api("test prompt")
            
            assert response == "test response"


class TestLLMIntegration:
    """Тесты для основного класса LLM интеграции."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.config = {
            "openai_api_key": "test-openai-key",
            "anthropic_api_key": "test-anthropic-key",
            "local_llm_url": "http://localhost:11434",
            "local_llm_model": "llama2"
        }
        
        with patch('app.llm_integration.OpenAIProvider') as mock_openai, \
             patch('app.llm_integration.AnthropicProvider') as mock_anthropic, \
             patch('app.llm_integration.LocalLLMProvider') as mock_local:
            
            mock_openai.return_value = Mock()
            mock_anthropic.return_value = Mock()
            mock_local.return_value = Mock()
            
            self.integration = LLMIntegration(self.config)
    
    def test_initialization(self):
        """Тест инициализации интеграции."""
        assert "openai" in self.integration.providers
        assert "anthropic" in self.integration.providers
        assert "local" in self.integration.providers
    
    def test_get_available_providers(self):
        """Тест получения доступных провайдеров."""
        providers = self.integration.get_available_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
        assert "local" in providers
    
    def test_is_provider_available(self):
        """Тест проверки доступности провайдера."""
        assert self.integration.is_provider_available("openai") is True
        assert self.integration.is_provider_available("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_get_recommendations_auto_provider(self):
        """Тест получения рекомендаций с автоматическим выбором провайдера."""
        mock_recommendations = [Mock()]
        self.integration.providers["openai"].get_recommendations = AsyncMock(
            return_value=mock_recommendations
        )
        
        recommendations = await self.integration.get_recommendations(
            "SELECT * FROM users",
            {"plan": "test"}
        )
        
        assert recommendations == mock_recommendations
    
    @pytest.mark.asyncio
    async def test_get_recommendations_specific_provider(self):
        """Тест получения рекомендаций с указанным провайдером."""
        mock_recommendations = [Mock()]
        self.integration.providers["anthropic"].get_recommendations = AsyncMock(
            return_value=mock_recommendations
        )
        
        recommendations = await self.integration.get_recommendations(
            "SELECT * FROM users",
            {"plan": "test"},
            provider="anthropic"
        )
        
        assert recommendations == mock_recommendations
    
    @pytest.mark.asyncio
    async def test_get_recommendations_no_providers(self):
        """Тест получения рекомендаций без доступных провайдеров."""
        self.integration.providers = {}
        
        recommendations = await self.integration.get_recommendations(
            "SELECT * FROM users",
            {"plan": "test"}
        )
        
        assert recommendations == []
    
    @pytest.mark.asyncio
    async def test_analyze_database_schema(self):
        """Тест анализа схемы БД."""
        mock_recommendations = [Mock()]
        self.integration.providers["openai"].analyze_database_schema = AsyncMock(
            return_value=mock_recommendations
        )
        
        recommendations = await self.integration.analyze_database_schema(
            {"tables": ["users", "orders"]}
        )
        
        assert recommendations == mock_recommendations
    
    @pytest.mark.asyncio
    async def test_optimize_query(self):
        """Тест оптимизации запроса."""
        mock_optimized_query = "SELECT id FROM users"
        self.integration.providers["openai"].optimize_query = AsyncMock(
            return_value=mock_optimized_query
        )
        
        optimized = await self.integration.optimize_query(
            "SELECT * FROM users",
            {"context": "test"}
        )
        
        assert optimized == mock_optimized_query


class TestLLMIntegrationNoProviders:
    """Тесты для LLM интеграции без провайдеров."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.config = {}
        self.integration = LLMIntegration(self.config)
    
    def test_initialization_no_providers(self):
        """Тест инициализации без провайдеров."""
        assert self.integration.providers == {}
    
    def test_get_available_providers_empty(self):
        """Тест получения доступных провайдеров (пустой список)."""
        providers = self.integration.get_available_providers()
        assert providers == []
    
    @pytest.mark.asyncio
    async def test_get_recommendations_no_providers(self):
        """Тест получения рекомендаций без провайдеров."""
        recommendations = await self.integration.get_recommendations(
            "SELECT * FROM users",
            {"plan": "test"}
        )
        
        assert recommendations == []
    
    @pytest.mark.asyncio
    async def test_optimize_query_no_providers(self):
        """Тест оптимизации запроса без провайдеров."""
        original_query = "SELECT * FROM users"
        optimized = await self.integration.optimize_query(
            original_query,
            {"context": "test"}
        )
        
        # Без провайдеров возвращается исходный запрос
        assert optimized == original_query


if __name__ == "__main__":
    pytest.main([__file__])
