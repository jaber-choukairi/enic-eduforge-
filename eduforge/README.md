# EduForge — AI Exam Generation System

Upload course materials (PDF, DOCX, TXT) → generate professional exams using AI.

---

## Your Setup
- **Python**: 3.10.10 in `.venv`
- **Database**: PostgreSQL 17 local (port 5432)
- **Docker**: Redis + ChromaDB + MLflow
- **AI**: Groq API (free — llama-3.3-70b)

---

## Every Session — Start These 2 Terminals

### Terminal 1 — API
```powershell
cd C:\Users\MSI\Downloads\eduforge
$env:PYTHONPATH = "."
$env:DATABASE_URL = "postgresql://eduforge:eduforge@127.0.0.1:5432/eduforge"
.venv\Scripts\python.exe -m uvicorn services.gateway.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2 — UI
```powershell
cd C:\Users\MSI\Downloads\eduforge
$env:PYTHONPATH = "."
$env:DATABASE_URL = "postgresql://eduforge:eduforge@127.0.0.1:5432/eduforge"
.venv\Scripts\python.exe -m streamlit run ui/dashboard.py
```

Open http://localhost:8501 — login: `teacher / teacher123`

---

## First-Time Setup

```powershell
# 1. Create and activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Docker services
docker compose up -d redis chromadb mlflow

# 4. Create DB tables + demo users
$env:PYTHONPATH = "."
$env:DATABASE_URL = "postgresql://eduforge:eduforge@127.0.0.1:5432/eduforge"
.venv\Scripts\python.exe scripts/cli.py setup

# 5. Add your Groq API key to .env
# Get free key at https://console.groq.com
# Edit .env → set GROQ_API_KEY=gsk_...
```

---

## Workflow

1. **Upload Material** → PDF/DOCX of your course
2. **Wait ~30s** → status changes PENDING → READY (28+ chunks)
3. **Generate Exam** → select material, choose question types & count
4. **My Exams** → Export Markdown (teacher copy with answers)

---

## Groq API Key
Get your free key at https://console.groq.com → API Keys → Create
Add to `.env`:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxx
```

---

## Troubleshooting

**Material stuck at PENDING:**
```powershell
pip install "numpy<2" sentence-transformers --upgrade
# Then click Retry button on the material card
```

**VectorDB red in UI:**
```powershell
docker start eduforge-chroma
```

**DB connection error:**
```powershell
# Check local Postgres is running
Get-Service postgresql*
```

---

## Credentials
| Role | Username | Password |
|------|----------|----------|
| Teacher | teacher | teacher123 |
| Admin | admin | admin123 |

---

## Architecture
```
Browser (Streamlit :8501)
    └── FastAPI (:8000)
            ├── PostgreSQL 17 local (:5432)  — users, materials, exams, questions
            ├── Redis Docker (:6379)          — task queue
            ├── ChromaDB Docker (:8100)       — vector embeddings
            └── Groq API (cloud)             — LLM question generation

PDF Upload → TextExtractor → TextChunker → EmbeddingEngine → ChromaDB
                                                                    ↓
Generate Exam → retrieve chunks → PromptBuilder → Groq API → QuestionParser → DB
```