import sqlite3
from typing import Any, Dict, List
from tools.base import Tool

class AnomalyDetectorTool(Tool):
    name = "anomaly_detector_tool"
    def __init__(self, db_path: str, ratio_threshold: float = 1.6, min_history: int = 3):
        self.db_path = db_path
        self.ratio_threshold = ratio_threshold
        self.min_history = min_history
    def _conn(self):
        return sqlite3.connect(self.db_path)
    def _vendor_history(self, vendor_id: int) -> List[float]:
        sql = "SELECT total FROM invoices WHERE vendor_id=? AND status IN ('posted','paid')"
        with self._conn() as con:
            cur = con.cursor()
            cur.execute(sql, (vendor_id,))
            return [float(r[0]) for r in cur.fetchall()]
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "invoice_id" in payload:
            sql = "SELECT vendor_id, total, currency FROM invoices WHERE invoice_id=?"
            with self._conn() as con:
                cur = con.cursor()
                cur.execute(sql, (payload["invoice_id"],))
                row = cur.fetchone()
                if not row:
                    return {"ok": False, "error": "Invoice not found"}
                vendor_id, total, currency = int(row[0]), float(row[1]), (row[2] or "USD")
        else:
            feats = payload.get("features", {})
            vendor_id = int(feats.get("vendor_id", 0))
            total = float(feats.get("total", 0.0))
            currency = str(feats.get("currency", "USD"))
        hist = self._vendor_history(vendor_id)
        reasons = []
        is_anom = False
        if len(hist) >= self.min_history:
            avg = sum(hist)/len(hist)
            ratio = (total/avg) if avg>0 else 0.0
            reasons.append(("ratio_vs_vendor_avg", round(ratio,2)))
            if ratio >= self.ratio_threshold:
                is_anom = True
        else:
            if total > 10000:
                is_anom = True
                reasons.append(("insufficient_history_high_total", total))
        if currency not in ("USD","EUR","AED"):
            reasons.append(("unusual_currency", currency))
        score = 0.5 if is_anom else 0.1
        return {"ok": True, "score": float(score), "is_anomalous": bool(is_anom), "reasons": reasons}
