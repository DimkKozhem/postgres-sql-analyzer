"""Тесты для основного модуля анализатора."""

import pytest
import json
from unittest.mock import Mock, patch

from app.analyzer import SQLAnalyzer, AnalysisResult
from app.plan_parser import QueryMetrics


class TestSQLAnalyzer:
    """Тесты для класса SQLAnalyzer."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.analyzer = SQLAnalyzer(mock_mode=True)
    
    def test_init_mock_mode(self):
        """Тест инициализации в mock режиме."""
        analyzer = SQLAnalyzer(mock_mode=True)
        assert analyzer.mock_mode is True
        assert analyzer.dsn is None
        assert hasattr(analyzer.db_connection, 'execute_explain')
    
    def test_init_with_dsn(self):
        """Тест инициализации с DSN."""
        dsn = "postgresql://user:pass@localhost:5432/db"
        analyzer = SQLAnalyzer(dsn=dsn, mock_mode=False)
        assert analyzer.mock_mode is False
        assert analyzer.dsn == dsn
    
    def test_analyze_sql_valid(self):
        """Тест анализа валидного SQL."""
        sql = "SELECT * FROM users LIMIT 10;"
        result = self.analyzer.analyze_sql(sql)
        
        assert isinstance(result, AnalysisResult)
        assert result.sql == sql
        assert result.is_valid is True
        assert len(result.validation_errors) == 0
        assert result.explain_json is not None
        assert result.metrics is not None
        assert isinstance(result.metrics, QueryMetrics)
    
    def test_analyze_sql_invalid(self):
        """Тест анализа невалидного SQL."""
        sql = "DELETE FROM users;"
        result = self.analyzer.analyze_sql(sql)
        
        assert isinstance(result, AnalysisResult)
        assert result.sql == sql
        assert result.is_valid is False
        assert len(result.validation_errors) > 0
    
    def test_analyze_sql_with_custom_config(self):
        """Тест анализа с пользовательской конфигурацией."""
        sql = "SELECT * FROM users;"
        custom_config = {'work_mem': 64, 'large_table_threshold': 500000}
        
        result = self.analyzer.analyze_sql(sql, custom_config)
        
        assert result.config_used['work_mem'] == 64
        assert result.config_used['large_table_threshold'] == 500000
    
    def test_get_pg_stat_statements(self):
        """Тест получения статистики pg_stat_statements."""
        stats = self.analyzer.get_pg_stat_statements(limit=10)
        
        assert isinstance(stats, list)
        assert len(stats) > 0
        assert 'query' in stats[0]
        assert 'calls' in stats[0]
        assert 'total_time' in stats[0]
    
    def test_update_config(self):
        """Тест обновления конфигурации."""
        new_config = {'work_mem': 128, 'shared_buffers': 256}
        self.analyzer.update_config(new_config)
        
        assert self.analyzer.config['work_mem'] == 128
        assert self.analyzer.config['shared_buffers'] == 256
    
    def test_get_config(self):
        """Тест получения конфигурации."""
        config = self.analyzer.get_config()
        
        assert isinstance(config, dict)
        assert 'work_mem' in config
        assert 'shared_buffers' in config
        assert 'effective_cache_size' in config
    
    def test_get_example_queries(self):
        """Тест получения примеров запросов."""
        examples = self.analyzer.get_example_queries()
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        
        for example in examples:
            assert 'name' in example
            assert 'description' in example
            assert 'sql' in example
    
    def test_analyze_example_query(self):
        """Тест анализа примера запроса."""
        result = self.analyzer.analyze_example_query(0)
        
        assert isinstance(result, AnalysisResult)
        assert result.is_valid is True
        assert result.explain_json is not None
    
    def test_analyze_example_query_invalid_index(self):
        """Тест анализа примера с неверным индексом."""
        with pytest.raises(ValueError, match="Неверный индекс примера"):
            self.analyzer.analyze_example_query(999)


class TestAnalysisResult:
    """Тесты для класса AnalysisResult."""
    
    def test_analysis_result_creation(self):
        """Тест создания результата анализа."""
        result = AnalysisResult(
            sql="SELECT * FROM users;",
            is_valid=True,
            validation_errors=[],
            explain_json={"Plan": {"Node Type": "Seq Scan"}},
            plan_summary={"total_nodes": 1},
            metrics=Mock(spec=QueryMetrics),
            recommendations=[],
            analysis_time=0.1,
            config_used={"work_mem": 4}
        )
        
        assert result.sql == "SELECT * FROM users;"
        assert result.is_valid is True
        assert len(result.validation_errors) == 0
        assert result.explain_json is not None
        assert result.plan_summary is not None
        assert result.metrics is not None
        assert len(result.recommendations) == 0
        assert result.analysis_time == 0.1
        assert result.config_used["work_mem"] == 4


class TestExport:
    """Тесты для экспорта результатов."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.analyzer = SQLAnalyzer(mock_mode=True)
        self.result = self.analyzer.analyze_sql("SELECT * FROM users;")
    
    def test_export_json(self):
        """Тест экспорта в JSON."""
        json_report = self.analyzer.export_analysis_report(self.result, "json")
        
        assert isinstance(json_report, str)
        data = json.loads(json_report)
        
        assert 'sql' in data
        assert 'is_valid' in data
        assert 'metrics' in data
        assert 'recommendations' in data
    
    def test_export_text(self):
        """Тест экспорта в текстовом формате."""
        text_report = self.analyzer.export_analysis_report(self.result, "text")
        
        assert isinstance(text_report, str)
        assert "ОТЧЕТ ПО АНАЛИЗУ SQL-ЗАПРОСА" in text_report
        # Проверяем наличие рекомендаций только если они есть
        if self.result.recommendations:
            assert "РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ" in text_report
    
    def test_export_invalid_format(self):
        """Тест экспорта в неверном формате."""
        with pytest.raises(ValueError, match="Неподдерживаемый формат"):
            self.analyzer.export_analysis_report(self.result, "invalid")


class TestIntegration:
    """Интеграционные тесты."""
    
    def test_full_analysis_workflow(self):
        """Тест полного рабочего процесса анализа."""
        analyzer = SQLAnalyzer(mock_mode=True)
        
        # Анализируем SQL
        sql = "SELECT u.name, o.total_amount FROM users u JOIN orders o ON u.id = o.user_id;"
        result = analyzer.analyze_sql(sql)
        
        # Проверяем результат
        assert result.is_valid
        assert result.explain_json is not None
        assert result.metrics is not None
        assert len(result.recommendations) > 0
        
        # Экспортируем результаты
        json_report = analyzer.export_analysis_report(result, "json")
        text_report = analyzer.export_analysis_report(result, "text")
        
        assert len(json_report) > 0
        assert len(text_report) > 0
        
        # Проверяем конфигурацию
        config = analyzer.get_config()
        assert 'work_mem' in config
        assert 'shared_buffers' in config
    
    def test_configuration_updates(self):
        """Тест обновления конфигурации и повторного анализа."""
        analyzer = SQLAnalyzer(mock_mode=True)
        
        # Начальная конфигурация
        initial_config = analyzer.get_config()
        initial_work_mem = initial_config['work_mem']
        
        # Обновляем конфигурацию
        new_config = {'work_mem': initial_work_mem * 2}
        analyzer.update_config(new_config)
        
        # Проверяем обновление
        updated_config = analyzer.get_config()
        assert updated_config['work_mem'] == initial_work_mem * 2
        
        # Анализируем с новой конфигурацией
        sql = "SELECT * FROM users ORDER BY name;"
        result = analyzer.analyze_sql(sql, new_config)
        
        assert result.config_used['work_mem'] == initial_work_mem * 2


if __name__ == "__main__":
    pytest.main([__file__])
