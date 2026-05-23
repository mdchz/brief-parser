import json
from anthropic import AnthropicBedrock

client = AnthropicBedrock(aws_region="us-east-1")

EXTRACTION_TOOL = {
    "name": "extract_brief_requirements",
    "description": "Extract structured requirements from a creative brief",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Name or title of the project/campaign"
            },
            "brand": {
                "type": "string",
                "description": "Brand or client name"
            },
            "asset_type": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Types of creative assets needed (Banner, Video, Social, Email, Landing Page, etc.)"
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Size specifications, aspect ratios, or format requirements"
            },
            "channels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Distribution channels (Instagram, Programmatic Display, Email, etc.)"
            },
            "target_audience": {
                "type": "string",
                "description": "Who the creative is targeting"
            },
            "key_message": {
                "type": "string",
                "description": "Primary message or value proposition"
            },
            "cta": {
                "type": "string",
                "description": "Call to action text"
            },
            "brand_guidelines": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Color, font, style, and other brand constraints"
            },
            "deliverables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "format": {"type": "string"},
                        "quantity": {"type": "integer"}
                    },
                    "required": ["description"]
                },
                "description": "List of specific deliverables with details"
            },
            "deadline": {
                "type": "string",
                "description": "Due date or timeline if specified"
            },
            "stakeholders": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Names and roles of people mentioned"
            },
            "ambiguities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Things the brief didn't specify clearly that should be clarified before starting work"
            },
            "confidence": {
                "type": "object",
                "description": "Per-field confidence level (high, medium, low) for each extracted field",
                "additionalProperties": {"type": "string", "enum": ["high", "medium", "low"]}
            }
        },
        "required": [
            "project_name", "brand", "asset_type", "dimensions", "channels",
            "target_audience", "key_message", "cta", "brand_guidelines",
            "deliverables", "deadline", "stakeholders", "ambiguities", "confidence"
        ]
    }
}

SYSTEM_PROMPT = """You are a creative operations specialist who extracts structured requirements from unstructured creative briefs.

Your job is to parse messy, informal, or scattered brief content and extract every actionable requirement into structured fields. You must:

1. Extract ALL requirements mentioned, even if buried in casual language
2. Infer reasonable values when strongly implied (mark confidence as "medium")
3. Flag anything ambiguous or missing as an "ambiguity" that needs clarification
4. Assign confidence levels to each field:
   - "high": explicitly stated in the brief
   - "medium": strongly implied or inferred from context
   - "low": guessed or partially specified

Be thorough with ambiguities — these save the creative team from having to go back and ask questions later. Think about what a designer would need to know that isn't clearly stated."""


REVIEW_TOOL = {
    "name": "review_extraction",
    "description": "Review and correct a previous extraction, returning only the corrections",
    "input_schema": {
        "type": "object",
        "properties": {
            "corrections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "description": "Field name to correct"},
                        "issue": {"type": "string", "description": "What was wrong or missed"},
                        "corrected_value": {"description": "The corrected value (same type as original field)"}
                    },
                    "required": ["field", "issue", "corrected_value"]
                },
                "description": "List of corrections to apply"
            },
            "confidence_downgrades": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "from_level": {"type": "string"},
                        "to_level": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["field", "to_level", "reason"]
                },
                "description": "Fields whose confidence should be lowered"
            },
            "missed_ambiguities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional ambiguities the first pass missed"
            },
            "assessment": {
                "type": "string",
                "enum": ["pass", "minor_corrections", "significant_corrections"],
                "description": "Overall quality of the first extraction"
            }
        },
        "required": ["corrections", "confidence_downgrades", "missed_ambiguities", "assessment"]
    }
}

REVIEW_SYSTEM = """You are a quality reviewer for creative brief extractions. You receive:
1. The original brief text
2. A previous extraction attempt (JSON)

Your job is to find errors, missed information, and overconfident scores. Be critical. Check:
- Are any extracted values wrong or incomplete?
- Are confidence scores too high for vague or ambiguous information?
- Did the first pass miss any ambiguities a designer would care about?
- Are deliverables complete — did it miss any implied items?

Only flag real issues. If the extraction is solid, say assessment: "pass" with empty corrections."""


def parse_brief(brief_text: str, use_review=True) -> dict:
    """Extract requirements with optional agent review loop."""
    # Pass 1: Extract
    response = client.messages.create(
        model="us.anthropic.claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_brief_requirements"},
        messages=[
            {
                "role": "user",
                "content": f"Parse this creative brief and extract all structured requirements:\n\n---\n{brief_text}\n---"
            }
        ]
    )

    extraction = None
    for block in response.content:
        if block.type == "tool_use":
            extraction = block.input
            break

    if not extraction:
        return {"error": "Failed to extract requirements"}

    if not use_review:
        extraction["_agent"] = {"passes": 1, "review": "skipped"}
        return extraction

    # Pass 2: Review agent evaluates the extraction
    review_response = client.messages.create(
        model="us.anthropic.claude-sonnet-4-6",
        max_tokens=4096,
        system=REVIEW_SYSTEM,
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "review_extraction"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"ORIGINAL BRIEF:\n---\n{brief_text}\n---\n\n"
                    f"EXTRACTION RESULT:\n```json\n{json.dumps(extraction, indent=2)}\n```\n\n"
                    "Review this extraction. Find any errors, missed ambiguities, or overconfident scores."
                )
            }
        ]
    )

    review = None
    for block in review_response.content:
        if block.type == "tool_use":
            review = block.input
            break

    if not review:
        extraction["_agent"] = {"passes": 2, "review": "failed_to_parse"}
        return extraction

    # Apply corrections
    for correction in review.get("corrections", []):
        field = correction.get("field")
        if field and field in extraction:
            extraction[field] = correction["corrected_value"]

    # Apply confidence downgrades
    for downgrade in review.get("confidence_downgrades", []):
        field = downgrade.get("field")
        if field and "confidence" in extraction:
            extraction["confidence"][field] = downgrade["to_level"]

    # Merge missed ambiguities
    missed = review.get("missed_ambiguities", [])
    if not isinstance(missed, list):
        missed = [missed] if missed else []
    if missed:
        existing = extraction.get("ambiguities", [])
        if not isinstance(existing, list):
            existing = [existing] if existing else []
        extraction["ambiguities"] = existing + missed

    # Attach agent metadata
    extraction["_agent"] = {
        "passes": 2,
        "review": review.get("assessment", "unknown"),
        "corrections_applied": len(review.get("corrections", [])),
        "confidence_downgrades": len(review.get("confidence_downgrades", [])),
        "ambiguities_added": len(missed),
    }

    return extraction
