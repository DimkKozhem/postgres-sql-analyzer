#!/usr/bin/env python3
"""
Модуль backup для PostgreSQL SQL Analyzer.
Обеспечивает автоматическое резервное копирование конфигураций и данных.
"""

import os
import json
import zipfile
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Менеджер резервного копирования."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Создаем поддиректории
        (self.backup_dir / "configs").mkdir(exist_ok=True)
        (self.backup_dir / "data").mkdir(exist_ok=True)
        (self.backup_dir / "logs").mkdir(exist_ok=True)

    def create_config_backup(self, config: Dict[str, Any]) -> str:
        """Создает резервную копию конфигурации."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"config_backup_{timestamp}.json"
            filepath = self.backup_dir / "configs" / filename

            # Убираем чувствительные данные
            safe_config = self._sanitize_config(config)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=2, ensure_ascii=False)

            logger.info(f"Конфигурация сохранена в {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Ошибка создания backup конфигурации: {e}")
            raise

    def create_data_backup(self, data_dir: str = "data") -> str:
        """Создает резервную копию данных."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_backup_{timestamp}.zip"
            filepath = self.backup_dir / "data" / filename

            data_path = Path(data_dir)
            if not data_path.exists():
                logger.warning(f"Директория данных {data_dir} не найдена")
                return ""

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(data_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(data_path)
                        zipf.write(file_path, arcname)

            logger.info(f"Данные сохранены в {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Ошибка создания backup данных: {e}")
            raise

    def create_logs_backup(self, logs_dir: str = "logs") -> str:
        """Создает резервную копию логов."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_backup_{timestamp}.zip"
            filepath = self.backup_dir / "logs" / filename

            logs_path = Path(logs_dir)
            if not logs_path.exists():
                logger.warning(f"Директория логов {logs_dir} не найдена")
                return ""

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(logs_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(logs_path)
                        zipf.write(file_path, arcname)

            logger.info(f"Логи сохранены в {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Ошибка создания backup логов: {e}")
            raise

    def create_full_backup(self, config: Dict[str, Any],
                           data_dir: str = "data",
                           logs_dir: str = "logs") -> str:
        """Создает полную резервную копию."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"full_backup_{timestamp}.zip"
            filepath = self.backup_dir / filename

            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Конфигурация
                safe_config = self._sanitize_config(config)
                config_data = json.dumps(safe_config, indent=2, ensure_ascii=False)
                zipf.writestr("config.json", config_data)

                # Данные
                if Path(data_dir).exists():
                    for root, dirs, files in os.walk(data_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = f"data/{file_path.relative_to(data_dir)}"
                            zipf.write(file_path, arcname)

                # Логи
                if Path(logs_dir).exists():
                    for root, dirs, files in os.walk(logs_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = f"logs/{file_path.relative_to(logs_dir)}"
                            zipf.write(file_path, arcname)

                # Метаданные
                metadata = {
                    "backup_timestamp": timestamp,
                    "backup_type": "full",
                    "config_keys": list(safe_config.keys()),
                    "data_dirs": [data_dir, logs_dir]
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

            logger.info(f"Полный backup создан: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Ошибка создания полного backup: {e}")
            raise

    def restore_config(self, backup_file: str) -> Dict[str, Any]:
        """Восстанавливает конфигурацию из backup."""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            logger.info(f"Конфигурация восстановлена из {backup_file}")
            return config

        except Exception as e:
            logger.error(f"Ошибка восстановления конфигурации: {e}")
            raise

    def restore_data(self, backup_file: str, target_dir: str = "data") -> bool:
        """Восстанавливает данные из backup."""
        try:
            target_path = Path(target_dir)
            target_path.mkdir(exist_ok=True)

            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(target_path)

            logger.info(f"Данные восстановлены в {target_dir}")
            return True

        except Exception as e:
            logger.error(f"Ошибка восстановления данных: {e}")
            raise

    def list_backups(self, backup_type: str = "all") -> List[Dict[str, Any]]:
        """Список доступных backup."""
        backups = []

        try:
            if backup_type in ["all", "configs"]:
                config_dir = self.backup_dir / "configs"
                for file in config_dir.glob("*.json"):
                    backups.append({
                        "type": "config",
                        "filename": file.name,
                        "path": str(file),
                        "size": file.stat().st_size,
                        "created": datetime.fromtimestamp(file.stat().st_ctime)
                    })

            if backup_type in ["all", "data"]:
                data_dir = self.backup_dir / "data"
                for file in data_dir.glob("*.zip"):
                    backups.append({
                        "type": "data",
                        "filename": file.name,
                        "path": str(file),
                        "size": file.stat().st_size,
                        "created": datetime.fromtimestamp(file.stat().st_ctime)
                    })

            if backup_type in ["all", "full"]:
                for file in self.backup_dir.glob("full_backup_*.zip"):
                    backups.append({
                        "type": "full",
                        "filename": file.name,
                        "path": str(file),
                        "size": file.stat().st_size,
                        "created": datetime.fromtimestamp(file.stat().st_ctime)
                    })

            # Сортируем по дате создания
            backups.sort(key=lambda x: x["created"], reverse=True)

        except Exception as e:
            logger.error(f"Ошибка получения списка backup: {e}")

        return backups

    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Удаляет старые backup файлы."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0

            for backup_type in ["configs", "data", "logs"]:
                type_dir = self.backup_dir / backup_type
                if type_dir.exists():
                    for file in type_dir.iterdir():
                        if file.is_file():
                            file_date = datetime.fromtimestamp(file.stat().st_ctime)
                            if file_date < cutoff_date:
                                file.unlink()
                                deleted_count += 1
                                logger.info(f"Удален старый backup: {file}")

            # Удаляем старые полные backup
            for file in self.backup_dir.glob("full_backup_*.zip"):
                file_date = datetime.fromtimestamp(file.stat().st_ctime)
                if file_date < cutoff_date:
                    file.unlink()
                    deleted_count += 1
                    logger.info(f"Удален старый полный backup: {file}")

            logger.info(f"Удалено {deleted_count} старых backup файлов")
            return deleted_count

        except Exception as e:
            logger.error(f"Ошибка очистки старых backup: {e}")
            return 0

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Убирает чувствительные данные из конфигурации."""
        safe_config = config.copy()

        # Список ключей с чувствительными данными
        sensitive_keys = [
            "openai_api_key", "anthropic_api_key", "password", "secret",
            "token", "key", "credential"
        ]

        for key in safe_config:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = "***HIDDEN***"

        return safe_config

    def get_backup_stats(self) -> Dict[str, Any]:
        """Получает статистику по backup."""
        try:
            total_size = 0
            backup_counts = {"configs": 0, "data": 0, "full": 0}

            for backup_type in ["configs", "data", "logs"]:
                type_dir = self.backup_dir / backup_type
                if type_dir.exists():
                    for file in type_dir.iterdir():
                        if file.is_file():
                            total_size += file.stat().st_size
                            if backup_type in backup_counts:
                                backup_counts[backup_type] += 1

            # Полные backup
            for file in self.backup_dir.glob("full_backup_*.zip"):
                total_size += file.stat().st_size
                backup_counts["full"] += 1

            return {
                "total_backups": sum(backup_counts.values()),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "backup_counts": backup_counts,
                "backup_dir": str(self.backup_dir)
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики backup: {e}")
            return {}


# Глобальный экземпляр
backup_manager = BackupManager()


def create_backup(config: Dict[str, Any] = None,
                  backup_type: str = "config") -> str:
    """Синхронная функция для создания backup."""
    try:
        if backup_type == "config" and config:
            return backup_manager.create_config_backup(config)
        elif backup_type == "data":
            return backup_manager.create_data_backup()
        elif backup_type == "logs":
            return backup_manager.create_logs_backup()
        elif backup_type == "full":
            return backup_manager.create_full_backup(config or {})
        else:
            raise ValueError(f"Неизвестный тип backup: {backup_type}")
    except Exception as e:
        logger.error(f"Ошибка создания backup: {e}")
        raise
