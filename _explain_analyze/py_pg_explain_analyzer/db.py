## py_pg_explain_analyzer/db.py
from __future__ import annotations
from typing import Any, Dict, List
import json
import psycopg

class PgConnection:
    """Тонкая обёртка над psycopg для EXPLAIN JSON."""

    def __init__(self, dsn: str):
        self._conn = psycopg.connect(dsn)
        self._conn.autocommit = True

    def explain_json(self, sql: str, analyze: bool = False, verbose: bool = True,
                     buffers: bool = False, timing: bool = False, settings: bool = True, costs:bool = True) -> List[Dict[str, Any]]:
        flags = []
        if analyze:
            flags.append("ANALYZE")
        if verbose:
            flags.append("VERBOSE")
        if buffers:
            flags.append("BUFFERS")
        if timing:
            flags.append("TIMING")
        if settings:
            flags.append("SETTINGS")
        if costs:
            flags.append("COSTS")
        flags_str = ", ".join(flags)
        q = f"EXPLAIN ({flags_str}, FORMAT JSON) {sql}"
        with self._conn.cursor() as cur:
            cur.execute(q)
            row = cur.fetchone()
            # psycopg возвращает массив из одного JSON документа
            return row[0]

    def close(self):
        self._conn.close()
