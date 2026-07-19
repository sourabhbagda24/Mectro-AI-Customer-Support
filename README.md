# Mectro AI Customer Support System

An AI-powered customer support system for **Mectro Company**, built with **LangChain Agents**, **MySQL**, **Groq (LLaMA 3.3)**, and **FastAPI**.

It reads a raw customer message, figures out what the customer wants, looks up the real answer in a MySQL database, and writes a professional reply back — fully automatically, through three separate AI agents chained together.

> **Business scenario this solves:** A customer types *"I would like to know your refund policy."* The system detects the intent (`refund_policy`), pulls the actual refund policy text out of MySQL, and generates a natural, professional response — without a human agent having to type anything.

---

## Table of Contents

1. [What this project does](#what-this-project-does)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [File-by-file explanation](#file-by-file-explanation)
6. [Database design](#database-design)
7. [The three agents, in detail](#the-three-agents-in-detail)
8. [The frontend](#the-frontend)
9. [Setup & installation](#setup--installation)
10. [Running the project](#running-the-project)
11. [API reference](#api-reference)
12. [Example walkthrough](#example-walkthrough)
13. [Design decisions & trade-offs](#design-decisions--trade-offs)

---

## What this project does

Mectro receives hundreds of customer support messages a day about six recurring topics:

- Order Status
- Refund Policy
- Order Cancellation
- Payment Issues
- Shipping Information
- Return Policy

Instead of a human reading every message, this system runs each one through an automated **3-agent pipeline**:

```
Customer types a message
        │
        ▼
Agent 1 — figures out WHAT they're asking about
        │
        ▼
Agent 2 — looks up the REAL answer in MySQL
        │
        ▼
Agent 3 — writes a professional REPLY using that real data
        │
        ▼
Customer receives the final response
```

No agent does more than one job. That separation is intentional — it's the "single responsibility" requirement the whole project is built around.

---

## Architecture

```
┌────────────────────┐    ┌────────────────────────┐    ┌─────────────────────────┐    ┌───────────────────────────┐
│   Customer Query    │──▶ │ Intent Detection Agent │──▶ │  MySQL Database Agent   │──▶ │ Response Generator Agent  │
│  (raw text input)   │    │ (LLM, structured out)  │    │ (LangChain tool-calling)│    │      (LLM, prose)         │
└────────────────────┘    └────────────────────────┘    └─────────────────────────┘    └───────────────────────────┘
                                                                       │
                                                                       ▼
                                                            ┌───────────────────────┐
                                                            │     MySQL Database     │
                                                            │  policies / orders      │
                                                            └───────────────────────┘
```

Everything is orchestrated by plain, sequential Python (`app/orchestrator.py`) — **not** LangGraph. Each agent is called one after another, and its output is passed as input to the next. There is no shared agent memory, no vector database, and no embeddings anywhere in this project — by design, per the assignment's constraints.

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| LLM | **Groq** (`llama-3.3-70b-versatile`) | Fast, free-tier-friendly inference |
| Agent framework | **LangChain** (`create_tool_calling_agent`, `AgentExecutor`, structured output) | Required by the assignment; no LangGraph |
| Database | **MySQL** | Required by the assignment; stores policies and orders |
| DB access | **SQLAlchemy** + **PyMySQL** | Safe, parameterised queries (no raw SQL from the LLM) |
| API layer | **FastAPI** | Serves the pipeline as an HTTP endpoint |
| Validation | **Pydantic** | Structured intent output + request/response schemas |
| Config | **python-dotenv** | Keeps API keys and DB credentials out of source code |
| Frontend | Plain **HTML/CSS/JS** (no framework) | Single file, zero build step, served directly by FastAPI |

---

## Project structure

```
support_system/
├── app/
│   ├── main.py                    # FastAPI app: routes, CORS, serves the frontend
│   ├── config.py                  # Loads .env into a Settings object
│   ├── database.py                # SQLAlchemy engine + safe, parameterised DB queries
│   ├── tools.py                   # LangChain @tool wrappers around database.py
│   ├── orchestrator.py            # Runs the 3 agents in sequence
│   ├── __init__.py
│   └── agents/
│       ├── intent_agent.py        # Agent 1 — Intent Detection
│       ├── sql_agent.py           # Agent 2 — MySQL Database Agent
│       ├── response_agent.py      # Agent 3 — Response Generator
│       └── __init__.py
├── static/
│   └── index.html                 # Frontend UI (black & white "receipt printer" console)
├── database/
│   ├── schema.sql                 # CREATE TABLE statements (policies, orders, support_logs)
│   └── seed_data.sql              # Sample policy text + sample orders
├── requirements.txt                # Pinned Python dependencies
├── .env.example                    # Template for required environment variables
└── README.md                       # This file
```

---

## File-by-file explanation

### `app/config.py`
Reads environment variables (via `python-dotenv`) into a single `Settings` object: the Groq API key/model, and the MySQL host/port/user/password/database name. Everything else in the app imports `settings` from here instead of calling `os.getenv` directly, so there's exactly one place that knows how configuration is loaded.

### `app/database.py`
The **only** file that talks to MySQL directly. It:
- Creates a single SQLAlchemy engine (`create_engine`, reused across requests via a module-level singleton).
- Exposes two safe, parameterised lookup functions:
  - `fetch_policy(policy_type)` → one row from `policies`
  - `fetch_order(order_id)` → one row from `orders`
- Exposes `log_interaction(...)` which writes every completed conversation (query, intent, retrieved data, final response) into `support_logs`, for auditing.

All queries use SQLAlchemy's `text()` with **named bind parameters** (`:ptype`, `:oid`, etc.) — never raw string formatting — so there is no SQL-injection surface even though the values ultimately come from an LLM's tool call.

### `app/tools.py`
Wraps the functions in `database.py` as **LangChain tools** using the `@tool` decorator, so Agent 2 (the MySQL Database Agent) can call them. There are 5 tools:

| Tool | What it does |
|---|---|
| `get_refund_policy()` | Returns the refund policy row |
| `get_return_policy()` | Returns the return policy row |
| `get_cancellation_policy()` | Returns the cancellation policy row |
| `get_shipping_policy()` | Returns the general shipping policy row |
| `get_order_details(order_id)` | Returns a specific order's status/payment/tracking info |

Each tool has a docstring — LangChain uses that docstring to decide, at runtime, which tool best matches the customer's intent. This is the actual "tool calling" mechanism, not a hardcoded if/else.

### `app/agents/intent_agent.py` — **Agent 1**
Takes the raw customer message and returns a structured `IntentResult`:
```python
class IntentResult(BaseModel):
    intent: Literal["order_status", "refund_policy", "order_cancellation",
                     "payment_issue", "shipping_information", "return_policy", "unknown"]
    order_id: Optional[str]
    reasoning: str
```
It uses `llm.with_structured_output(IntentResult)` — the LLM's response is forced to match this schema, so downstream code never has to parse free-form text. This is the "Structured Outputs" requirement in practice.

### `app/agents/sql_agent.py` — **Agent 2**
A real LangChain **tool-calling agent** (`create_tool_calling_agent` + `AgentExecutor`), given the 5 tools from `tools.py`. Its system prompt tells it exactly which tool to call for which intent (e.g. `refund_policy` → `get_refund_policy`, `order_status` → `get_order_details`). It calls **exactly one** tool per request and returns that tool's raw result.

### `app/agents/response_agent.py` — **Agent 3**
A simple LLM prompt chain (`prompt | llm | StrOutputParser`) that takes the original query, the detected intent, and the raw retrieved data, and writes a warm, professional customer-facing reply. It's explicitly instructed never to invent information that isn't in the retrieved data.

### `app/orchestrator.py`
The glue. `run_support_pipeline(customer_query)`:
1. Calls Agent 1 → gets intent + order_id
2. Calls Agent 2 → gets retrieved_data
3. Calls Agent 3 → gets final_response
4. Logs everything to `support_logs`
5. Returns all of it as one dictionary

This is plain sequential Python — deliberately not LangGraph — matching the assignment's required linear workflow.

### `app/main.py`
The FastAPI app itself:
- `GET /` → serves `static/index.html` (the frontend)
- `GET /health` → simple health check
- `POST /api/support/query` → runs `run_support_pipeline()` and returns the result as JSON
- CORS is enabled (`allow_origins=["*"]`) so the frontend can call the API from any origin during development

### `static/index.html`
The entire frontend in one file — see [The frontend](#the-frontend) below.

### `database/schema.sql` / `database/seed_data.sql`
Reference SQL to create the three tables and populate them with sample data. These are **not read by the running application** — they're one-time setup scripts you run directly against MySQL (via `mysql` CLI or a GUI). Once your tables exist, you can delete these files; the app only needs the tables themselves to already exist in your database.

---

## Database design

**Database name:** `mectro_support`

### `policies`
| Column | Type | Notes |
|---|---|---|
| `id` | INT, PK, auto-increment | |
| `policy_type` | VARCHAR(50), UNIQUE | `refund_policy`, `return_policy`, `cancellation_policy`, `shipping_policy` |
| `title` | VARCHAR(150) | Human-readable title |
| `content` | TEXT | The actual policy text shown to customers |
| `updated_at` | TIMESTAMP | Auto-updated on change |

### `orders`
| Column | Type | Notes |
|---|---|---|
| `id` | INT, PK, auto-increment | |
| `order_id` | VARCHAR(20), UNIQUE | e.g. `ORD1001` |
| `customer_name` | VARCHAR(100) | |
| `order_status` | VARCHAR(50) | Placed / Shipped / Out for Delivery / Delivered / Cancelled |
| `payment_status` | VARCHAR(50) | Paid / Pending / Failed / Refunded |
| `tracking_number` | VARCHAR(50) | Nullable |
| `carrier` | VARCHAR(50) | Nullable |
| `expected_delivery` | DATE | Nullable |
| `order_amount` | DECIMAL(10,2) | |
| `created_at` | TIMESTAMP | |

### `support_logs`
| Column | Type | Notes |
|---|---|---|
| `id` | INT, PK, auto-increment | |
| `customer_query` | TEXT | What the customer typed |
| `detected_intent` | VARCHAR(50) | Agent 1's output |
| `order_id` | VARCHAR(20) | If any was extracted |
| `retrieved_data` | TEXT | Agent 2's raw output |
| `final_response` | TEXT | Agent 3's output |
| `created_at` | TIMESTAMP | |

Used purely for auditing — nothing reads from it at request time, so a logging failure never breaks a customer-facing response (it's wrapped in a try/except in `orchestrator.py`).

---

## The three agents, in detail

### Why 3 separate agents instead of 1 big prompt?
Because the assignment requires **single responsibility per agent** — each one should be independently testable, debuggable, and replaceable. In practice this means:
- If intent detection is wrong, you only need to fix Agent 1's prompt.
- If the wrong data is being pulled, you only need to fix Agent 2's tool logic.
- If replies sound robotic, you only need to fix Agent 3's prompt.

None of the three agents know how the others work internally — they only pass simple, well-defined data between each other (a string, a Pydantic model, a JSON string).

### Temperature settings
- Agent 1 (intent) → `temperature=0` — classification should be deterministic
- Agent 2 (SQL/tool-calling) → `temperature=0` — tool selection should be deterministic
- Agent 3 (response) → `temperature=0.4` — a little natural variation is fine and even desirable in customer-facing prose

---

## The frontend

`static/index.html` is a single self-contained file (HTML + CSS + JS, no build tools, no npm) served directly by FastAPI at `/`.

**Design concept:** a black-and-white "receipt printer" console. The customer types a message on the left in a dark terminal-style input panel; the response prints out on the right as a paper "ticket stub" with a torn perforated edge at the bottom — evoking an actual support-ticket printout, while staying strictly black/white/gray with no color accents.

**How it talks to the backend:** a single `fetch('/api/support/query', { method: 'POST', body: JSON.stringify({ customer_query }) })` call. Because the frontend is served from the same FastAPI app, this is a same-origin request — no separate server or proxy needed.

**What it shows:** just the final customer-facing response (`data.final_response`) — not the internal intent/SQL trace — since that's what a real support console should surface to whoever's testing it.

**Example query chips:** six pre-filled buttons (Refund policy, Order status, Cancel order, Payment issue, Shipping info, Return policy) so you can test all six intents with one click each, without typing.

---

## Setup & installation

### 1. Create the MySQL database and tables

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed_data.sql
```

(If you've already created equivalent tables yourself — e.g. by importing a CSV — you can skip this and just make sure your table/column names match the schema above.)

### 2. Get a Groq API key

Sign up free at [console.groq.com/keys](https://console.groq.com/keys).

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_actual_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=mectro_support
```

### 4. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the project

```bash
uvicorn app.main:app --reload
```

Then open:

| URL | What it is |
|---|---|
| `http://127.0.0.1:8000/` | The frontend console |
| `http://127.0.0.1:8000/docs` | Interactive Swagger API docs |
| `http://127.0.0.1:8000/health` | Health check |

---

## API reference

### `POST /api/support/query`

**Request body:**
```json
{
  "customer_query": "I would like to know your refund policy."
}
```

**Response body:**
```json
{
  "customer_query": "I would like to know your refund policy.",
  "detected_intent": "refund_policy",
  "intent_reasoning": "Customer is asking about the refund policy in general.",
  "order_id": null,
  "retrieved_data": "{\"policy_type\": \"refund_policy\", \"title\": \"Refund Policy\", \"content\": \"...\"}",
  "final_response": "Thank you for reaching out! Mectro offers a full refund within 30 days of delivery..."
}
```

### `GET /health`
```json
{ "status": "ok" }
```

---

## Example walkthrough

**Customer types:** `"What's the status of my order ORD1001?"`

1. **Agent 1 (Intent Detection)** reads the message and outputs:
   ```json
   { "intent": "order_status", "order_id": "ORD1001", "reasoning": "Customer is asking about their order's current status." }
   ```
2. **Agent 2 (MySQL Database Agent)** sees `intent = order_status` and an `order_id`, so it calls the `get_order_details("ORD1001")` tool, which runs:
   ```sql
   SELECT order_id, customer_name, order_status, payment_status,
          tracking_number, carrier, expected_delivery, order_amount
   FROM orders WHERE UPPER(order_id) = UPPER('ORD1001') LIMIT 1;
   ```
   and gets back the row for Aditi Sharma's shipped order.
3. **Agent 3 (Response Generator)** turns that JSON row into:
   > "Hi! Your order ORD1001 has been shipped via BlueDart and is expected to arrive by July 20, 2026. You can track it using tracking number TRK9988771. Let us know if you need anything else!"

---

## Design decisions & trade-offs

- **Tools instead of free-form SQL.** The MySQL Database Agent can only call 5 fixed, parameterised tools — it never writes its own SQL. This trades a small amount of flexibility for real injection-safety, since the LLM's output never becomes part of a query string.
- **Structured output over prompted JSON.** Agent 1 uses `with_structured_output()` rather than asking the LLM to "return JSON" in a text prompt — this guarantees a parseable, schema-valid result instead of hoping the model formats it correctly.
- **Plain orchestration over LangGraph.** The assignment explicitly disallows LangGraph, so the 3-agent handoff is just ordinary sequential Python function calls — simpler to read and debug for a linear (non-branching, non-looping) workflow like this one.
- **Best-effort logging.** Writing to `support_logs` is wrapped in a try/except specifically so that a logging/DB hiccup never prevents the customer from getting their answer.
