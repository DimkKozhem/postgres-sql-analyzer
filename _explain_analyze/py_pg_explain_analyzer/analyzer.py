## py_pg_explain_analyzer/analyzer.py
from __future__ import annotations
from typing import List
from .models import AnalysisRequest, AnalysisResult, Issue, Suggestion, IndexCandidate, Plan
from .db import PgConnection
from .plan_parser import parse_explain_json
from .rules import RULES
from .report import build_markdown_report

class PgExplainAnalyzer:
    def __init__(self, db_conn: PgConnection):
        self.db = db_conn

    def analyze_one(self, req: AnalysisRequest) -> AnalysisResult:
        raw = self.db.explain_json(
            sql=req.sql,
            analyze=req.analyze,
            verbose=req.verbose,
            buffers=req.buffers,
            timing=req.timing,
        )
        plan = parse_explain_json(raw)

        all_issues, all_sugs, all_idx = [], [], []
        for rule in RULES:
            issues, sugs, idx = rule(plan)
            all_issues.extend(issues)
            all_sugs.extend(sugs)
            all_idx.extend(idx)

        res = AnalysisResult(
            sql=req.sql,
            plan=plan,
            issues=all_issues,
            suggestions=all_sugs,
            index_candidates=all_idx,
            raw_explain_json=raw,
        )
        # Markdown без LLM (вторым шагом будем добавлять вывод LLM поверх)
        res.markdown_report = build_markdown_report(res, llm_summary=None)
        return res