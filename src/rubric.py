"""Evaluator rubric. Every checkpoint is strictly PASS or FAIL (no partial marks)."""

RUBRIC = {
    "accuracy": (
        "PASS only if RAG is defined correctly: an LLM is combined with a retrieval step that "
        "fetches relevant external documents, which are given to the LLM as context to generate "
        "the answer. FAIL if RAG is confused with fine-tuning/training or any technical claim is wrong."
    ),
    "beginner_friendly": (
        "PASS only if the lesson assumes ZERO prior knowledge, uses simple short sentences and "
        "everyday words, and no concept is used before it is introduced."
    ),
    "examples": (
        "PASS only if there are AT LEAST 2 distinct, practical real-life examples "
        "(e.g. company chatbot, customer support, legal/medical search)."
    ),
    "jargon_explanation": (
        "PASS only if EVERY technical term used (LLM, embedding, vector database, retrieval, "
        "context, hallucination, etc.) is explained in plain words the first time it appears."
    ),
    "completeness": (
        "PASS only if the lesson clearly covers ALL of: What is RAG, Why is RAG needed, "
        "How does RAG work (step by step), Real-life examples."
    ),
    "teaching_flow": (
        "PASS only if the order is logical: introduction -> what -> why -> how -> examples -> "
        "summary/conclusion, with smooth transitions."
    ),
}
CHECKPOINTS = list(RUBRIC)


def evolved_rubric(memory, base=RUBRIC, threshold=2):
    """Checkpoints that failed >= threshold times in past runs get a stricter, explicit condition."""
    rubric = dict(base)
    for cp in memory.recurring(threshold):
        reasons = "; ".join(memory.top_reasons(cp))
        rubric[cp] += (
            f" [EVOLVED STRICTNESS: this checkpoint failed {memory.data['failure_counts'][cp]} "
            f"times before. Explicitly verify: {reasons}]"
        )
    return rubric
