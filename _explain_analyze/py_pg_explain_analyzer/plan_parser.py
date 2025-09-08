## py_pg_explain_analyzer/plan_parser.py
from __future__ import annotations
from typing import Any, Dict, List
from .models import Plan, PlanNode

# EXPLAIN FORMAT JSON обычно отдаёт список из объектов, где ключи: "Plan", "Planning Time", "Execution Time".

def _parse_node(raw: Dict[str, Any]) -> PlanNode:
    children = []
    for kid in raw.get("Plans", []) or []:
        children.append(_parse_node(kid))

    # нормализуем buffers: если в плане есть конкретные ключи с числами → собираем словарь
    buffers: Dict[str, Any] = {}
    for key in [
        "Shared Hit Blocks",
        "Shared Read Blocks",
        "Shared Dirtied Blocks",
        "Shared Written Blocks",
        "Local Hit Blocks",
        "Local Read Blocks",
        "Local Dirtied Blocks",
        "Local Written Blocks",
        "Temp Read Blocks",
        "Temp Written Blocks",
        "I/O Read Time",
        "I/O Write Time",
    ]:
        if key in raw:
            buffers[key] = raw[key]

    return PlanNode(
        node_type=raw.get("Node Type"),
        relation_name=raw.get("Relation Name"),
        alias=raw.get("Alias"),
        actual_rows=raw.get("Actual Rows"),
        plan_rows=raw.get("Plan Rows"),
        actual_total_time_ms=raw.get("Actual Total Time"),
        index_name=raw.get("Index Name"),
        filter=raw.get("Filter"),
        join_type=raw.get("Join Type"),
        hash_cond=raw.get("Hash Cond"),
        merge_cond=raw.get("Merge Cond"),
        recheck_cond=raw.get("Recheck Cond"),
        startup_cost=raw.get("Startup Cost"),
        total_cost=raw.get("Total Cost"),
        rows=raw.get("Plan Rows"),
        width=raw.get("Plan Width"),
        buffers=buffers,
        children=children,
    )



def parse_explain_json(doc: List[Dict[str, Any]]) -> Plan:
    # doc: список из одного объекта; внутри ключ "Plan" — корень
    first = doc[0]
    root_raw = first["Plan"]
    root = _parse_node(root_raw)
    planning_time_ms = first.get("Planning Time")
    execution_time_ms = first.get("Execution Time")
    return Plan(root=root, planning_time_ms=planning_time_ms, execution_time_ms=execution_time_ms)

