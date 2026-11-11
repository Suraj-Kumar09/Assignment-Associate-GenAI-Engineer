from .llm import extract_json
from .rubric import CHECKPOINTS

SYSTEM = """You are a strict Evaluator Agent. Judge the lesson against the rubric.
Each checkpoint must be exactly "PASS" or "FAIL" - NO partial marks. If in doubt, FAIL.
Return ONLY JSON (no markdown fences):
{"accuracy":"PASS|FAIL","beginner_friendly":"...","examples":"...","jargon_explanation":"...",
 "completeness":"...","teaching_flow":"...",
 "failure_reasons":{"<failed_checkpoint>":"specific reason + what to fix"}}"""


def normalize(raw):
    """Enforce binary results; overall is computed in code (LLM's own verdict is never trusted)."""
    res = {c: ("PASS" if str(raw.get(c, "")).strip().upper() == "PASS" else "FAIL") for c in CHECKPOINTS}
    res["overall_result"] = "PASS" if all(res[c] == "PASS" for c in CHECKPOINTS) else "FAIL"
    reasons = raw.get("failure_reasons") or {}
    failed = [c for c in CHECKPOINTS if res[c] == "FAIL"]
    if isinstance(reasons, list):
        reasons = {c: "; ".join(map(str, reasons)) for c in failed}
    res["failure_reasons"] = {c: str(reasons.get(c, "No reason given by evaluator")) for c in failed}
    return res


class Evaluator:
    def __init__(self, llm):
        self.llm = llm

    def evaluate(self, lesson, rubric):
        rub = "\n".join(f"- {k}: {v}" for k, v in rubric.items())
        text = self.llm.complete(SYSTEM, f"RUBRIC:\n{rub}\n\nLESSON:\n{lesson}", max_tokens=1500)
        return normalize(extract_json(text))
