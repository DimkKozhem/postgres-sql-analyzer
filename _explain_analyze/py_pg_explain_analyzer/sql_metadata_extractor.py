## py_pg_explain_analyzer/sql_metadata_extractor.py
import psycopg
from psycopg.rows import dict_row


class TableInfoExtractor:
    """
    Что измеряется:
    1. Типы данных колонок (columns)
       - Проверяются только filter_columns.
    2. Наличие индексов по важным колонкам (indexes)
       - Возвращаются только индексы, где участвует хотя бы одна колонка из filter_columns.
    3. Оценка количества строк в таблице (estimated_rows)
       - Приближённая оценка размера таблицы.
    4. Статистика по колонкам (columns_stats)
       - Для filter_columns: n_distinct, null_frac, most_common_vals.
    5. Непокрытые индексами колонки (unindexed_columns)
       - filter_columns, для которых не найдено ни одного индекса.
    """

    def __init__(self, dsn: str):
        self.conn = psycopg.connect(dsn, row_factory=dict_row)

    @staticmethod
    def _split_table_name(table: str):
        """Разбиваем schema.table -> (schema, table). Если нет схемы, то public"""
        if "." in table:
            schema, name = table.split(".", 1)
        else:
            schema, name = "public", table
        return schema, name

    def get_table_info(self, table: str, filter_columns: list[str]):
        """Информация о таблице: только выбранные колонки, индексы, строки"""
        schema, name = self._split_table_name(table)
        info = {"columns": [], "indexes": [], "estimated_rows": None}

        with self.conn.cursor() as cur:
            # Только нужные колонки
            if filter_columns:
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                      AND column_name = ANY(%s);
                    """,
                    (schema, name, filter_columns),
                )
                info["columns"] = cur.fetchall()

            # Индексы (фильтруем только по нужным колонкам)
            cur.execute(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = %s AND tablename = %s;
                """,
                (schema, name),
            )
            all_indexes = cur.fetchall()
            if filter_columns:
                relevant_indexes = []
                for idx in all_indexes:
                    if any(col in idx["indexdef"] for col in filter_columns):
                        relevant_indexes.append(idx)
                info["indexes"] = relevant_indexes
            else:
                info["indexes"] = all_indexes

            # Оценка строк
            cur.execute(
                """
                SELECT c.reltuples::BIGINT AS estimated_rows
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = %s AND n.nspname = %s;
                """,
                (name, schema),
            )
            row = cur.fetchone()
            info["estimated_rows"] = row["estimated_rows"] if row else None

        return info

    def get_column_stats(self, table: str, column: str):
        """Собрать статистику из pg_stats только для конкретной колонки"""
        schema, name = self._split_table_name(table)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT attname, n_distinct, null_frac, most_common_vals
                FROM pg_stats
                WHERE schemaname = %s AND tablename = %s AND attname = %s;
                """,
                (schema, name, column),
            )
            return cur.fetchone()

    def analyze(self, tables_dict: dict):
        """
        Анализ на основе словаря:
        {
            'employees': {
                'alias': None,
                'filter_columns': ['hire_date', 'department']
            },
            'ads.ads': {
                'alias': 'aa',
                'filter_columns': ['price', 'status', 'updated_at']
            }
        }
        """
        result = {}

        for table, meta in tables_dict.items():
            filter_columns = meta.get("filter_columns", [])
            table_info = self.get_table_info(table, filter_columns)
            result[table] = table_info

            # статистика по колонкам
            result[table]["columns_stats"] = {}
            for col in filter_columns:
                stats = self.get_column_stats(table, col)
                if stats:
                    result[table]["columns_stats"][col] = stats

            # поиск колонок без индексов
            indexed_columns = set()
            for idx in table_info["indexes"]:
                for col in filter_columns:
                    if col in idx["indexdef"]:
                        indexed_columns.add(col)

            unindexed = [col for col in filter_columns if col not in indexed_columns]
            result[table]["unindexed_columns"] = unindexed

        return result
