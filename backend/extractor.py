import json
import os
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


class Deadline(BaseModel):
    title: str
    date: str  # ISO 8601, e.g. "2026-09-15"
    description: str | None = None


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text(extraction_mode="layout") for page in reader.pages)


def extract_deadlines(pdf_bytes: bytes, term_start_date: str | None = None) -> list[Deadline]:
    text = extract_text(pdf_bytes)

    if term_start_date:
        anchor_instruction = (
            f"The term/course begins on {term_start_date} (YYYY-MM-DD). "
            "Some items may be given as relative dates (e.g. a weekday name, "
            "'Week 3 Friday', 'Mon of Wk 5') instead of an absolute date. "
            "Use the term start date to resolve those into absolute YYYY-MM-DD dates. "
            "If an item's date genuinely cannot be resolved even with this anchor, omit it "
            "rather than guessing."
        )
    else:
        anchor_instruction = (
            "No term start date was provided. If an item's date is relative "
            "(e.g. just a weekday name like 'Monday', or 'Week 3') and cannot be resolved "
            "to an absolute calendar date without knowing when the term starts, omit that "
            "item rather than guessing a date."
        )

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are given the text of an academic document, which may or may not be a syllabus. "
                    "Extract every deadline, exam, and due date that is EXPLICITLY stated in the text, "
                    "with an explicit or resolvable associated date. "
                    "Do not infer, guess, or invent a date for an item that doesn't have one written down "
                    "and can't be resolved. "
                    f"{anchor_instruction} "
                    "If the document contains no deadlines (e.g. it's just a class meeting schedule, "
                    "room list, or has no dates at all), return an empty array. "
                    "Respond with ONLY a JSON array, no other text, matching this shape: "
                    '[{"title": str, "date": "YYYY-MM-DD", "description": str | null}]'
                ),
            },
            {"role": "user", "content": text},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].removeprefix("json").strip()
    items = json.loads(raw)
    return [Deadline(**item) for item in items]
