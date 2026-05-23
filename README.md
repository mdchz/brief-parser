# BriefBot — AI Creative Brief Parser

Transforms messy creative briefs into structured, validated requirements — with confidence scoring and intelligent gap detection.

Paste an email, Slack thread, or Word doc. Get back 14 structured fields, per-field confidence levels, and the follow-up questions your team would forget to ask.

---

## How It Works

```
Unstructured Brief ──→ Claude Sonnet 4.6 (tool_use) ──→ 14-field extraction
                                                              │
                                                              ▼
                                                     Review Agent (Pass 2)
                                                              │
                                                              ▼
                                                  Validated JSON + Ambiguities
```

1. **Input** — Paste text or upload a file (TXT, PDF, DOCX, XLSX, CSV)
2. **Extract** — Claude extracts 14 structured fields via `tool_use` — the schema forces valid JSON, no regex parsing needed
3. **Self-Review** — A second-pass agent critiques the extraction: corrects errors, downgrades overconfident scores, surfaces missed ambiguities
4. **Output** — Structured spec with confidence badges, exportable as JSON, CSV, or Jira template

## Why Two Passes?

Single-pass extraction misses things. The review agent consistently finds:
- **~4 field corrections** per brief (wrong values, incomplete lists)
- **~4 confidence downgrades** (scores that were too optimistic)
- **~7 additional ambiguities** (questions a designer would need answered)

This catches 30%+ more issues than single-pass extraction alone.

## Key Design Decisions

| Decision | Why |
|----------|-----|
| `tool_use` for forced structure | The schema IS the prompt. No parsing, no hallucinated JSON. |
| Per-field confidence scoring | High = explicit, Medium = inferred, Low = guessed. Tells the team what to trust. |
| Ambiguity detection as a first-class field | Turns extraction into intelligence — surfaces what's missing, not just what's there. |
| Two-pass agentic loop | Extract then self-critique. The reviewer has different instructions and catches blind spots. |

## Prompts & Schema

All prompt logic lives in [`parser.py`](parser.py):

- **Extraction tool schema** (lines 6–91) — 14-field `tool_use` definition. Field descriptions carry the prompt intelligence.
- **System prompt** (lines 93–105) — Role assignment, extraction rules, confidence level definitions.
- **Review agent** (lines 108–166) — Second-pass tool schema: corrections, confidence downgrades, missed ambiguities.

## Run Locally

```bash
# Requires AWS credentials configured for Amazon Bedrock access
pip install -r requirements.txt
streamlit run app.py
```

Supports file uploads (TXT, PDF, DOCX, XLSX, CSV) and includes three built-in example briefs for testing.

## Tech Stack

| Component | Choice |
|-----------|--------|
| LLM | Claude Sonnet 4.6 via Amazon Bedrock (`us.anthropic.claude-sonnet-4-6`) |
| Structured output | Claude `tool_use` with forced tool choice |
| Framework | Streamlit |
| Language | Python |

## Project Structure

```
brief-parser/
├── parser.py          # Core extraction + review agent logic
├── app.py             # Streamlit UI with dark theme
├── examples/          # Sample briefs (email, Slack, Word doc)
├── requirements.txt   # Python dependencies
└── README.md
```
