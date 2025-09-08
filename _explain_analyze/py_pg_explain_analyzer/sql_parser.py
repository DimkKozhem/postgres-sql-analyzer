## py_pg_explain_analyzer/sql_parser.py
from __future__ import annotations
import sys
from sqlglot import parse_one, exp
from typing import Dict, List, Any


class SqlAnalyzer:
    """
    Суть модуля sql_parser.py простая — это статический анализатор SQL-запросов на базе sqlglot.
    1. Парсинг и AST
        - разбирает SQL-запрос в дерево выражений (sqlglot.Expression),
        - доступ к полному AST для дальнейшего анализа.
    2. Извлечение таблиц и колонок
        - собирает список используемых таблиц (включая schema.table),
        - учитывает алиасы,
        - исключает CTE (WITH ...),
        - пропускает * (SELECT *),
        - отдельно выделяет колонки, участвующие в фильтрах/сортировках/группировках (filter_columns) — полезно для рекомендаций по индексам.
    3. Нормализация SQL
        - возвращает отформатированный SQL в едином стиле (pretty-print).
    4. Линтинг
        - выполняет базовые проверки стиля: наличие ; в конце, количество таблиц,
        - можно расширять правила (например, запрет SELECT *, вложенные подзапросы и т. п.).
    """
    def __init__(self, sql: str, dialect: str = "postgres"):
        self.sql = sql.strip()
        self.dialect = dialect
        try:
            self.ast = parse_one(self.sql, read=self.dialect)
        except Exception as e:
            raise ValueError(f"Ошибка разбора SQL: {e}") from e

    def get_ast(self) -> exp.Expression:
        """Возвращает AST дерева (sqlglot Expression)."""
        return self.ast

    def get_tables_and_columns(self) -> Dict[str, Dict[str, Any]]:
        tables: Dict[str, Dict[str, Any]] = {}

        # соберём имена всех CTE
        cte_names = set()
        cte_names |= set([cte.this.this for cte in self.ast.find_all(exp.CTE) if cte.this.this])
        cte_names |= set([str(cte.alias) for cte in self.ast.find_all(exp.CTE)])


        # таблицы и алиасы
        for t in self.ast.find_all(exp.Table):
            # пропускаем CTE
            if t.this.this in cte_names and not t.args.get("db"):
                continue

            # собираем полное имя
            if t.args.get("db"):
                name = f"{t.args['db'].this}.{t.this.this}"
            else:
                name = t.this.this

            alias = t.args.get("alias")
            alias_name = alias.this if alias else None
            if isinstance(alias_name, exp.Identifier):
                alias_name = alias_name.this

            tables[name] = {"alias": alias_name, "columns": [], "filter_columns": []}


        # все колонки
        for c in self.ast.find_all(exp.Column):
            if isinstance(c.this, exp.Star):
                continue  # пропускаем *
            col_name = c.name
            table_name = None

            if c.table:  # есть алиас
                alias = str(c.table)
                for t, info in tables.items():
                    if info["alias"] == alias:
                        table_name = t
                        break

            if table_name:
                if col_name not in tables[table_name]["columns"]:
                    tables[table_name]["columns"].append(col_name)
            else:
                if len(tables) == 1:
                    first_tbl = next(iter(tables))
                    if col_name not in tables[first_tbl]["columns"]:
                        tables[first_tbl]["columns"].append(col_name)

        # фильтры (WHERE / JOIN / GROUP / ORDER / HAVING)
        filter_exprs = (
            list(self.ast.find_all(exp.Where))
            + list(self.ast.find_all(exp.Join))
            + list(self.ast.find_all(exp.Group))
            + list(self.ast.find_all(exp.Order))
            + list(self.ast.find_all(exp.Having))
        )

        for expr in filter_exprs:
            for c in expr.find_all(exp.Column):
                if isinstance(c.this, exp.Star):
                    continue  # пропускаем *
                col_name = c.name
                table_name = None

                if c.table:
                    alias = str(c.table)
                    for t, info in tables.items():
                        if info["alias"] == alias:
                            table_name = t
                            break
                else:
                    if len(tables) == 1:
                        table_name = next(iter(tables))

                if table_name and col_name not in tables[table_name]["filter_columns"]:
                    tables[table_name]["filter_columns"].append(col_name)


        return tables


    def normalize(self) -> str:
        """Возвращает нормализованный SQL (единый стиль)."""
        return self.ast.sql(dialect=self.dialect, pretty=True)

    def lint(self) -> List[str]:
        """
        Простая проверка: возвращает список предупреждений по стилю/структуре.
        (Можно расширять правила.)
        """
        issues = []
        if not self.sql.endswith(";"):
            issues.append("Запрос не оканчивается на ';'")
        if len(self.get_tables_and_columns()) > 5:
            issues.append("Запрос использует слишком много таблиц (рекомендуется <=5).")
        return issues

    def rewrite(self) -> str:
        """
        Базовый пример переписывания: упрощение COUNT(1) → COUNT(*).
        """
        rewritten = self.ast.transform(
            lambda n: exp.Count(this=exp.Star()) if isinstance(n, exp.Count) else n
        )
        return rewritten.sql(dialect=self.dialect, pretty=True)


def _demo(sql: str):
    analyzer = SqlAnalyzer(sql)

    print("=== AST ===")
    print(analyzer.get_ast().dump())

    print("\n=== Таблицы и колонки ===")
    print(analyzer.get_tables_and_columns())

    print("\n=== Нормализованный SQL ===")
    print(analyzer.normalize())

    print("\n=== Линтинг ===")
    print(analyzer.lint())

    print("\n=== Переписанный SQL ===")
    print(analyzer.rewrite())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sql = " ".join(sys.argv[1:])
    else:
        sql = """
        SELECT o.id, o.user_id, u.name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.created_at >= now() - interval '30 days'
        ORDER BY o.created_at DESC
        """
    _demo(sql)
