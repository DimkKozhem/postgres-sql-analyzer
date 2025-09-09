"""Модуль кэширования для PostgreSQL SQL Analyzer."""

import time
import hashlib
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
from app.types import CacheConfig, CacheKey, CacheEntry

logger = logging.getLogger(__name__)


class MemoryCache:
    """Кэш в памяти."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """Получает значение из кэша."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        # Проверяем TTL
        if time.time() - timestamp > self.default_ttl:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None

        # Обновляем время доступа
        self.access_times[key] = time.time()
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохраняет значение в кэш."""
        # Очищаем старые записи если кэш переполнен
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        ttl = ttl or self.default_ttl
        self.cache[key] = (value, time.time())
        self.access_times[key] = time.time()

    def delete(self, key: str) -> bool:
        """Удаляет значение из кэша."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """Очищает весь кэш."""
        self.cache.clear()
        self.access_times.clear()

    def _evict_oldest(self) -> None:
        """Удаляет самую старую запись."""
        if not self.access_times:
            return

        oldest_key = min(
            self.access_times.keys(),
            key=lambda k: self.access_times[k])
        self.delete(oldest_key)

    def size(self) -> int:
        """Возвращает размер кэша."""
        return len(self.cache)

    def keys(self) -> list:
        """Возвращает ключи кэша."""
        return list(self.cache.keys())


class CacheManager:
    """Менеджер кэширования."""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache = MemoryCache(
            max_size=self.config.max_size,
            default_ttl=self.config.ttl
        )
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

    def get(self, key: CacheKey) -> Optional[Any]:
        """Получает значение из кэша."""
        cache_key = self._make_key(key)
        value = self.cache.get(cache_key)

        if value is not None:
            self.stats['hits'] += 1
            logger.debug(f"Cache hit for key: {cache_key}")
        else:
            self.stats['misses'] += 1
            logger.debug(f"Cache miss for key: {cache_key}")

        return value

    def set(self, key: CacheKey, value: Any,
            ttl: Optional[int] = None) -> None:
        """Сохраняет значение в кэш."""
        cache_key = self._make_key(key)
        self.cache.set(cache_key, value, ttl)
        self.stats['sets'] += 1
        logger.debug(f"Cache set for key: {cache_key}")

    def delete(self, key: CacheKey) -> bool:
        """Удаляет значение из кэша."""
        cache_key = self._make_key(key)
        result = self.cache.delete(cache_key)
        if result:
            self.stats['deletes'] += 1
            logger.debug(f"Cache delete for key: {cache_key}")
        return result

    def clear(self) -> None:
        """Очищает весь кэш."""
        self.cache.clear()
        logger.info("Cache cleared")

    def _make_key(self, key: CacheKey) -> str:
        """Создает строковый ключ из различных типов."""
        if isinstance(key, str):
            return key
        elif isinstance(key, (list, tuple)):
            return "_".join(str(k) for k in key)
        elif isinstance(key, dict):
            # Сортируем ключи для консистентности
            sorted_items = sorted(key.items())
            return "_".join(f"{k}:{v}" for k, v in sorted_items)
        else:
            return str(key)

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (
            self.stats['hits']
            / total_requests
            * 100) if total_requests > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'size': self.cache.size(),
            'max_size': self.cache.max_size
        }


def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """Декоратор для кэширования результатов функций."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Используем имя функции и аргументы
                cache_key = f"{
                    func.__name__}:{
                    hash(
                        str(args) + str(
                            sorted(
                                kwargs.items())))}"

            # Проверяем кэш
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for function {func.__name__}")
                return cached_result

            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache set for function {func.__name__}")

            return result
        return wrapper
    return decorator


def cache_invalidate(pattern: str) -> None:
    """Инвалидирует кэш по паттерну."""
    keys_to_delete = []
    for key in cache_manager.cache.keys():
        if pattern in key:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        cache_manager.delete(key)

    logger.info(
        f"Invalidated {
            len(keys_to_delete)} cache entries matching pattern: {pattern}")


class QueryCache:
    """Специализированный кэш для SQL запросов."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.query_ttl = 600  # 10 минут для SQL запросов

    def get_query_result(self, query: str, dsn: str) -> Optional[Any]:
        """Получает результат SQL запроса из кэша."""
        key = self._make_query_key(query, dsn)
        return self.cache_manager.get(key)

    def set_query_result(self, query: str, dsn: str, result: Any) -> None:
        """Сохраняет результат SQL запроса в кэш."""
        key = self._make_query_key(query, dsn)
        self.cache_manager.set(key, result, self.query_ttl)

    def invalidate_query(self, query: str, dsn: str) -> None:
        """Инвалидирует кэш для конкретного запроса."""
        key = self._make_query_key(query, dsn)
        self.cache_manager.delete(key)

    def _make_query_key(self, query: str, dsn: str) -> str:
        """Создает ключ для SQL запроса."""
        # Нормализуем запрос (убираем лишние пробелы)
        normalized_query = " ".join(query.split())
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()
        dsn_hash = hashlib.sha256(dsn.encode()).hexdigest()
        return f"query:{query_hash}:{dsn_hash}"


class DatabaseCache:
    """Специализированный кэш для данных базы данных."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.db_info_ttl = 1800  # 30 минут для информации о БД
        self.metrics_ttl = 300   # 5 минут для метрик

    def get_database_info(self, dsn: str) -> Optional[Any]:
        """Получает информацию о базе данных из кэша."""
        key = f"db_info:{hashlib.sha256(dsn.encode()).hexdigest()}"
        return self.cache_manager.get(key)

    def set_database_info(self, dsn: str, info: Any) -> None:
        """Сохраняет информацию о базе данных в кэш."""
        key = f"db_info:{hashlib.sha256(dsn.encode()).hexdigest()}"
        self.cache_manager.set(key, info, self.db_info_ttl)

    def get_metrics(self, dsn: str, metric_type: str) -> Optional[Any]:
        """Получает метрики из кэша."""
        key = f"metrics:{metric_type}:{
            hashlib.sha256(
                dsn.encode()).hexdigest()}"
        return self.cache_manager.get(key)

    def set_metrics(self, dsn: str, metric_type: str, metrics: Any) -> None:
        """Сохраняет метрики в кэш."""
        key = f"metrics:{metric_type}:{
            hashlib.sha256(
                dsn.encode()).hexdigest()}"
        self.cache_manager.set(key, metrics, self.metrics_ttl)

    def invalidate_database_cache(self, dsn: str) -> None:
        """Инвалидирует весь кэш для базы данных."""
        dsn_hash = hashlib.sha256(dsn.encode()).hexdigest()
        cache_invalidate(f":{dsn_hash}")


# Глобальные экземпляры
cache_manager = CacheManager()
query_cache = QueryCache(cache_manager)
database_cache = DatabaseCache(cache_manager)


def get_cache_stats() -> Dict[str, Any]:
    """Возвращает статистику кэша."""
    return cache_manager.get_stats()


def clear_all_cache() -> None:
    """Очищает весь кэш."""
    cache_manager.clear()


def warm_up_cache(dsn: str) -> None:
    """Прогревает кэш основными данными."""
    logger.info("Warming up cache...")

    try:
        # Кэшируем информацию о базе данных
        from app.database import DatabaseConnection
        db_conn = DatabaseConnection(dsn)

        # Получаем базовую информацию
        with db_conn.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]

                cur.execute("""
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables
                    LIMIT 10
                """)
                tables = cur.fetchall()

        # Сохраняем в кэш
        database_cache.set_database_info(dsn, {
            'version': version,
            'tables': tables
        })

        logger.info("Cache warmed up successfully")

    except Exception as e:
        logger.error(f"Error warming up cache: {e}")
