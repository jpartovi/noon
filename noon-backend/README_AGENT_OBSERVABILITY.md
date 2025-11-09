# Agent Observability & User Insights

## Quick Start

### 1. Run Migrations

Apply the new database migrations in Supabase SQL Editor:
- `0004_user_insights.sql` - User insights table
- `0005_calendar_preferences.sql` - Calendar preferences table
- `0006_agent_observability.sql` - Agent observability table

### 2. Start Background Workers

**Async Job Processor** (processes insight updates and calendar events):
```bash
cd noon-backend
uv run python -m workers.async_job_processor
```

**Preference Emitter Worker** (emits calendar events from preferences):
```bash
cd noon-backend
uv run python -m workers.preference_emitter_worker
```

### 3. Agent Can Now Update Insights

The LangGraph agent can call `/user-insights/update` to asynchronously update user insights when it discovers something about the user.

## Architecture

See `ARCHITECTURE_AGENT_OBSERVABILITY.md` for full details.

## Key Changes

1. **Request Logging** - Now only logs `/agent/*` endpoints (LLM calls)
2. **Agent Observability** - New table for tracking all agent/LLM interactions
3. **User Insights** - LLM can discover and store user preferences asynchronously
4. **Calendar Preferences** - Auto-scheduling system for gym, sleep, focus blocks, etc.
5. **Background Workers** - Process insights and emit calendar events

