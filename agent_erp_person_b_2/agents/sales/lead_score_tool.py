import os
from typing import Any, Dict
from tools.base import Tool

def _heuristic_score(features: Dict[str, Any]) -> float:
    msg_len = min(int(features.get("msg_len", 0)), 500) / 500.0
    kw_hits = min(int(features.get("kw_hits", 0)), 5) / 5.0
    visits = min(int(features.get("visits", 0)), 10) / 10.0
    source = str(features.get("source", "web")).lower()
    src_w = {"web":0.5, "email":0.7, "referral":0.8, "event":0.9}.get(source, 0.5)
    raw = 0.35*msg_len + 0.35*kw_hits + 0.2*visits + 0.1*src_w
    return max(0.0, min(1.0, raw))

class LeadScoreTool(Tool):
    name = "lead_score_tool"
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_order = ["msg_len","kw_hits","visits","source_event","source_referral","source_email"]
        if model_path and os.path.exists(model_path):
            try:
                import joblib
                self.model = joblib.load(model_path)
                if hasattr(self.model, "feature_names_"):
                    self.feature_order = list(self.model.feature_names_)
            except Exception:
                self.model = None
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        feats = payload.get("features", {})
        if self.model is None:
            score = _heuristic_score(feats)
            return {"ok": True, "score": float(score), "mode": "heuristic"}
        try:
            src = str(feats.get("source","web")).lower()
            X = [
                float(feats.get("msg_len",0)),
                float(feats.get("kw_hits",0)),
                float(feats.get("visits",0)),
                1.0 if src=="event" else 0.0,
                1.0 if src=="referral" else 0.0,
                1.0 if src=="email" else 0.0,
            ]
            prob = float(self.model.predict_proba([X])[0][1])
            return {"ok": True, "score": prob, "mode": "ml"}
        except Exception as e:
            return {"ok": False, "error": f"ML scoring failed: {e}"}
