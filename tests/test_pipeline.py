import json

from src.evaluator import normalize
from src.memory import Memory
from src.mock import MockEvaluator, MockGenerator
from src.outputs import write_outputs
from src.pipeline import run_pipeline
from src.rubric import CHECKPOINTS, RUBRIC, evolved_rubric


def _run(tmp_path, stubborn=False):
    mem = Memory(tmp_path / "memory.json")
    res = run_pipeline(MockGenerator(stubborn), MockEvaluator(), mem, "RAG", 2, log=lambda *_: None)
    write_outputs(tmp_path, res)
    return res, mem


def test_results_are_binary_and_overall_computed_in_code():
    raw = {c: "PASS" for c in CHECKPOINTS}
    raw["examples"] = "PARTIAL"          # no partial marks -> FAIL
    raw["overall_result"] = "PASS"       # LLM's own verdict must be ignored
    res = normalize(raw)
    assert res["examples"] == "FAIL" and res["overall_result"] == "FAIL"
    assert set(res[c] for c in CHECKPOINTS) <= {"PASS", "FAIL"}


def test_retry_then_pass(tmp_path):
    res, _ = _run(tmp_path)
    assert res["status"] == "APPROVED"
    assert [a["result"] for a in res["attempts"]] == ["FAIL", "PASS"]
    assert (tmp_path / "approved_lesson.md").exists()


def test_rejected_after_max_retries(tmp_path):
    res, _ = _run(tmp_path, stubborn=True)
    assert res["status"] == "REJECTED"
    assert len(res["attempts"]) == 3                       # initial + 2 retries
    assert not (tmp_path / "approved_lesson.md").exists()  # never shown as approved
    log = json.loads((tmp_path / "rejection_log.json").read_text())
    assert log["final_status"] == "REJECTED"


def test_memory_is_actually_used_next_run(tmp_path):
    _run(tmp_path)                       # run 1: fails first, learns
    res2, mem = _run(tmp_path)           # run 2: memory hints -> pass on first attempt
    assert len(res2["attempts"]) == 1 and res2["status"] == "APPROVED"
    assert mem.generator_hints() != ""


def test_recurring_failures_tighten_rubric(tmp_path):
    _run(tmp_path, stubborn=True)
    _, mem = _run(tmp_path, stubborn=True)
    assert "examples" in mem.recurring()
    assert "EVOLVED STRICTNESS" in evolved_rubric(mem, RUBRIC)["examples"]


# ---- real-LLM code path, tested with a fake LLM (no network) ------------------------------
from src.evaluator import Evaluator
from src.generator import Generator
from src.llm import parse_gemini


class FakeLLM:
    """Acts like Gemini/Claude: weak lesson first, good lesson after feedback; evaluator returns fenced JSON."""

    def complete(self, system, user, max_tokens=0):
        if "Generator Agent" in system:
            good = "REJECTED" in user
            body = "good lesson" if good else "weak lesson"
            return f"<lesson>{body}</lesson><changes>added example</changes>"
        ok = "good lesson" in user
        verdict = {c: "PASS" for c in CHECKPOINTS}
        if not ok:
            verdict["examples"] = "FAIL"
            verdict["failure_reasons"] = {"examples": "Only 1 example."}
        import json as _j
        return "```json\n" + _j.dumps(verdict) + "\n```"


def test_real_agents_with_fake_llm(tmp_path):
    mem = Memory(tmp_path / "m.json")
    llm = FakeLLM()
    res = run_pipeline(Generator(llm), Evaluator(llm), mem, "RAG", 2, log=lambda *_: None)
    assert res["status"] == "APPROVED" and res["lesson"] == "good lesson"
    assert [a["result"] for a in res["attempts"]] == ["FAIL", "PASS"]
    assert res["attempts"][1]["improvement_made"] == "added example"


def test_parse_gemini_response():
    data = {"candidates": [{"content": {"parts": [{"text": "Hello "}, {"text": "world"}]}}]}
    assert parse_gemini(data) == "Hello world"
