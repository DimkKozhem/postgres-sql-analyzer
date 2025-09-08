## py_pg_explain_analyzer/report.py
from __future__ import annotations
from typing import List
from .models import AnalysisResult, Issue, Suggestion, IndexCandidate


def _render_issues(issues: List[Issue]) -> str:
    if not issues:
        return "**Проблемы не обнаружены.**"
    out = ["### Обнаруженные проблемы:"]
    for it in issues:
        out.append(f"- **[{it.severity.value.upper()}] {it.title}** (code={it.code})\n  \n  {it.details}")
    return "\n".join(out)


def _render_suggestions(sug: List[Suggestion]) -> str:
    if not sug:
        return "**Предложения отсутствуют.**"
    out = ["### Предложения по оптимизации:"]
    for s in sug:
        out.append(f"- **{s.title}** (code={s.code})\n  \n  _Почему:_ {s.rationale}\n\n  _Шаги:_\n\n  ```sql\n{s.fix or '-- см. описание выше'}\n```")
    return "\n".join(out)


def _render_indexes(idx: List[IndexCandidate]) -> str:
    if not idx:
        return "**Кандидаты индексов не предложены.**"
    out = ["### Кандидаты индексов:"]
    for ic in idx:
        out.append(f"- {ic.to_ddl()}")
    return "\n".join(out)


def build_markdown_report(res: AnalysisResult, llm_summary: str = "") -> str:
    header = f"# Отчёт по анализу запроса\n\n````sql\n{res.sql}\n````\n\n"
    meta = []
    if res.plan.planning_time_ms is not None:
        meta.append(f"Planning time: {res.plan.planning_time_ms:.2f} ms")
    if res.plan.execution_time_ms is not None:
        meta.append(f"Execution time: {res.plan.execution_time_ms:.2f} ms")
    meta_block = ("\n".join(meta) + "\n\n") if meta else ""

    sections = [
        header,
        meta_block,
        _render_issues(res.issues),
        "\n\n",
        _render_suggestions(res.suggestions),
        "\n\n",
        _render_indexes(res.index_candidates),
    ]

    if llm_summary:
        sections.append("\n\n---\n\n## LLM‑резюме\n\n" + llm_summary)

    return "".join(sections)