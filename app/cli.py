"""CLI интерфейс для PostgreSQL SQL Analyzer."""

import click
import json
import sys
from typing import Optional

from .analyzer import SQLAnalyzer


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PostgreSQL SQL Analyzer - инструмент для превентивного анализа SQL-запросов."""


@cli.command()
@click.option('--sql', '-s', help='SQL-запрос для анализа')
@click.option('--file', '-f', type=click.Path(exists=True),
              help='Файл с SQL-запросом')
@click.option('--dsn', '-d', required=True,
              help='DSN подключения к PostgreSQL')
@click.option('--output', '-o', type=click.Path(),
              help='Файл для сохранения результата')
@click.option('--format',
              'output_format',
              type=click.Choice(['json',
                                 'text']),
              default='json',
              help='Формат вывода')
@click.option('--work-mem', type=int, default=4, help='work_mem в MB')
@click.option('--shared-buffers', type=int,
              default=128, help='shared_buffers в MB')
@click.option('--effective-cache-size', type=int,
              default=4, help='effective_cache_size в GB')
@click.option('--large-table-threshold', type=int,
              default=1000000, help='Порог большой таблицы')
@click.option('--expensive-query-threshold', type=float,
              default=1000.0, help='Порог дорогого запроса')
def analyze(sql: Optional[str], file: Optional[str], dsn: str,
            output: Optional[str], output_format: str, **config_options):
    """Анализирует SQL-запрос."""

    # Получаем SQL
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                sql = f.read().strip()
        except Exception as e:
            click.echo(f"Ошибка чтения файла: {e}", err=True)
            sys.exit(1)
    elif not sql:
        click.echo(
            "Необходимо указать SQL-запрос через --sql или --file",
            err=True)
        sys.exit(1)

    try:
        # Создаем анализатор
        analyzer = SQLAnalyzer(dsn)

        # Обновляем конфигурацию
        custom_config = {
            'work_mem': config_options['work_mem'],
            'shared_buffers': config_options['shared_buffers'],
            'effective_cache_size': config_options['effective_cache_size'],
            'large_table_threshold': config_options['large_table_threshold'],
            'expensive_query_threshold': config_options['expensive_query_threshold']}

        # Анализируем SQL
        click.echo("🔍 Выполняется анализ SQL...")
        result = analyzer.analyze_sql(sql, custom_config)

        # Экспортируем результат
        report = analyzer.export_analysis_report(result, output_format)

        if output:
            # Сохраняем в файл
            with open(output, 'w', encoding='utf-8') as f:
                f.write(report)
            click.echo(f"✅ Результат сохранен в {output}")
        else:
            # Выводим в stdout
            click.echo(report)

        # Статус выхода
        if not result.is_valid:
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Ошибка анализа: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--dsn', '-d', required=True,
              help='DSN подключения к PostgreSQL')
@click.option('--limit', '-l', type=int, default=20, help='Количество записей')
@click.option('--output', '-o', type=click.Path(),
              help='Файл для сохранения результата')
def stats(dsn: str, limit: int, output: Optional[str]):
    """Показывает статистику из pg_stat_statements."""

    try:
        # Создаем анализатор
        analyzer = SQLAnalyzer(dsn)

        # Получаем статистику
        click.echo("📊 Получение статистики...")
        stats_data = analyzer.get_pg_stat_statements(limit)

        if not stats_data:
            click.echo("Статистика недоступна или пуста")
            return

        # Форматируем результат
        result = {
            "total_queries": len(stats_data),
            "total_calls": sum(s['calls'] for s in stats_data),
            "total_time": sum(s['total_time'] for s in stats_data),
            "queries": stats_data
        }

        # Выводим результат
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            click.echo(f"✅ Статистика сохранена в {output}")
        else:
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"❌ Ошибка получения статистики: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(),
              help='Файл для сохранения примеров')
def examples(output: Optional[str]):
    """Показывает примеры тестовых запросов."""

    try:
        # Создаем временный анализатор для получения примеров
        # Используем фиктивный DSN, так как нам нужны только примеры
        analyzer = SQLAnalyzer("postgresql://dummy:dummy@localhost/dummy")

        # Получаем примеры
        examples_data = analyzer.get_example_queries()

        # Форматируем результат
        result = {
            "examples": examples_data,
            "total": len(examples_data)
        }

        # Выводим результат
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            click.echo(f"✅ Примеры сохранены в {output}")
        else:
            click.echo("📋 Примеры тестовых запросов:")
            click.echo()

            for i, example in enumerate(examples_data, 1):
                click.echo(f"{i}. {example['name']}")
                click.echo(f"   {example['description']}")
                click.echo(f"   SQL: {example['sql'].strip()}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ Ошибка получения примеров: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--dsn', '-d', required=True,
              help='DSN подключения к PostgreSQL')
@click.option('--work-mem', type=int, default=4, help='work_mem в MB')
@click.option('--shared-buffers', type=int,
              default=128, help='shared_buffers в MB')
@click.option('--effective-cache-size', type=int,
              default=4, help='effective_cache_size в GB')
def test(dsn: str, **config_options):
    """Тестирует анализатор на примерах."""

    try:
        # Создаем анализатор
        analyzer = SQLAnalyzer(dsn)

        # Обновляем конфигурацию
        custom_config = {
            'work_mem': config_options['work_mem'],
            'shared_buffers': config_options['shared_buffers'],
            'effective_cache_size': config_options['effective_cache_size']
        }

        # Получаем примеры
        examples_data = analyzer.get_example_queries()

        click.echo("🧪 Тестирование анализатора...")
        click.echo()

        total_tests = len(examples_data)
        passed_tests = 0

        for i, example in enumerate(examples_data, 1):
            click.echo(f"Тест {i}/{total_tests}: {example['name']}")

            try:
                # Анализируем пример
                result = analyzer.analyze_sql(example['sql'], custom_config)

                if result.is_valid:
                    click.echo("  ✅ Успешно")
                    if result.metrics:
                        click.echo(
                            f"     Время: {
                                result.metrics.estimated_time_ms:.2f} мс")
                        click.echo(
                            f"     I/O: {result.metrics.estimated_io_mb:.2f} MB")
                        click.echo(
                            f"     Рекомендации: {len(result.recommendations)}")
                    passed_tests += 1
                else:
                    click.echo(
                        f"  ❌ Ошибки валидации: {
                            result.validation_errors}")

            except Exception as e:
                click.echo(f"  ❌ Ошибка анализа: {e}")

            click.echo()

        # Итоги тестирования
        click.echo("=" * 50)
        click.echo(
            f"Результаты тестирования: {passed_tests}/{total_tests} прошли")

        if passed_tests == total_tests:
            click.echo("🎉 Все тесты прошли успешно!")
        else:
            click.echo("⚠️ Некоторые тесты не прошли")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Ошибка тестирования: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Показывает текущую конфигурацию по умолчанию."""

    try:
        from .config import get_default_config

        config_data = get_default_config()

        click.echo("⚙️ Конфигурация по умолчанию:")
        click.echo()

        for key, value in config_data.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"❌ Ошибка получения конфигурации: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
