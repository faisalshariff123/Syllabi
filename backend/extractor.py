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
    return "\n".join(page.extract_text() for page in reader.pages)


def extract_deadlines(pdf_bytes: bytes) -> list[Deadline]:
    text = extract_text(pdf_bytes)

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract every deadline, exam, and due date from this syllabus. "
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
