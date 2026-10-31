# ZAIO Handbook Assistant (RAG Assignment)

An AI assistant that answers student questions using the
**March 2026 Fullstack AI Engineer Bootcamp handbook.pdf**.

It searches the handbook for the most relevant text, sends that text to an LLM
(Claude, ChatGPT or Gemini - your choice), and returns a short answer plus the page it came from. If the handbook
doesn't contain the answer it replies:

> I could not find that information in the handbook.

**Assignment checklist:** see [REQUIREMENTS.md](REQUIREMENTS.md) for every
assignment requirement (Parts 1–5) and the exact code that meets it.

## Tools used (and why)

| Part | Tool | Why |
|---|---|---|
| Language | Python 3.10+ | Required by the assignment, huge AI ecosystem |
| Read PDF | `pypdf` | Pure Python, no extra system installs |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, runs locally, small (~90 MB), good quality |
| Vector database | `chromadb` | Saves to a folder on disk, no server needed, stores text + page numbers together |
| LLM | Claude (`anthropic`), ChatGPT (`openai`) or Gemini (`google-genai`), picked with `LLM_PROVIDER` in `.env` | Claude (`claude-opus-5-5`) is the default: strong at "answer only from this context" tasks |
| API | `fastapi` + `uvicorn` | Accepts/returns JSON, auto docs at `/docs`, easy to test, ready for n8n |
| Tests | `pytest` | The standard Python test runner |

**Recommended stack:** Python + Sentence Transformers + ChromaDB + FastAPI.

## Project structure

```
RAG Assignment/
├── .venv/                   # virtual environment (created by you)
├── data/
│   └── March 2026 Fullstack AI Engineer Bootcamp handbook.pdf
├── src/
│   ├── testing/
│   │   ├── test_api.py          # unit tests for the API (main.py)
│   │   ├── test_auth.py         # unit tests for LLM_PROVIDER and the API keys
│   │   ├── test_ingest.py       # unit tests for src/ingest.py
│   │   ├── test_retrieve.py     # unit tests for src/retrieve.py
│   │   └── run_questions.py     # Part 4: asks 10 questions, writes test_results.md
│   ├── ingest.py            # Part 1: load PDF -> text -> chunks -> embeddings -> ChromaDB
│   └── retrieve.py          # Part 2: embed question -> search -> build prompt -> ask the LLM
├── vectorstore/             # the ChromaDB database (created by src/ingest.py)
├── .env.example             # template for .env, with blank keys (safe to upload)
├── .env                     # your copy: LLM_PROVIDER + your API key (never upload this)
├── main.py                  # Part 3/5: FastAPI app with POST /ask and a simple web page
├── test_results.md          # Part 4 output
├── requirements.txt         # the Python packages to install (pip install -r ...)
├── REQUIREMENTS.md          # the assignment requirements, mapped to the code
├── GUIDE.txt                # step-by-step tutorial to build this from scratch
└── README.md
```

**Always run commands from the project folder** (the one with `main.py`).
The code uses relative paths like `data/...` and `vectorstore`, so running
from inside `src/` creates an empty extra `src/vectorstore/` folder.

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(macOS/Linux: `source .venv/bin/activate`)

### Choose the LLM and add your API key

Copy the template to make your own `.env` file (it stays on your computer):

```powershell
copy .env.example .env
```

(macOS/Linux: `cp .env.example .env`)

Open `.env`, set `LLM_PROVIDER` and paste the key for that provider (you
only need one key):

```
LLM_PROVIDER=claude
LLM_MODEL=
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=
GEMINI_API_KEY=
```

| `LLM_PROVIDER` | Key to fill in | Default model | Where to get the key |
|---|---|---|---|
| `claude` (default) | `ANTHROPIC_API_KEY` | `claude-opus-5-5` | https://platform.claude.com → Settings → API keys |
| `openai` (ChatGPT) | `OPENAI_API_KEY` | `gpt-5-nano` | https://platform.openai.com/api-keys |
| `gemini` | `GEMINI_API_KEY` | `gemini-3.8-flash` | https://aistudio.google.com/apikey |

`LLM_MODEL` is optional: fill it in to use a different model from the same
provider (e.g. `claude-sonnet-5-5`). Restart the server after changing `.env`.
`src/retrieve.py` reads `.env` with `python-dotenv`.

#### Getting a Claude API key

1. Go to https://platform.claude.com and sign up or log in.
2. Add credit under **Billing** (the API is pay-as-you-go and separate from a
   claude.ai Pro subscription; a question here costs a fraction of a cent).
3. Go to **Settings → API keys → Create key**, give it a name (e.g.
   `rag-assignment`) and create it.
4. Copy the key straight away: it starts with `sk-ant-` and is only shown once.
   If you lose it, delete it and create a new one.
5. Paste it after `ANTHROPIC_API_KEY=` in `.env` (no spaces or quotes).

Without a key the app still runs: it skips the LLM and returns the best
matching handbook text as the answer.

## Run

1. Build the vector database (only needed once, or when the PDF changes):

   ```powershell
   python src/ingest.py
   ```

2. Start the API:

   ```powershell
   uvicorn main:app --reload
   ```

3. Use it:
   - Browser: http://127.0.0.1:8000
   - Interactive docs: http://127.0.0.1:8000/docs
   - PowerShell:

     ```powershell
     Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question": "How much are the fees?"}'
     ```

## API

### `POST /ask`

Request:

```json
{ "question": "What is the attendance requirement?" }
```

Response (200):

```json
{ "answer": "...", "source": "Page 12" }
```

Not in the handbook (200):

```json
{ "answer": "I could not find that information in the handbook.", "source": "Not found" }
```

Invalid requests (400) always return JSON:

| Request | Response |
|---|---|
| body is not JSON | `{"error": "Invalid JSON"}` |
| body is not an object | `{"error": "Invalid request"}` |
| no `question` field | `{"error": "Missing question"}` |
| `question` is not a string | `{"error": "Question must be text"}` |
| `question` is blank | `{"error": "Question is empty"}` |

Unexpected server problems return 500 `{"error": "Something went wrong"}`.

"Source" is the PDF page number (page 1 = the cover), which is one more than
the number printed at the bottom of most handbook pages.

## Tests

Unit tests in `src/testing/` (no API key needed, the LLM and database are faked):

```powershell
python -m pytest -v
```

Part 4 test of the real assistant (API must be running in another terminal):

```powershell
python src/testing/run_questions.py
```

Results are written to [test_results.md](test_results.md).

## n8n readiness (Part 5)

- Accepts `Content-Type: application/json` POST bodies
- Always returns JSON, including for errors
- In n8n use an **HTTP Request** node: Method `POST`, URL
  `http://<your-pc-ip>:8000/ask`, Body Content Type `JSON`, body
  `{"question": "{{ $json.question }}"}`. Start uvicorn with `--host 0.0.0.0`
  if n8n runs on another machine or in Docker.
