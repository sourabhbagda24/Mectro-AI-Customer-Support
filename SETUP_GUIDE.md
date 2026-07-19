# Mectro AI Customer Support — Setup Guide

Your project's README already had excellent documentation, but the zip was missing a few files it references, so nothing would actually run out of the box. I added them and fixed a couple of config issues. Here's what changed and how to get the project running end to end.

## What was missing / fixed

| Issue | Fix |
|---|---|
| `database/schema.sql` — referenced in README, not in zip | Created, matches the README's table design (`policies`, `orders`, `support_logs`) |
| `database/seed_data.sql` — referenced in README, not in zip | Created, with the 4 policies and 6 sample orders (including `ORD1001` used in the README's walkthrough) |
| `.env.example` — referenced in README, not in zip | Created |
| Root `main.py` was empty | Added a convenience runner (`python main.py`) |
| `.python-version` pinned `3.14` | Changed to `3.11` — the pinned `langchain`/`pydantic`/`sqlalchemy` versions in `requirements.txt` are not guaranteed to work on 3.14 yet; 3.11 is safe |
| `requirements.txt` had duplicate/unused `sqlalchemy` and `pandas` entries | Removed — `pandas` isn't used anywhere in the code |
| `pyproject.toml` had `requires-python = ">=3.14"` and no dependencies listed | Aligned with `requirements.txt` and the new Python version range |

## Steps to establish the project

### 1. Install prerequisites
- Python 3.11 (or 3.12)
- MySQL Server 8.x running locally or reachable remotely
- A free [Groq API key](https://console.groq.com/keys)

### 2. Create the database
```bash
cd Mectro-AI-Customer-Support-main
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed_data.sql
```
This creates the `mectro_support` database with the `policies`, `orders`, and `support_logs` tables, and loads sample data.

### 3. Configure environment variables
```bash
cp .env.example .env
```
Then edit `.env` with your real Groq key and MySQL credentials.

### 4. Set up Python and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run the app
```bash
python main.py
# or: uvicorn app.main:app --reload
```

### 6. Verify
| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/` | Frontend console |
| `http://127.0.0.1:8000/docs` | Swagger API docs |
| `http://127.0.0.1:8000/health` | Health check — should return `{"status": "ok"}` |

Try a query like *"What's the status of my order ORD1001?"* — it should return the sample data for Aditi Sharma's shipped order.

## One thing worth knowing about the code itself
The README describes Agent 2 (`sql_agent.py`) as a real LangChain `create_tool_calling_agent` + `AgentExecutor` that decides which tool to call. In the actual code, it's a plain Python `if/elif` on the detected intent that calls the matching tool directly — functionally reliable, but not literally an LLM-driven tool-calling agent. Not a blocker for running the project, just worth knowing if this needs to match an assignment's specific requirement about agent architecture.
