"""Offline stand-ins (no API key) - same interface as Generator / Evaluator."""
from .rubric import CHECKPOINTS


class MockGenerator:
    """Weak first draft. Improves only from evaluator feedback or memory hints.
    stubborn=True never improves -> used to demo the REJECTED path."""

    def __init__(self, stubborn=False):
        self.stubborn = stubborn
        self.examples, self.jargon = 1, False

    def generate(self, topic, hints="", feedback="", prev_lesson=""):
        if not self.stubborn:
            if "examples" in hints or "example" in feedback.lower():
                self.examples = 2
            if "jargon" in hints or "jargon" in feedback.lower():
                self.jargon = True
        emb = ("Embedding = a list of numbers that captures the meaning of text.\n"
               if self.jargon else "We turn text into an embedding and store it in a vector database.\n")
        ex = "".join(f"### Example {i + 1}\nA practical use case number {i + 1}.\n" for i in range(self.examples))
        lesson = (
            "# Introduction to RAG\n## What is RAG?\nRAG retrieves documents and gives them to an LLM.\n"
            "## Why is RAG needed?\nLLMs can be outdated or make things up.\n"
            f"## How does RAG work?\n{emb}\n## Real-life examples\n{ex}\n## Summary\nRAG = search + generate."
        )
        return lesson, "mock: applied evaluator feedback / memory hints"


class MockEvaluator:
    def evaluate(self, lesson, rubric):
        from .evaluator import normalize

        raw = {c: "PASS" for c in CHECKPOINTS}
        why = {}
        if lesson.count("### Example") < 2:
            raw["examples"] = "FAIL"
            why["examples"] = "Only one practical example provided; a second is required."
        if "Embedding =" not in lesson:
            raw["jargon_explanation"] = "FAIL"
            why["jargon_explanation"] = "Jargon 'embedding' and 'vector database' used without explanation."
        raw["failure_reasons"] = why
        return normalize(raw)
