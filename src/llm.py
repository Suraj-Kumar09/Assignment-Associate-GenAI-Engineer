import json
import os
import re
import time
import urllib.error
import urllib.request


class ClaudeClient:
    def __init__(self, model):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system, user, max_tokens=3000):
        r = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text")


def parse_gemini(data):
    """Pull the answer text out of a Gemini generateContent response."""
    cands = data.get("candidates")
    if not cands:
        raise RuntimeError(f"Gemini returned no candidates (blocked?): {data.get('promptFeedback')}")
    parts = cands[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text.strip():
        raise RuntimeError(f"Gemini returned empty text (finishReason={cands[0].get('finishReason')})")
    return text


class GeminiClient:
    """Plain REST call (stdlib only, no extra package needed)."""

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, model, api_key=None):
        self.model = model
        self.api_key = api_key or os.environ["GEMINI_API_KEY"]

    def complete(self, system, user, max_tokens=3000):
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            # extra room: Gemini 2.5 models count internal "thinking" tokens in this limit
            "generationConfig": {"maxOutputTokens": max(max_tokens, 8192)},
        }
        req = urllib.request.Request(
            self.URL.format(model=self.model),
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return parse_gemini(json.load(r))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                if e.code in (429, 500, 503) and attempt < 3:  # free-tier rate limit -> wait, retry
                    wait = 15 * (attempt + 1)
                    print(f"[gemini] HTTP {e.code}, retrying in {wait}s ...")
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"Gemini API error {e.code}: {detail}") from None


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("No JSON object found in model output")
    return json.loads(m.group(0))
