## Kuveka Scores Assessment

A lightweight Django + DRF service that scores uploaded leads against a submitted offer using a rules layer plus an AI intent layer (Gemini). It exposes simple REST endpoints to upload an offer, upload leads (CSV), run scoring, fetch results, and download results.

Deployed on Render: `https://kuveka-scores-assessment.onrender.com`

Loom demo: add your Loom link here


## Quick Start

### Prerequisites
- Python 3.11+
- pip
- A Google Gemini API key

### Clone and install
```bash
git clone https://github.com/your-org/kuveka-scores-assessment.git
cd kuveka-scores-assessment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Environment variables
Create a `.env` file in the project root with the following keys (these are read in `backend/settings.py` via `python-dotenv`):
```bash
SECRET_KEY=replace-with-a-strong-secret
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1
GEMINI_API_KEY=your-gemini-api-key
```

Notes:
- `DEBUG` should be `False` in production.
- `DJANGO_ALLOWED_HOSTS` is space-separated.
- On Render, set these in the Dashboard → Environment.

### Run migrations and start server
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Base URL locally: `http://localhost:8000/`


## API Endpoints
Base path for app: `/scores/`

### 1) Upload Offer
- Method: POST
- URL: `/scores/offer/`
- Body (JSON):
```json
{
  "product_name": "Acme Sales Copilot",
  "value_prop": "Automate outreach and qualify leads",
  "ideal_use_cases": ["SaaS", "B2B", "Financial Services"],
  "target_roles": ["Head of Sales", "VP Growth"]
}
```
- cURL:
```bash
curl -X POST http://localhost:8000/scores/offer/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Acme Sales Copilot",
    "value_prop": "Automate outreach and qualify leads",
    "ideal_use_cases": ["SaaS", "B2B", "Financial Services"],
    "target_roles": ["Head of Sales", "VP Growth"]
  }'
```

### 2) Upload Leads (CSV)
- Method: POST (multipart/form-data)
- URL: `/scores/leads/upload/`
- Form field: `file` (CSV file)
- CSV headers expected: `name,role,company,industry,location,linkedin_bio`
- cURL:
```bash
curl -X POST http://localhost:8000/scores/leads/upload/ \
  -F "file=@./sample_leads.csv"
```

Sample CSV file content:
```csv
name,role,company,industry,location,linkedin_bio
Jane Doe,Head of Sales,Acme Corp,SaaS,NY,Sales leader with 10+ years in B2B SaaS
John Smith,Engineer,Widgets Inc,Manufacturing,SF,Building internal tools
```

### 3) Run Scoring
- Method: POST
- URL: `/scores/score/`
- Body: empty JSON `{}` is fine
- cURL:
```bash
curl -X POST http://localhost:8000/scores/score/ -H "Content-Type: application/json" -d '{}'
```

### 4) Fetch Results
- Method: GET
- URL: `/scores/results/`
- cURL:
```bash
curl http://localhost:8000/scores/results/
```

### 5) Download Results (CSV)
- Method: GET
- URL: `/scores/results/download/`
- cURL:
```bash
curl -L -o scored_results.csv http://localhost:8000/scores/results/download/
```

Notes:
- The current in-memory implementation stores the last uploaded offer and leads and returns a single combined result object for the first lead in the CSV.
- For multi-user or multi-lead scenarios, a persistence layer and batch output format would be preferred.


## Rule Logic and AI Prompt
Implemented in `scores/utils.py`.

### Rule Layer
- **Role relevance**: Maps roles to points via keyword matching.
  - Decision maker keywords: `ceo, founder, head, vp, director, coo, cto, cfo` → +20
  - Influencer keywords: `manager, specialist, tech lead, sales head` → +10
  - Others → +0
- **Industry match**: Compares `lead.industry` to items in `offer.ideal_use_cases` using exact, substring, or fuzzy match (difflib ratio > 0.3) → +20 (exact) / +10 (partial) / +0
- **Data completeness**: All fields present → +10

### AI Layer
- Model: Gemini `gemini-2.5-flash` via `google.genai` client.
- Prompt (structured JSON output requested):
```text
You are a sales assistant. Given the product/offer details and the lead info, classify the buying intent as High, Medium, or Low and provide 1-2 sentence reasoning. Respond ONLY in JSON: {"intent": "<High/Medium/Low>", "reasoning": "<reasoning>"}
```
- Post-processing:
  - Intent mapping to points: High → 50, Medium → 30, Low → 10
  - Final total = rule points + AI points
  - Intent thresholds: ≥ 70 → High, ≥ 40 → Medium, else Low


## Testing
Current automated tests are minimal. Validation performed for this assessment:
- Postman flows for happy paths and error cases:
  - Offer missing → `400`
  - Leads file missing → `400`
  - Score before uploads → `400`
  - Results before scoring → `404`
- Manual CSV parsing validation with sample data.
- AI layer sanity checks for JSON-only responses and intent mapping.

Potential test additions (not yet included):
- Unit tests for `industry_match`, `calculate_rule_score`, and thresholding.
- Contract tests for endpoints with fixtures.
- Mocked AI client for deterministic scoring in CI.


## Why `runserver` instead of Gunicorn
- For a small assessment and to simplify local setup, `python manage.py runserver` is sufficient.
- It avoids extra infra and configuration while demonstrating the core scoring logic and API design.
- In production, you would deploy behind a production WSGI/ASGI server (e.g., Gunicorn/Uvicorn) with proper process management and static/media handling.


## Deployment (Render)
The app is deployed to Render at `https://kuveka-scores-assessment.onrender.com`.

High-level steps:
- Service type: Web Service
- Start command: `python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT`
- Environment: Python 3.11
- Environment variables: set `SECRET_KEY`, `DEBUG=False`, `DJANGO_ALLOWED_HOSTS="kuveka-scores-assessment.onrender.com"`, `GEMINI_API_KEY`


## Postman Collection (optional)
If desired, export a Postman collection with the five endpoints above and include it under `docs/postman_collection.json`.


## Local development tips
- Use a dedicated `.env` and never commit secrets.
- If you hit AI quota/latency, temporarily stub the AI call in `ai_intent_score` and return a fixed intent for development.
- CSVs should be UTF-8 encoded; headers must match exactly.


## Limitations and Future Improvements
- In-memory storage of offer/leads/results; not multi-user safe. Replace with database models keyed per session or user.
- Only the first lead in the uploaded CSV is currently scored end-to-end. Extend to batch scoring and return a list of results.
- Add retries and structured error handling for AI client; validate and sanitize JSON responses more robustly.
- Add comprehensive tests and CI with mocked AI.
- Swap `runserver` with Gunicorn/Uvicorn in production and add Docker healthchecks.


## Repository Structure
```text
backend/               # Django project settings and URLs
scores/                # App with endpoints, utils, and scoring logic
  ├─ urls.py           # /scores/* routes
  ├─ views.py          # DRF APIViews for upload/score/results
  ├─ utils.py          # CSV parsing, rule scoring, AI prompt, final scoring
  └─ models.py         # (empty for now; future persistence)
manage.py
requirements.txt
Dockerfile
docker-compose.yaml    # (optional; not strictly required for local run)
```


## License
MIT or as specified by the hosting repository.
