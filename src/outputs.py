import json
from pathlib import Path


def write_outputs(out_dir, result):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "rejection_log.json").write_text(json.dumps(
        {"run_id": result["run_id"], "topic": result["topic"],
         "final_status": result["status"], "attempts": result["attempts"]},
        indent=2, ensure_ascii=False))

    md = [f"# Rejection Log  (run {result['run_id']})", f"**Final status:** {result['status']}\n",
          "| Attempt | Result | Failed checks |", "|---|---|---|"]
    for a in result["attempts"]:
        md.append(f"| {a['attempt']} | {a['result']} | {', '.join(a['failed_checkpoints']) or '-'} |")
    md.append("")
    for a in result["attempts"]:
        if a["failed_checkpoints"]:
            md.append(f"## {a['attempt']}")
            for cp, why in a["failure_reasons"].items():
                md.append(f"- **{cp}**: {why}")
            md.append("")
        if a["improvement_made"] != "initial draft":
            md.append(f"_Improvement in {a['attempt']}:_ {a['improvement_made']}\n")
    (out / "rejection_log.md").write_text("\n".join(md))

    approved = out / "approved_lesson.md"
    if result["status"] == "APPROVED":
        approved.write_text(result["lesson"])
    else:
        approved.unlink(missing_ok=True)  # a failed lesson is never presented as approved
