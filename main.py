"""CLI:  python main.py [--provider auto|gemini|claude|mock] [--runs N] [--stubborn]
                        [--reset-memory] [--show-memory]"""
import argparse
import os
import sys

from src import config
from src.evaluator import Evaluator
from src.generator import Generator
from src.memory import Memory
from src.outputs import write_outputs
from src.pipeline import run_pipeline


def resolve_provider(choice, mock_flag):
    if mock_flag:
        return "mock"
    if choice != "auto":
        return choice
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude"
    return "mock"


def build_agents(provider, stubborn):
    if provider == "mock":
        from src.mock import MockEvaluator, MockGenerator
        return MockGenerator(stubborn=stubborn), MockEvaluator()
    if provider == "gemini":
        from src.llm import GeminiClient
        llm = GeminiClient(config.GEMINI_MODEL)
    else:
        from src.llm import ClaudeClient
        llm = ClaudeClient(config.MODEL)
    return Generator(llm), Evaluator(llm)


def main():
    ap = argparse.ArgumentParser(description="Self-evolving RAG lesson generator")
    ap.add_argument("--provider", choices=["auto", "gemini", "claude", "mock"], default="auto",
                    help="auto = GEMINI_API_KEY, else ANTHROPIC_API_KEY, else mock")
    ap.add_argument("--mock", action="store_true", help="same as --provider mock")
    ap.add_argument("--stubborn", action="store_true", help="(mock) generator never improves -> REJECTED demo")
    ap.add_argument("--runs", type=int, default=1, help="run the pipeline N times (see memory effect)")
    ap.add_argument("--reset-memory", action="store_true")
    ap.add_argument("--show-memory", action="store_true")
    a = ap.parse_args()

    mem_path = config.OUT_DIR / "memory.json"
    if a.reset_memory and mem_path.exists():
        mem_path.unlink()
        print("Memory reset.")
    memory = Memory(mem_path)

    if a.show_memory:
        d = memory.data
        print(f"Runs: {len(d['runs'])}\nFailure counts: {d['failure_counts']}")
        print(f"Recurring (>=2): {memory.recurring()}")
        print(f"Hints that will be injected next run:\n{memory.generator_hints() or '(none)'}")
        return 0

    provider = resolve_provider(a.provider, a.mock)
    needs_key = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}.get(provider)
    if needs_key and not os.getenv(needs_key):
        print(f"ERROR: {needs_key} is not set in this terminal.")
        return 2
    model = {"gemini": config.GEMINI_MODEL, "claude": config.MODEL}.get(provider, "offline demo")
    print(f"Provider: {provider} ({model})")

    status = "REJECTED"
    for n in range(1, a.runs + 1):
        print(f"\n===== RUN {n}/{a.runs} =====")
        gen, ev = build_agents(provider, a.stubborn)
        result = run_pipeline(gen, ev, memory, config.TOPIC, config.MAX_RETRIES)
        write_outputs(config.OUT_DIR, result)
        status = result["status"]
        print(f"=> {status}")

    print(f"\nOutputs in: {config.OUT_DIR}/  (approved_lesson.md, rejection_log.json/.md, memory.json)")
    return 0 if status == "APPROVED" else 1


if __name__ == "__main__":
    sys.exit(main())
