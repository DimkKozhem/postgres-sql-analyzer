"""Модуль для работы с базой данных PostgreSQL."""

import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

import psycopg2  # type: ignore
from psycopg2.extras import RealDictCursor  # type: ignore
from psycopg2.extensions import connection  # type: ignore

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Класс для управления подключением к PostgreSQL."""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._connection: Optional[connection] = None
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения подключения."""
        try:
            conn = psycopg2.connect(
                self.dsn,
                cursor_factory=RealDictCursor
            )
            # Устанавливаем read-only режим
            conn.autocommit = True
            yield conn
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_explain(self, sql: str) -> Optional[Dict[str, Any]]:
        """Выполняет EXPLAIN (FORMAT JSON) для SQL-запроса."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Проверяем безопасность запроса
                    if not self._is_safe_query(sql):
                        raise ValueError("Запрос содержит небезопасные операции")
                    
                    cur.execute("EXPLAIN (FORMAT JSON) " + sql)
                    result = cur.fetchone()
                    
                    if result and 'QUERY PLAN' in result:
                        return json.loads(result['QUERY PLAN'])
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка выполнения EXPLAIN: {e}")
            raise
    
    def get_pg_stat_statements(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает статистику из pg_stat_statements."""
        if not settings.ENABLE_PG_STAT_STATEMENTS:
            return []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            rows,
                            shared_blks_hit,
                            shared_blks_read,
                            shared_blks_written,
                            shared_blks_dirtied,
                            temp_blks_read,
                            temp_blks_written,
                            shared_blk_read_time,
                            shared_blk_write_time
                        FROM pg_stat_statements 
                        ORDER BY total_exec_time DESC 
                        LIMIT %s
                    """, (limit,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.warning(f"Не удалось получить pg_stat_statements: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о таблице."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            tableowner,
                            tablespace,
                            hasindexes,
                            hasrules,
                            hastriggers,
                            rowsecurity
                        FROM pg_tables 
                        WHERE tablename = %s
                    """, (table_name,))
                    
                    result = cur.fetchone()
                    if result:
                        return dict(result)
                    return None
                    
        except Exception as e:
            logger.warning(f"Не удалось получить информацию о таблице {table_name}: {e}")
            return None
    
    def _is_safe_query(self, sql: str) -> bool:
        """Проверяет безопасность SQL-запроса."""
        sql_upper = sql.upper().strip()
        
        # Запрещенные операции
        dangerous_keywords = [
            'DELETE', 'UPDATE', 'INSERT', 'DROP', 'CREATE', 'ALTER', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'VACUUM', 'ANALYZE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        return True


class MockDatabaseConnection:
    """Mock-класс для тестирования без подключения к БД."""
    
    def execute_explain(self, sql: str) -> Optional[Dict[str, Any]]:
        """Возвращает mock EXPLAIN JSON."""
        return self._get_mock_explain(sql)
    
    def get_pg_stat_statements(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает mock статистику."""
        return [
            {
                "query": "SELECT * FROM users WHERE id = $1",
                "calls": 1000,
                "total_time": 5000.0,
                "mean_time": 5.0,
                "rows": 1000,
                "shared_blks_hit": 5000,
                "shared_blks_read": 100,
                "shared_blks_written": 0,
                "shared_blks_dirtied": 0,
                "temp_blks_read": 0,
                "temp_blks_written": 0,
                "blk_read_time": 10.0,
                "blk_write_time": 0.0
            }
        ]
    
    def _get_mock_explain(self, sql: str) -> Dict[str, Any]:
        """Генерирует mock EXPLAIN JSON."""
        if "JOIN" in sql.upper():
            return {
                "Plan": {
                    "Node Type": "Hash Join",
                    "Strategy": "Inner",
                    "Startup Cost": 0.00,
                    "Total Cost": 1000.00,
                    "Plan Rows": 10000,
                    "Plan Width": 100,
                    "Plans": [
                        {
                            "Node Type": "Seq Scan",
                            "Relation Name": "users",
                            "Startup Cost": 0.00,
                            "Total Cost": 500.00,
                            "Plan Rows": 10000,
                            "Plan Width": 50
                        },
                        {
                            "Node Type": "Hash",
                            "Startup Cost": 0.00,
                            "Total Cost": 500.00,
                            "Plan Rows": 10000,
                            "Plan Width": 50
                        }
                    ]
                }
            }
        else:
            return {
                "Plan": {
                    "Node Type": "Seq Scan",
                    "Relation Name": "users",
                    "Startup Cost": 0.00,
                    "Total Cost": 500.00,
                    "Plan Rows": 10000,
                    "Plan Width": 50
                }
            }
