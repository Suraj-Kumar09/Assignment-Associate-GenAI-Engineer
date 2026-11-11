"""Persistent memory: failures, reasons, fixes -> reused in the next run."""
import json
from pathlib import Path

from .rubric import CHECKPOINTS


def _latest_unique(items, n=3):
    seen, out = set(), []
    for x in reversed(items):
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:n]


class Memory:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self._load()

    def _blank(self):
        return {
            "runs": [],
            "failure_counts": {c: 0 for c in CHECKPOINTS},
            "reasons": {c: [] for c in CHECKPOINTS},
            "fixes": {c: [] for c in CHECKPOINTS},
        }

    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return self._blank()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    # ---- queries -------------------------------------------------------
    def recurring(self, threshold=2):
        """Checkpoints/instructions that keep failing."""
        return [c for c, n in self.data["failure_counts"].items() if n >= threshold]

    def top_reasons(self, cp, n=3):
        return _latest_unique(self.data["reasons"][cp], n)

    def generator_hints(self):
        """Past failures turned into proactive instructions for the Generator."""
        lines = []
        counts = sorted(self.data["failure_counts"].items(), key=lambda kv: -kv[1])
        for cp, n in counts:
            if n == 0:
                continue
            reasons = "; ".join(r.rstrip(".") for r in self.top_reasons(cp))
            line = f"- '{cp}' failed {n} time(s) before. Reasons: {reasons}."
            fixes = _latest_unique(self.data["fixes"][cp])
            if fixes:
                line += f" What fixed it earlier: {'; '.join(f.rstrip('.') for f in fixes)}."
            lines.append(line)
        return "\n".join(lines)

    # ---- update --------------------------------------------------------
    def record_run(self, run_id, status, attempts):
        for a in attempts:
            for cp in a["failed_checkpoints"]:
                self.data["failure_counts"][cp] += 1
                self.data["reasons"][cp].append(a["failure_reasons"][cp])
        # a retry that fixed a previously failed checkpoint -> remember what was changed
        for prev, cur in zip(attempts, attempts[1:]):
            for cp in prev["failed_checkpoints"]:
                if cp not in cur["failed_checkpoints"]:
                    self.data["fixes"][cp].append(cur["improvement_made"])
        self.data["runs"].append({"run_id": run_id, "status": status, "attempts": attempts})
        self.save()
