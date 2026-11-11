import re

SYSTEM = """You are a Generator Agent that writes beginner lessons. Use simple English.
Assume the learner has ZERO knowledge. The lesson MUST contain these sections in order:
Introduction, What is RAG?, Why is RAG needed?, How does RAG work? (step by step),
Real-life examples (at least 2), Summary.
Explain every technical term in plain words the first time it appears.
Return exactly:
<lesson>...markdown lesson...</lesson>
<changes>1-3 lines: what you changed vs. the previous attempt (or 'initial draft')</changes>"""


class Generator:
    def __init__(self, llm):
        self.llm = llm

    def generate(self, topic, hints="", feedback="", prev_lesson=""):
        user = f"Topic: {topic}\n"
        if hints:
            user += f"\nLESSONS FROM PAST RUNS (avoid these failures proactively):\n{hints}\n"
        if feedback:
            user += (
                f"\nYour previous lesson was REJECTED. Evaluator feedback:\n{feedback}\n\n"
                f"Previous lesson:\n{prev_lesson}\n\nFix EVERY failure and rewrite the lesson."
            )
        out = self.llm.complete(SYSTEM, user)
        lesson = re.search(r"<lesson>(.*?)</lesson>", out, re.S)
        changes = re.search(r"<changes>(.*?)</changes>", out, re.S)
        return (
            lesson.group(1).strip() if lesson else out.strip(),
            changes.group(1).strip() if changes else "not reported",
        )
