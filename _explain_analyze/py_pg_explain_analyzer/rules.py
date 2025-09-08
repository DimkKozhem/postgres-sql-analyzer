## py_pg_explain_analyzer/rules.py

from __future__ import annotations
from typing import List, Tuple
from .models import Plan, PlanNode, Issue, Suggestion, Severity, IndexCandidate
import re


def _walk(node: PlanNode):
    yield node
    for ch in node.children:
        yield from _walk(ch)


# Простейший парсер выражений для WHERE/Join, чтобы вытащить колонки
_COL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_\.]*)\s*(=|<|>|<=|>=|IN|LIKE|ILIKE)")


def extract_columns(expr: str) -> List[str]:
    cols = []
    for m in _COL_RE.finditer(expr or ""):
        col = m.group(1)
        if "." in col or col.isidentifier():
            cols.append(col.split(".")[-1])
    return list(dict.fromkeys(cols))


# === Эвристики ===

def rule_seqscan(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """Seq Scan без индекса."""
    issues, suggestions, idx = [], [], []
    for node in _walk(plan.root):
        if node.node_type == "Seq Scan" and node.relation_name:
            issues.append(
                Issue(
                    code="SEQSCAN",
                    title=f"Полное сканирование {node.relation_name}",
                    severity=Severity.MEDIUM,
                    details=f"Запрос делает последовательное сканирование таблицы {node.relation_name}.",
                    node_path=node.relation_name,
                )
            )
            if node.filter:
                cols = extract_columns(node.filter)
                if cols:
                    cand = IndexCandidate(table=node.relation_name, columns=cols)
                    idx.append(cand)
                    suggestions.append(
                        Suggestion(
                            code="INDEX_FOR_SEQSCAN",
                            title=f"Рассмотрите индекс на {node.relation_name}({', '.join(cols)})",
                            rationale=f"Фильтр `{node.filter}` может быть ускорен индексом.",
                            related_indexes=[cand],
                            fix=cand.to_ddl(),
                        )
                    )
    return issues, suggestions, idx


def rule_joins(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """Hash Join / Merge Join / Nested Loop → проверить условие соединения и предложить индексы."""
    issues, suggestions, idx = [], [], []
    for node in _walk(plan.root):
        if node.node_type in ("Hash Join", "Merge Join", "Nested Loop"):
            cond = node.hash_cond or node.merge_cond
            if cond:
                cols = extract_columns(cond)
                if len(cols) >= 2 and len(node.children) >= 2:
                    left_col, right_col = cols[0], cols[1]
                    ltab = node.children[0].relation_name or "left"
                    rtab = node.children[1].relation_name or "right"
                    ic1 = IndexCandidate(table=str(ltab), columns=[left_col])
                    ic2 = IndexCandidate(table=str(rtab), columns=[right_col])
                    idx.extend([ic1, ic2])
                    suggestions.append(
                        Suggestion(
                            code="INDEX_FOR_JOIN",
                            title=f"Индексы под условие соединения: {ltab}({left_col}), {rtab}({right_col})",
                            rationale=f"Условие соединения `{cond}` может быть ускорено индексами.",
                            related_indexes=[ic1, ic2],
                            fix="\n".join([ic1.to_ddl(), ic2.to_ddl()]),
                        )
                    )
    return issues, suggestions, idx


def rule_sort(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """Sort → проверить ORDER BY, предложить индекс."""
    issues, suggestions, idx = [], [], []
    for node in _walk(plan.root):
        if node.node_type == "Sort":
            issues.append(
                Issue(
                    code="SORT_NODE",
                    title="Сортировка в плане",
                    severity=Severity.LOW,
                    details="Используется Sort. Для ORDER BY стоит проверить индекс.",
                )
            )
            # В JSON плана бывает поле Sort Key
            sort_keys = getattr(node, "sort_key", None)
            if sort_keys:
                cand = IndexCandidate(table="?", columns=sort_keys)
                idx.append(cand)
                suggestions.append(
                    Suggestion(
                        code="INDEX_FOR_SORT",
                        title=f"Индекс под ORDER BY ({', '.join(sort_keys)})",
                        rationale="Сортировка может быть ускорена индексом.",
                        related_indexes=[cand],
                        fix=cand.to_ddl(),
                    )
                )
    return issues, suggestions, idx


def rule_group_by(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """GroupAggregate / HashAggregate → проверить возможность индекса."""
    issues, suggestions, idx = [], [], []
    for node in _walk(plan.root):
        if node.node_type in ("GroupAggregate", "HashAggregate"):
            issues.append(
                Issue(
                    code="AGGREGATE_NODE",
                    title=f"Агрегация ({node.node_type})",
                    severity=Severity.LOW,
                    details="Используется агрегация. Для GROUP BY/DISTINCT можно рассмотреть индекс.",
                )
            )
    return issues, suggestions, idx


def rule_limit_without_order(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """LIMIT без ORDER BY → результат может быть неопределённым."""
    issues, suggestions, idx = [], [], []
    for node in _walk(plan.root):
        if node.node_type == "Limit":
            # ищем наличие Sort выше по дереву
            parent_has_sort = any(ch.node_type == "Sort" for ch in node.children)
            if not parent_has_sort:
                issues.append(
                    Issue(
                        code="LIMIT_WITHOUT_ORDER",
                        title="LIMIT без ORDER BY",
                        severity=Severity.LOW,
                        details="Запрос использует LIMIT, но без ORDER BY порядок строк не гарантируется.",
                    )
                )
    return issues, suggestions, idx


def rule_dml_without_where(plan: Plan) -> Tuple[List[Issue], List[Suggestion], List[IndexCandidate]]:
    """Проверка на UPDATE/DELETE без WHERE."""
    issues, suggestions, idx = [], [], []
    if plan.root.node_type in ("Delete", "Update"):
        has_filter = any(node.filter for node in _walk(plan.root))
        if not has_filter:
            issues.append(
                Issue(
                    code="DML_NO_WHERE",
                    title=f"{plan.root.node_type} без WHERE",
                    severity=Severity.HIGH,
                    details=f"Операция {plan.root.node_type} может затронуть всю таблицу.",
                )
            )
    return issues, suggestions, idx


# Список всех правил
RULES = [
    rule_seqscan,
    rule_joins,
    rule_sort,
    rule_group_by,
    rule_limit_without_order,
    rule_dml_without_where,
]
