"""Input -> Generator -> Evaluator -> Decision / Regeneration -> Memory."""
from datetime import datetime

from .rubric import CHECKPOINTS, RUBRIC, evolved_rubric


def run_pipeline(generator, evaluator, memory, topic, max_retries=2, log=print):
    hints = memory.generator_hints()
    rubric = evolved_rubric(memory, RUBRIC)
    if hints:
        log(f"[memory] Injecting past-failure hints into generator:\n{hints}\n")
    if memory.recurring():
        log(f"[memory] Rubric tightened for recurring failures: {memory.recurring()}\n")

    attempts, feedback, lesson, status = [], "", "", "REJECTED"
    for i in range(max_retries + 1):
        label = "Initial generation" if i == 0 else f"Retry {i}"
        lesson, changes = generator.generate(topic, hints, feedback, lesson)
        result = evaluator.evaluate(lesson, rubric)
        failed = [c for c in CHECKPOINTS if result[c] == "FAIL"]
        log(f"[{label}] {result['overall_result']}  failed={failed}")
        attempts.append({
            "attempt": label,
            "result": result["overall_result"],
            "checkpoints": {c: result[c] for c in CHECKPOINTS},
            "failed_checkpoints": failed,
            "failure_reasons": result["failure_reasons"],
            "improvement_made": changes if i > 0 else "initial draft",
        })
        if result["overall_result"] == "PASS":
            status = "APPROVED"
            break
        feedback = "\n".join(f"- {c}: {r}" for c, r in result["failure_reasons"].items())

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    memory.record_run(run_id, status, attempts)
    return {"run_id": run_id, "topic": topic, "status": status,
            "lesson": lesson if status == "APPROVED" else None, "attempts": attempts}
