# BriefBot — AI Creative Brief Parser

An AI-powered tool that transforms messy creative briefs into structured requirements with confidence scoring and intelligent gap detection.

**What it does:** Paste any creative brief — an email, Slack thread, Word doc — and get structured deliverables, field-level confidence scores, and smart follow-up questions that catch ambiguities humans miss.

## How It Works

1. **Input** — Paste text or upload a file (TXT, PDF, DOCX, XLSX, CSV)
2. **Extract** — Claude Sonnet 4.6 (via Amazon Bedrock) extracts 14 structured fields using tool_use for guaranteed JSON output
3. **Review** — A second-pass agent self-critiques the extraction: corrects errors, downgrades overconfident scores, adds missed ambiguities
4. **Output** — Structured spec with confidence badges + exportable as JSON, CSV, or Jira template

## Architecture

```
Unstructured Brief → Streamlit UI → Claude (tool_use, 14-field schema)
                                         ↓
                                   Pass 1: Extract
                                         ↓
                                   Pass 2: Review Agent
                                         ↓
                                   Validated JSON + Ambiguities
```

**Key design decisions:**
- **Tool_use for forced structure** — No regex parsing. The schema IS the prompt.
- **Confidence scoring** — High (explicit), Medium (inferred), Low (guessed)
- **Ambiguity detection** — A meta-field that asks "what's missing?" — turns extraction into intelligence
- **Two-pass agent** — Extract then self-critique. Catches 30%+ more issues than single-pass.

## Prompts

### Extraction Schema (14 fields)
See [`parser.py`](parser.py) lines 6-91 — the `EXTRACTION_TOOL` definition with field descriptions that carry all the prompt intelligence.

### System Prompt
See [`parser.py`](parser.py) lines 93-105 — short role assignment + extraction rules + confidence level definitions.

### Review Agent
See [`parser.py`](parser.py) lines 108-166 — second-pass tool that returns corrections, confidence downgrades, and missed ambiguities.

## Run Locally

```bash
# Requires AWS credentials configured for Bedrock access
pip install -r requirements.txt
streamlit run app.py
```

## Demo Video

[Watch the 7-minute demo](demo_video.mp4) showing:
- The painful manual workflow today
- Building process: tool choices, prompt evolution, debugging
- Live demo on 3 formats (email, Slack, Word doc)

## Tech Stack

- **LLM:** Claude Sonnet 4.6 via Amazon Bedrock (inference profile: `us.anthropic.claude-sonnet-4-6`)
- **Framework:** Streamlit
- **Language:** Python
- **Key pattern:** tool_use for forced structured output + two-pass agentic review
