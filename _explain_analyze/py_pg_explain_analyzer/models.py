## py_pg_explain_analyzer/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class IndexCandidate:
    table: str
    columns: List[str]
    include: List[str] = field(default_factory=list)
    where_predicate: Optional[str] = None

    def to_ddl(self, schema: Optional[str] = None, unique: bool = False) -> str:
        tbl = f'"{schema}"."{self.table}"' if schema else f'"{self.table}"'
        cols = ", ".join([f'"{c}"' for c in self.columns])
        inc = f" INCLUDE ({', '.join([f'\"{c}\"' for c in self.include])})" if self.include else ""
        uniq = "UNIQUE " if unique else ""
        return f"CREATE {uniq}INDEX IF NOT EXISTS idx_{self.table}_{'_'.join(self.columns)} ON {tbl} ({cols}){inc};"

@dataclass
class Issue:
    code: str
    title: str
    severity: Severity
    details: str
    node_path: Optional[str] = None  # путь к узлу плана (для навигации)

@dataclass
class Suggestion:
    code: str
    title: str
    rationale: str
    fix: Optional[str] = None  # SQL/DDL/конкретные шаги
    related_indexes: List[IndexCandidate] = field(default_factory=list)

class PlanNode(BaseModel):
    node_type: str
    relation_name: Optional[str] = None
    alias: Optional[str] = None
    actual_rows: Optional[float] = None
    plan_rows: Optional[float] = None
    actual_total_time_ms: Optional[float] = None
    index_name: Optional[str] = None
    filter: Optional[str] = None
    join_type: Optional[str] = None
    hash_cond: Optional[str] = None
    merge_cond: Optional[str] = None
    recheck_cond: Optional[str] = None
    startup_cost: Optional[float] = None
    total_cost: Optional[float] = None
    rows: Optional[float] = None
    width: Optional[int] = None
    buffers: Dict[str, Any] = {}
    children: List["PlanNode"] = []

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow",
    }

class Plan(BaseModel):
    root: PlanNode
    planning_time_ms: Optional[float] = None
    execution_time_ms: Optional[float] = None

class AnalysisRequest(BaseModel):
    sql: str
    analyze: bool = False
    verbose: bool = False
    buffers: bool = False
    timing: bool = False
    settings: bool = False
    costs: bool = False

class AnalysisResult(BaseModel):
    sql: str
    plan: Plan
    issues: List[Issue]
    suggestions: List[Suggestion]
    index_candidates: List[IndexCandidate]
    markdown_report: Optional[str] = None
    raw_explain_json: Any
