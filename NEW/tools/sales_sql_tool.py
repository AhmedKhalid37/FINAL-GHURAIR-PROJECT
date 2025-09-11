import sqlite3
from typing import Any, Dict
from tools.base import Tool

class SalesSQLTool(Tool):
    name = "sales_sql_read_write"
    def __init__(self, db_path: str):
        self.db_path = db_path
    def _conn(self):
        con = sqlite3.connect(self.db_path)
        con.execute("PRAGMA foreign_keys = ON;")
        return con
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        op = payload.get("op")
        query = payload.get("query", "")
        params = payload.get("params", [])
        many = bool(payload.get("many", False))
        if not op or not query:
            return {"ok": False, "error": "Missing 'op' or 'query'"}
        with self._conn() as con:
            cur = con.cursor()
            try:
                if op == "read":
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description] if cur.description else []
                    return {"ok": True, "columns": cols, "rows": rows}
                elif op == "write":
                    if many:
                        cur.executemany(query, params)
                        lastrowid = None
                    else:
                        cur.execute(query, params)
                        lastrowid = cur.lastrowid
                    con.commit()
                    return {"ok": True, "rowcount": cur.rowcount, "lastrowid": lastrowid}
                else:
                    return {"ok": False, "error": f"Unknown op: {op}"}
            except Exception as e:
                return {"ok": False, "error": str(e)}
