# Self-Evolving RAG Lesson Generator (Generator + Evaluator Agents)

Ek AI system jo **"Introduction to RAG"** ka beginner lesson banata hai, evaluator se check karwata hai,
fail hone par retry karta hai (max 2), aur past failures se **seekhkar next run improve** hota hai.

## Flow

```
INPUT (Topic: RAG, zero-knowledge learner)
        |
        v
 +--------------+   lesson   +------------------+
 |  GENERATOR   | ---------> |    EVALUATOR     |  6 checkpoints, sirf PASS/FAIL
 +--------------+            +------------------+
        ^                            |
        | feedback (failure_reasons) |
        +------------ FAIL <---------+--------> PASS -> approved_lesson.md
              (max 2 retries)
                     |
        2 retries ke baad bhi FAIL -> REJECTED (approved lesson nahi banta)
                     |
                     v
   MEMORY (memory.json) -> next run: generator hints + stricter rubric
```

## Project structure

```
rag_lesson_agent/
├── main.py                 # CLI
├── src/
│   ├── config.py           # model, topic, MAX_RETRIES=2
│   ├── rubric.py           # rubric + evolved_rubric() (memory se strict hota hai)
│   ├── generator.py        # Generator Agent
│   ├── evaluator.py        # Evaluator Agent + binary enforcement
│   ├── pipeline.py         # generate -> evaluate -> retry loop
│   ├── memory.py           # persistent memory + hints
│   ├── outputs.py          # approved_lesson.md, rejection_log.json/.md
│   ├── llm.py              # Claude API client
│   └── mock.py             # offline demo (no API key)
├── tests/test_pipeline.py  # 5 tests
└── sample_outputs/         # approved_run/ aur rejected_run/ ke example outputs
```

## Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # real Claude
python main.py                          # 1 run
python main.py --runs 3                 # 3 runs -> memory ka effect dekhein
python main.py --mock --runs 2          # bina API key ke demo
python main.py --mock --stubborn        # REJECTED path demo
python main.py --show-memory            # memory + next-run hints
python main.py --reset-memory
python -m pytest -q
```

## Rubric (sirf PASS / FAIL, partial marks nahi)

| Checkpoint | PASS condition |
|---|---|
| accuracy | RAG = retrieval + LLM generation with retrieved context; fine-tuning se confuse nahi |
| beginner_friendly | Zero-knowledge, simple English, concept use hone se pehle introduce |
| examples | Kam se kam 2 practical real-life examples |
| jargon_explanation | Har technical term pehli baar aane par plain words mein explained |
| completeness | What, Why, How, Examples sab covered |
| teaching_flow | Intro -> What -> Why -> How -> Examples -> Summary |

`overall_result` **code** nikalta hai (ek bhi FAIL = FAIL). LLM ka overall verdict ignore hota hai.

## Memory / self-evolving (sirf log nahi, actual use)

Har run ke baad `memory.json` mein save hota hai: failed checkpoint, reason, retry mein kya improvement hua
(fix), aur failure counts. Next run mein:

1. **Generator hints:** past failures + "kis change se fix hua" prompt mein inject hote hain.
2. **Rubric evolution:** jo checkpoint >= 2 baar fail hua, uski pass condition evaluator ke liye strict ho jaati hai.
3. **Recurring failures:** `--show-memory` se baar-baar fail hone wale instructions dikhte hain.

Test proof: Run 1 mein initial attempt FAIL -> Retry 1 PASS. Run 2 mein memory hints se pehli attempt hi PASS.

## Outputs

- `approved_lesson.md` - sirf PASS par. REJECTED par yeh file delete hoti hai.
- `rejection_log.json` / `.md` - har attempt ke failed checks, reasons, improvements.
- `memory.json` - saari runs ka data.

## Gemini (free) ya Claude se chalana

```bash
# Gemini (free tier) - key: https://aistudio.google.com/apikey
export GEMINI_API_KEY="your_key"        # Git Bash / Mac / Linux
python main.py --provider gemini --reset-memory --runs 3

# Claude
export ANTHROPIC_API_KEY="your_key"
python main.py --provider claude

# Auto: GEMINI_API_KEY -> ANTHROPIC_API_KEY -> mock
python main.py
```
Model badalna ho: `export GEMINI_MODEL=...` (default `gemini-2.5-flash`).
Free tier mein 429 (rate limit) aaye to code khud wait karke retry karta hai.
