# py_pg_explain_analyzer/llm_summarizer.py
from __future__ import annotations
import json
from typing import Any, Dict, Optional
from textwrap import dedent

def _build_prompt(payload: Dict[str, Any]) -> str:
    """
    Собираем один большой промпт:
    - исходный SQL и нормализованный SQL;
    - результаты парсинга (таблицы/алиасы/колонки/filters);
    - метаданные по таблицам и колонкам (pg_class/pg_stats/индексы/UNINDEXED);
    - сырой EXPLAIN FORMAT JSON;
    - эвристики (issues/suggestions/index_candidates).
    """
    return dedent(f"""
    Ты — помощник по оптимизации Postgres-запросов. Проанализируй пакет данных и верни
    СТРОГО один JSON со следующей схемой:

    {{
      "problems": [{{"title": str, "severity": "low|medium|high|critical", "details": str}}],
      "warnings": [{{"title": str, "details": str}}],
      "recommendations": [
        {{"title": str, 
          "actions": [{{"sql": str|null, "note": str|null}}]
        }}
      ],
      "fixed_sql": str|null
    }}

    Запрещено выдумывать детали, опирайся только на входные данные.
    Если каких-то разделов нет — верни пустые массивы. Если нечего переписывать — fixed_sql = null.

    === ВХОДНЫЕ ДАННЫЕ ===
    ## original_sql
    {payload.get("sql")}

    ## normalized_sql
    {payload.get("normalized_sql")}

    ## parser_output (tables/aliases/columns/filter_columns)
    {json.dumps(payload.get("parser_output"), ensure_ascii=False)}

    ## metadata (types/indexes/pg_stats/estimated_rows/unindexed_columns)
    {json.dumps(payload.get("metadata", {}), ensure_ascii=False)}

    ## explain_json (FORMAT JSON)
    {json.dumps(payload.get("explain_json"), ensure_ascii=False)}

    ## heuristics (issues/suggestions/index_candidates)
    {json.dumps(payload.get("heuristics"), ensure_ascii=False)}
    """)

def run_llm(llm_client, payload: Dict[str, Any], model: str = "gpt-4.1-mini") -> Dict[str, Any]:
    """
    Универсальный вызов LLM, ожидающий клиента с методом chat.completions.create(...).
    Возвращает dict с ключами по схеме из _build_prompt().
    """
    prompt = _build_prompt(payload)
    resp = llm_client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Ты строгий эксперт по производительности Postgres и индексам."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        # На всякий случай заворачиваем «как есть», чтобы не терять ответ
        return {"raw_content": content}
