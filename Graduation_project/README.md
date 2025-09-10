# Smart Router/Orchestrator Agent (Graduation Project)

This project provides a minimal, production-style Router/Orchestrator Agent for a modular ERP system. The Router classifies user requests (Sales, Finance, Inventory, Analytics), routes them to the correct specialist agent, enforces governance (approvals for risky ops), and persists memory (conversations and tool calls) into `erp_sample.db`.

## What the Router Agent does
- Classifies each user request via LLM + keyword fallback.
- Routes to the right specialist agent tool.
- Persists memory of conversations and tool calls in SQLite for auditability.
- Applies governance policies and records approval requirements.
- Provides a system info tool that lists ERP tables and row counts.

## Files
- `Router_agent.py`: Main router/orchestrator agent and tools.
- `setup_db.py`: Builds and seeds `erp_sample.db` with ERP and orchestrator tables.
- `erp_sample.db`: SQLite database (generated/updated by `setup_db.py`).

## Memory Strategy
- Short-term: windowed chat memory (`ConversationBufferWindowMemory`) keeps the last 5 messages in RAM for better LLM responses.
- Long-term/Audit: each interaction is written to SQLite:
  - `conversations(session_id, user_id, user_input, agent_output, agent, success)`
  - `tool_calls(session_id, user_id, agent, inputs, outputs, success)`
- These tables enable debugging, analytics, and system audits.

## Governance & Approvals
- `check_governance()` inspects user requests for risky phrases and domain-sensitive actions.
- If flagged, a row is inserted into `approvals(session_id, user_id, request, agent, status, reasons)` with status `PENDING` and the live request is blocked until approved.
- You can extend this policy list or replace it with a classifier.

## Setup & Run
1. Create and seed the demo database:
```bash
python3 /Users/apple/Desktop/graduation/Graduation_project/setup_db.py
```
2. Export your LLM credentials (Gemini) and (optionally) identifiers:
```bash
export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
export ERP_SESSION_ID=demo-session
export ERP_USER_ID=demo-user
```
3. Start the Router Agent demo loop:
```bash
python3 /Users/apple/Desktop/graduation/Graduation_project/Router_agent.py
```
4. Try examples:
- "Show me customers"
- "Generate a revenue report for last quarter" (analytics)
- "Export all invoices" (should require approval)
- Type `system` to view tables and row counts. Type `quit` to exit.

## Extending
- Replace the stubbed agent executors with real ones in `agents/*` and keep the same interface (`executor.invoke({"input": str})`).
- Enhance `check_governance()` with a more robust policy engine or model-based classifier.
- Add more tools and domains by following the same pattern.

## Notes
- The Router ensures orchestrator tables exist at startup (idempotent create). For full control, manage schema via migrations instead.
- `config/llm.py` uses Gemini `gemini-1.5-flash`. Adjust temperature/model as needed.

---

# Configuration Placeholders
- TODO: insert your Google API key in environment `GOOGLE_API_KEY`.
- TODO: set your preferred Gemini model name in `config/llm.py` if different.
- TODO: update database path if needed (`Router_agent.py` -> `DB_PATH`). 