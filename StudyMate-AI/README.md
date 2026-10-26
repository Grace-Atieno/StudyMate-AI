# StudyMate AI

StudyMate AI is a small web app for students. You upload your notes (PDF, DOCX or TXT) and it gives you a short summary and a five-question multiple-choice quiz generated with Google's Gemini API. It started as an entry for the AI for Students Hackathon.

## What works

- Upload a `.pdf`, `.docx` or `.txt` file (up to 5 MB by default)
- AI-written summary
- Five-question quiz you can answer in the page, with instant feedback and a score
- Files are read in memory and never saved to disk

There are no user accounts and no database. Nothing is stored between requests.

## Tech stack

- Backend: Python 3.10+, Flask, Flask-CORS, Flask-Limiter, `google-genai`, python-docx, PyMuPDF
- Frontend: plain HTML, CSS and JavaScript (no build step)

## Project structure

```
backend/    Flask API (app.py), requirements, tests
frontend/   Static page (index.html, script.js, style.css)
database/   Unused Firebase placeholder from the first prototype
```

## Setup

You need Python 3.10 or newer and a Gemini API key from https://aistudio.google.com/.

```bash
git clone https://github.com/Grace-Atieno/StudyMate-AI.git
cd StudyMate-AI/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # then edit .env and add your key
python app.py                    # API on http://127.0.0.1:5000
```

In a second terminal, serve the frontend:

```bash
cd StudyMate-AI/frontend
python -m http.server 8080       # open http://127.0.0.1:8080
```

The app refuses to start if `GEMINI_API_KEY` is missing.

## Configuration

All settings are environment variables (see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Your Gemini key (required) | none |
| `GEMINI_MODEL` | Model name | `gemini-2.5-flash` |
| `ALLOWED_ORIGINS` | Comma-separated origins allowed by CORS | none (blocks all browsers) |
| `MAX_UPLOAD_MB` | Upload size limit | `5` |
| `MAX_TEXT_CHARS` | Characters of notes sent to the AI | `30000` |
| `RATELIMIT_STORAGE_URI` | Rate-limit store; use Redis if running several processes | `memory://` |
| `TRUST_PROXY` | Set to `1` behind one trusted reverse proxy | `0` |

If you serve the frontend from a different address or port, add it to `ALLOWED_ORIGINS` and update `API_URL` at the top of `frontend/script.js` (plus `connect-src` in the CSP `<meta>` tag in `index.html`).

## Tests and checks

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q tests
pip-audit -r requirements.txt
```

The tests cover upload validation, fake file types, size limits, CORS, security headers, rate limiting and the fail-closed key check. The Gemini call is mocked, so the tests don't need a key and **the live AI call has not been tested in this repo's test suite**.

## Security notes

- The API key lives only in the environment, never in code.
- Uploads are validated by extension and file signature, size-limited, and handled in memory.
- CORS only allows the origins you list. Uploads are rate-limited to 10 per minute per IP.
- AI output is validated on the server and inserted into the page with `textContent`, so it can't inject HTML.
- The notes are passed to the model as data with an instruction to ignore commands inside them. That reduces prompt injection but can't fully prevent it, so the worst case is a bad summary or quiz.
- Responses carry `nosniff`, `no-referrer`, `no-store` and a restrictive CSP; HSTS is added over HTTPS.

## Production

Don't use `python app.py` in production. Run behind HTTPS with a real server, for example:

```bash
gunicorn -w 2 -b 127.0.0.1:5000 "app:create_app()"
```

Set `TRUST_PROXY=1` only if exactly one proxy sits in front, use a Redis `RATELIMIT_STORAGE_URI`, and set `ALLOWED_ORIGINS` to your real site. Host the `frontend/` folder on any static host. Gemini free-tier limits and data-use terms apply to whatever notes your users upload.

## Known limitations

- Scanned PDFs (images only) have no extractable text and will be rejected.
- Only the first 30,000 characters of long notes are used.
- No accounts, history or saved quizzes. The Firebase file in `database/` is an unused placeholder.
- There are no frontend or end-to-end tests yet.
- There is no LICENSE file, so no license is granted yet. Add one before sharing the code.

## Troubleshooting

- **"Could not reach the server"**: the backend isn't running, or `API_URL` is wrong.
- **Browser CORS error**: add the page's origin to `ALLOWED_ORIGINS` and restart the backend.
- **"The AI service is unavailable"**: check the key, quota and `GEMINI_MODEL`; the backend log has details.
