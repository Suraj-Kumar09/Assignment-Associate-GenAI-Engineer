import os
from pathlib import Path

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_RETRIES = 2  # initial attempt + 2 retries = max 3 attempts
TOPIC = "Introduction to RAG (Retrieval-Augmented Generation)"
OUT_DIR = Path(os.getenv("OUT_DIR", "outputs"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
