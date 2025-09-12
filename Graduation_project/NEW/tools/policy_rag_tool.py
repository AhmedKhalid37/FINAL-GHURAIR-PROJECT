import sqlite3
from typing import Any, Dict
from tools.base_tool import BaseTool, register_tool
from tools.sales_rag_tool import _score_text

@register_tool
class PolicyRAGTool(BaseTool):
    name: str = "policy_rag_tool"
    description: str = "Search policy and glossary documents for relevant passages."

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        q = (payload.get("query") or "").strip()
        k = int(payload.get("k", 3))
        if not q:
            return {"ok": False, "error": "Empty query"}
        sql = """
        SELECT doc_id, title, body, category, updated_at
        FROM documents
        WHERE category IN ('policy','glossary')
          AND (title LIKE ? OR body LIKE ?)
        """
        like = f"%{q}%"
        with self._conn() as con:
            cur = con.cursor()
            cur.execute(sql, (like, like))
            rows = cur.fetchall()
        docs = []
        for (doc_id, title, body, category, updated_at) in rows:
            score = _score_text((title or "") + "\n" + (body or ""), q)
            docs.append({"doc_id": doc_id, "title": title, "category": category,
                         "score": score, "snippet": (body or "")[:240]})
        docs.sort(key=lambda d: d["score"], reverse=True)
        return {"ok": True, "matches": docs[:k]}
