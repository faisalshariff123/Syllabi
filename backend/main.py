import json

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from extractor import Deadline, extract_deadlines

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExportRequest(BaseModel):
    deadlines: list[Deadline]


@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI application!"}


@app.post("/extract")
@limiter.limit("5/minute")
async def extract(request: Request, file: UploadFile = File(...)) -> list[Deadline]:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await file.read()
    try:
        return extract_deadlines(pdf_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="LLM returned malformed JSON, try again")
    except ValidationError:
        raise HTTPException(status_code=502, detail="LLM output didn't match the expected deadline format")


@app.post("/export")
def export(req: ExportRequest) -> Response:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0"]
    for d in req.deadlines:
        ics_date = d.date.replace("-", "")
        lines += [
            "BEGIN:VEVENT",
            f"SUMMARY:{d.title}",
            f"DTSTART;VALUE=DATE:{ics_date}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    ics = "\r\n".join(lines)
    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=deadlines.ics"},
    )
