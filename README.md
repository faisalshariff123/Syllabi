# Syllabus → Calendar

Turns a course syllabus PDF into an importable `.ics` calendar of every deadline and exam.
Built as a real, measurable AI project — not a wrapper. The point of interest is the
**evaluation harness** that scores extraction accuracy, plus a **human-in-the-loop
confirmation** step before anything is exported.

## Architecture (one flow)

```
PDF ──► extract text (pypdf) ──► LLM extract dates → JSON (extractor.py)
                                          │
                                          ▼
                          eval harness scores vs ground truth (eval/run_eval.py)
                                          │
                          user reviews & edits deadlines (frontend)
                                          │
                                          ▼
                               export .ics (ics_export.py)
```

Two design decisions worth defending in an interview:
1. **Term dates are fed to the model** so relative dates ("Week 3 Friday") resolve to
   real calendar dates. Biggest single lever on accuracy.
2. **/extract and /export are separate** so the user confirms/edits before export.
   No date extractor is perfect; the product owns that honestly instead of hiding it.

## Run locally

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in LLM_API_KEY / LLM_MODEL (and LLM_BASE_URL for OpenRouter)
uvicorn main:app --reload --port 8000
```

Frontend (no build step):
```bash
cd frontend
python -m http.server 5173
# open http://localhost:5173  (backend must be running on :8000)
```

## Deploy (Week 1 milestone: a live link)

- Backend → Render web service: build `pip install -r requirements.txt`,
  start `uvicorn main:app --host 0.0.0.0 --port $PORT`, set env vars from `.env`.
- Frontend → Render static site (or Netlify/Vercel). Set the `API` value at the top of
  `index.html` (or in localStorage) to your deployed backend URL, and restrict CORS
  `allow_origins` in `main.py` to that frontend origin.

## The eval harness (Week 2 — the resume-maker)

1. Collect 15–20 real syllabi (yours + friends'). Put the PDFs in `eval/pdfs/`.
2. Copy `eval/ground_truth.example.json` to `eval/ground_truth.json` and hand-label the
   correct deadlines for each. This is your ground truth — be accurate.
3. Run it:
   ```bash
   cd eval
   python run_eval.py --truth ground_truth.json --pdfs pdfs/
   ```
4. Read the failure log. Fix the prompt / parsing. Re-run. Watch **date accuracy** climb.
   Record your before/after — that delta is your headline resume number.

Test the scorer without spending tokens (pass a predictions file):
```bash
python run_eval.py --truth ground_truth.json --predictions some_predictions.json
```

**Known refinement (good interview material):** title matching is greedy fuzzy matching,
so near-identical names like "Final project" vs "Final exam" can mis-pair. Improving this
(e.g. global/Hungarian assignment, or matching on date+title jointly) is a real
eval-design problem worth doing and worth talking about.

## What ships each week

- **Week 1:** upload → extract → edit → download, deployed. A link you can send.
- **Week 2:** eval harness + accuracy number; iterate the prompt to raise it.
- **Week 3:** polish the confirm/edit UI, add a usage counter, launch in class group
  chats / SJSU CS Discord the week before a semester or midterms.

## Resume bullet this earns (fill in real numbers)

> Built and deployed a tool converting syllabus PDFs into importable calendars
> (FastAPI, LLM extraction, React); designed an evaluation harness over 20 hand-labeled
> syllabi that raised date-extraction accuracy from X% to Y%, with a human-in-the-loop
> confirmation step. Used by N students.
