#!/usr/bin/env python3
"""Скрипт для тестирования подключения к базе данных через SSH."""

import sys
import os
import logging

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.ssh_tunnel import test_ssh_connection, test_db_connection, ssh_tunnel_context
from app.database import create_database_connection, get_connection_for_user

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ssh_tunnel():
    """Тестирует SSH туннель."""
    logger.info("=== Тестирование SSH туннеля ===")
    
    if not settings.SSH_HOST:
        logger.warning("SSH_HOST не настроен, пропускаем тест SSH")
        return False
    
    if test_ssh_connection():
        logger.info("✅ SSH подключение успешно")
        return True
    else:
        logger.error("❌ SSH подключение не удалось")
        return False


def test_database_connection():
    """Тестирует подключение к базе данных."""
    logger.info("=== Тестирование подключения к базе данных ===")
    
    try:
        # Тестируем основное подключение
        db_conn = create_database_connection()
        
        # Выполняем простой запрос
        with db_conn.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                logger.info(f"✅ Подключение к PostgreSQL успешно")
                logger.info(f"Версия: {version[0] if version else 'Неизвестно'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def test_different_users():
    """Тестирует подключения с разными пользователями."""
    logger.info("=== Тестирование подключений с разными пользователями ===")
    
    users = [
        ("default", "readonly_user"),
        ("admin", "admin_user"),
        ("super", "postgres")
    ]
    
    for user_type, user_name in users:
        try:
            logger.info(f"Тестирование пользователя: {user_name}")
            db_conn = get_connection_for_user(user_type)
            
            with db_conn.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_user;")
                    current_user = cur.fetchone()
                    logger.info(f"✅ Пользователь {user_name}: {current_user[0] if current_user else 'Неизвестно'}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка для пользователя {user_name}: {e}")


def test_ssh_tunnel_with_db():
    """Тестирует SSH туннель с подключением к базе данных."""
    logger.info("=== Тестирование SSH туннеля с БД ===")
    
    if not settings.AUTO_CREATE_SSH_TUNNEL:
        logger.info("AUTO_CREATE_SSH_TUNNEL отключен, пропускаем тест")
        return True
    
    try:
        with ssh_tunnel_context() as tunnel:
            if tunnel.is_tunnel_active():
                logger.info("✅ SSH туннель активен")
                
                # Тестируем подключение через туннель
                db_conn = create_database_connection()
                with db_conn.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT inet_server_addr(), inet_server_port();")
                        result = cur.fetchone()
                        logger.info(f"✅ Подключение через туннель успешно")
                        logger.info(f"Сервер: {result[0] if result else 'Неизвестно'}, Порт: {result[1] if result else 'Неизвестно'}")
                
                return True
            else:
                logger.error("❌ SSH туннель не активен")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка SSH туннеля с БД: {e}")
        return False


def main():
    """Основная функция тестирования."""
    logger.info("🚀 Начинаем тестирование подключений")
    logger.info(f"Настройки:")
    logger.info(f"  DB_HOST: {settings.DB_HOST}")
    logger.info(f"  DB_PORT: {settings.DB_PORT}")
    logger.info(f"  DB_USER: {settings.DB_USER}")
    logger.info(f"  SSH_HOST: {settings.SSH_HOST}")
    logger.info(f"  SSH_USER: {settings.SSH_USER}")
    logger.info(f"  AUTO_CREATE_SSH_TUNNEL: {settings.AUTO_CREATE_SSH_TUNNEL}")
    
    results = []
    
    # Тестируем SSH
    if settings.SSH_HOST:
        results.append(test_ssh_tunnel())
    
    # Тестируем подключение к БД
    results.append(test_database_connection())
    
    # Тестируем разных пользователей
    test_different_users()
    
    # Тестируем SSH туннель с БД
    if settings.AUTO_CREATE_SSH_TUNNEL:
        results.append(test_ssh_tunnel_with_db())
    
    # Итоги
    logger.info("=== ИТОГИ ТЕСТИРОВАНИЯ ===")
    if all(results):
        logger.info("🎉 Все тесты прошли успешно!")
        return 0
    else:
        logger.error("💥 Некоторые тесты не прошли")
        return 1


if __name__ == "__main__":
    sys.exit(main())
