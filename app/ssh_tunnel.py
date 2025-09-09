"""Модуль для создания SSH туннелей к базе данных PostgreSQL."""

import os
import subprocess
import time
import logging
import socket
from typing import Optional
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)


def _is_port_available(port: int) -> bool:
    """Проверяет, свободен ли порт."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def _kill_process_on_port(port: int) -> bool:
    """Убивает процесс, занимающий порт."""
    try:
        # Находим процесс, занимающий порт
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    subprocess.run(['kill', '-9', pid.strip()], timeout=5)
                    logger.info(f"Убит процесс {pid} на порту {port}")
            return True
    except Exception as e:
        logger.warning(f"Не удалось освободить порт {port}: {e}")
    
    return False


class SSHTunnel:
    """Класс для управления SSH туннелями."""
    
    def __init__(self) -> None:
        self.tunnel_process: Optional[subprocess.Popen] = None
        self.local_port: Optional[int] = None
    
    def create_tunnel(self, remote_host: str, remote_port: int,
                      local_port: int, ssh_host: str, ssh_user: str,
                      ssh_key_path: str) -> bool:
        """Создает SSH туннель."""
        try:
            # Расширяем путь к SSH ключу
            ssh_key_path = os.path.expanduser(ssh_key_path)
            
            # Проверяем существование SSH ключа
            if not os.path.exists(ssh_key_path):
                logger.error(f"SSH ключ не найден: {ssh_key_path}")
                return False
            
            # Команда для создания SSH туннеля
            cmd = [
                'ssh',
                '-N',  # Не выполнять удаленные команды
                '-L', f'{local_port}:{remote_host}:{remote_port}',  # Локальный порт -> удаленный хост:порт
                '-o', 'StrictHostKeyChecking=yes',  # Проверять host key для безопасности
                '-o', 'UserKnownHostsFile=~/.ssh/known_hosts',  # Сохранять host key
                '-o', 'ServerAliveInterval=60',  # Keep-alive
                '-o', 'ServerAliveCountMax=3',  # Максимум попыток keep-alive
                '-i', ssh_key_path,  # Путь к приватному ключу
                f'{ssh_user}@{ssh_host}'
            ]
            
            logger.info(f"Создание SSH туннеля: {ssh_user}@{ssh_host} -> localhost:{local_port}")
            
            # Проверяем, свободен ли порт
            if not _is_port_available(local_port):
                logger.warning(f"Порт {local_port} занят, пытаемся освободить...")
                _kill_process_on_port(local_port)
                time.sleep(1)  # Ждем освобождения порта
                
                if not _is_port_available(local_port):
                    raise RuntimeError(f"Не удалось освободить порт {local_port}")
            
            # Запускаем SSH туннель в фоновом режиме
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.local_port = local_port
            
            # Ждем немного, чтобы туннель успел установиться
            time.sleep(2)
            
            # Проверяем, что процесс еще работает
            if self.tunnel_process.poll() is None:
                logger.info(f"SSH туннель успешно создан на порту {local_port}")
                return True
            else:
                stdout, stderr = self.tunnel_process.communicate()
                logger.error(f"Ошибка создания SSH туннеля: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при создании SSH туннеля: {e}")
            return False
    
    def close_tunnel(self) -> None:
        """Закрывает SSH туннель."""
        if self.tunnel_process and self.tunnel_process.poll() is None:
            logger.info("Закрытие SSH туннеля")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Принудительное завершение SSH туннеля")
                self.tunnel_process.kill()
            self.tunnel_process = None
            self.local_port = None
    
    def is_tunnel_active(self) -> bool:
        """Проверяет, активен ли туннель."""
        return (self.tunnel_process is not None and
                self.tunnel_process.poll() is None)
    
    def get_local_port(self) -> Optional[int]:
        """Возвращает локальный порт туннеля."""
        return self.local_port


# Глобальный экземпляр туннеля
ssh_tunnel = SSHTunnel()


@contextmanager
def ssh_tunnel_context():
    """Контекстный менеджер для SSH туннеля."""
    tunnel_created = False
    
    try:
        # Создаем туннель, если настроено автоматическое создание
        if settings.AUTO_CREATE_SSH_TUNNEL and settings.SSH_HOST:
            if ssh_tunnel.create_tunnel(
                remote_host='localhost',  # PostgreSQL на удаленном сервере
                remote_port=5433,  # Порт PostgreSQL на сервере
                local_port=settings.DB_PORT,  # Локальный порт из настроек
                ssh_host=settings.SSH_HOST,
                ssh_user=settings.SSH_USER,
                ssh_key_path=settings.SSH_KEY_PATH
            ):
                tunnel_created = True
                logger.info("SSH туннель создан успешно")
            else:
                logger.error("Не удалось создать SSH туннель")
                raise ConnectionError("Не удалось создать SSH туннель")
        
        yield ssh_tunnel
        
    finally:
        # Закрываем туннель, если мы его создавали
        if tunnel_created:
            ssh_tunnel.close_tunnel()


def get_db_connection_string() -> str:
    """Возвращает строку подключения к базе данных."""
    if settings.AUTO_CREATE_SSH_TUNNEL and ssh_tunnel.is_tunnel_active():
        # Используем локальный порт туннеля
        host = 'localhost'
        port = ssh_tunnel.get_local_port() or settings.DB_PORT
    else:
        # Прямое подключение
        host = settings.DB_HOST
        port = settings.DB_PORT
    
    return f"host={host} port={port} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}"


def test_ssh_connection() -> bool:
    """Тестирует SSH подключение."""
    if not settings.SSH_HOST or not settings.SSH_USER:
        logger.warning("SSH настройки не заданы")
        return False
    
    try:
        ssh_key_path = os.path.expanduser(settings.SSH_KEY_PATH)
        
        if not os.path.exists(ssh_key_path):
            logger.error(f"SSH ключ не найден: {ssh_key_path}")
            return False
        
        # Тестируем SSH подключение
        cmd = [
            'ssh',
            '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=yes',
            '-o', 'UserKnownHostsFile=~/.ssh/known_hosts',
            '-i', ssh_key_path,
            f'{settings.SSH_USER}@{settings.SSH_HOST}',
            'echo "SSH connection test successful"'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.SSH_TIMEOUT)
        
        if result.returncode == 0:
            logger.info("SSH подключение успешно протестировано")
            return True
        else:
            logger.error(f"Ошибка SSH подключения: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании SSH подключения: {e}")
        return False


def test_db_connection() -> bool:
    """Тестирует подключение к базе данных."""
    try:
        import psycopg2
        
        conn_string = get_db_connection_string()
        conn = psycopg2.connect(conn_string)
        conn.close()
        
        logger.info("Подключение к базе данных успешно протестировано")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False
