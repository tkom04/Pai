Perfect — here’s a **Plan V3**, refined for what you said: **all parts included (budgets, groceries, calendar, HA)** but **MCP-first** (AI integration, not voice-first). This gives you a single source of truth to drop in your repo.

---

```markdown
# PAI_PLAN_V3.md — Personal AI (PAI) for Household Ops (MCP-First)

**Owner:** Rhys
**Stack:** Python 3.11 + FastAPI + Docker + APScheduler
**Integrations (MVP):** Notion (DBs), Google Calendar API (FamilyWall bridge), Home Assistant (REST API)
**Interface:** MCP Server exposing JSON schemas (usable by ChatGPT, Cursor, Perplexity, etc.)
**Design:** Dark mode-first (future dashboard), headless/GPT-driven now

---

## 1) Context & Goals

1. **Problem:** Household ops (budgets, groceries, tasks, flips, automations) live across many apps.
2. **Solution:** Pi-hosted API ("PAI") exposed as an **MCP server** so any AI can manage/query household data with JSON actions.
3. **Primary Outcomes (90 days):**
   - Daily **Morning Brief** & **Budget Check** via MCP call.
   - Add/view **Groceries**, **Tasks**, and **Events** in Notion + Google Calendar (FamilyWall sync).
   - Trigger **HA service calls** via schema actions.
   - Weekly Brief → Notion + Calendar reminder.
4. **Non-Goals (MVP):**
   - No auto-trading or flips (later phase).
   - No FamilyWall API (Google Calendar bridge only).
   - No consumer voice focus (MCP-first, voice optional later).

---

## 2) Tech Choices

- **Backend:** Python + FastAPI (API-first).
- **MCP Layer:** Each API route wrapped as MCP tool with JSON schema.
- **Scheduling:** APScheduler for jobs (morning/lunch/weekly).
- **Integrations:** Notion SDK, Google API client, HA REST API.
- **UI (later):** Next.js dashboard (dark mode) for monitoring.

---

## 3) High-Level Architecture

```

\[AI Client (ChatGPT/Cursor/Perplexity)]
│
(MCP JSON Action)
▼
\[PAI FastAPI + MCP Server] ─────────┬──────────┬───────────────┐
│          │               │
\[Notion]   \[Google Cal]   \[Home Assistant]
↑          ↑   │          ↑
│          │   └─ FamilyWall (subscribed)
└── Budgets, Groceries, Tasks, Reports

```

---

## 4) Repo Structure

```

personal-ai/
├─ app/
│   ├─ main.py             # FastAPI app + endpoints
│   ├─ services/           # budgets, groceries, calendar, ha
│   ├─ jobs/               # morning\_brief, budget\_check, weekly\_brief
│   └─ util/               # logging, security, time
├─ mcp/
│   ├─ budget\_tool.py
│   ├─ groceries\_tool.py
│   ├─ calendar\_tool.py
│   └─ ha\_tool.py
├─ schemas/
│   ├─ budget\_schema.json
│   ├─ groceries\_schema.json
│   ├─ calendar\_schema.json
│   └─ ha\_schema.json
├─ tests/
├─ data/                   # sample CSVs
├─ requirements.txt
├─ Dockerfile
├─ .env.example
└─ README.md

```

---

## 5) Core Endpoints (MVP)

1. `GET /ping` → health check (API key).
2. `POST /budget_scan { period, source, path }` → caps/spent/delta.
3. `POST /add_to_groceries { item, qty }` → Notion Groceries DB.
4. `POST /create_task { title, due }` → Notion Tasks DB.
5. `POST /create_event { title, start, end, description? }` → Google Calendar (FamilyWall bridge).
6. `POST /ha_service_call { domain, service, entity_id }` → HA control.

Each wrapped as an MCP tool with JSON schema.

---

## 6) Scheduling Jobs (APScheduler)

- **07:30 daily** → `morning_brief()` (events, budget snapshot).
- **12:00 daily** → `budget_check()` (warn if >80% cap).
- **Sun 18:00** → `weekly_brief()` (compile report → Notion + Calendar reminder).

---

## 7) Build Plan (7 Days)

**Day 1**: Scaffold FastAPI + `/ping` + API-key + Dockerfile.
**Day 2**: Stub all 4 pillars (budget, groceries, calendar, HA).
**Day 3**: Wire Google Calendar → confirm FamilyWall shows events.
**Day 4**: Wire Notion DBs (groceries, tasks, budgets).
**Day 5**: Add APScheduler jobs + CSV budget parsing.
**Day 6**: Create MCP wrappers + JSON schemas → test in Cursor/GPT.
**Day 7**: End-to-end demo: Morning Brief + groceries add + event + HA toggle.

---

## 8) Validation Plan

- Use yourself daily for 14 days (dogfooding).
- Recruit 3–6 testers (AI power users).
- Success =
  - ≥4 days/week used.
  - ≥2 testers say they’d pay £7–15/mo.
  - Clear “wins” (saved time/money, prevented missed event).

---

## 9) Guardrails

- No auto-trading.
- Ask before irreversible HA actions.
- Log all actions (who/what/when).
- Secrets in `.env`, never in repo.

---

## 10) Post-MVP

- Swap CSV → Open Banking MCP ingestion.
- Add **shopping basket filler** (Tesco/Sainsbury’s, manual confirm).
- Build Next.js dark mode dashboard.
- Add **flip/market scans** for financial ops.
- Optional: add Alexa/Google voice skill hitting MCP.

---

## 11) Next 3 Actions (Today)

1. Create repo `personal-ai` with `/ping`, API-key, Dockerfile.
2. Implement `POST /create_event` → confirm event syncs to FamilyWall via Google Calendar.
3. Draft first MCP tool + schema (`budget_scan`) and test call from Cursor/GPT.

---
```

---

⚡ Plan V3 = **all 4 pillars included**, but the **primary interface is MCP**, not Alexa/Google.
That means ChatGPT, Cursor, or any AI can “drive your life” using schema calls.

Want me to also sketch the **first MCP schema file** (e.g., `budget_schema.json`) so you can drop it into your repo right away?
