# Agent Observability & User Insights Architecture

## Overview

This document outlines the architecture for:
1. **Agent Observability** - Logging only LLM/agent calls (not all requests)
2. **User Insights** - LLM-discovered user preferences stored asynchronously
3. **Calendar Event Emitter** - Background system for auto-scheduling preference-based events

## Database Schema

### 1. Agent Observability (`agent_observability`)

Tracks LangGraph agent calls and LLM interactions.

**Key Fields:**
- `agent_run_id` - LangGraph run ID for tracing
- `agent_action` - Agent action (create, read, update, delete, search, schedule)
- `llm_model` - Model used (e.g., 'gpt-4o-mini')
- `llm_prompt_tokens`, `llm_completion_tokens`, `llm_total_tokens` - Token usage
- `llm_cost_usd` - Estimated cost
- `user_message` - User's input
- `agent_response` - Agent's response
- `agent_state` - Full agent state (JSONB)
- `tool_result` - Tool execution result (JSONB)
- `execution_time_ms` - Performance metrics
- `intent_category` - Extracted intent
- `entities` - Extracted entities (JSONB)

**Use Cases:**
- Track LLM costs and usage
- Debug agent behavior
- Analyze user patterns
- Monitor performance

### 2. User Insights (`user_insights`)

Stores LLM-discovered user preferences, habits, and patterns.

**Key Fields:**
- `insight_type` - 'preference', 'habit', 'pattern', 'goal', 'constraint'
- `category` - 'schedule', 'meetings', 'health', 'work', 'personal'
- `key` - Unique key within category (e.g., 'preferred_gym_time')
- `value` - Flexible JSONB value
- `confidence` - LLM confidence (0.0 to 1.0)
- `source` - 'agent' (LLM), 'pattern_analysis', 'explicit'
- `source_request_id` - Link to request that generated this

**Unique Constraint:** `(user_id, category, key)` - Ensures one insight per key

**Example Insights:**
```json
{
  "insight_type": "preference",
  "category": "health",
  "key": "gym_time",
  "value": {"time": "06:00", "duration_minutes": 60, "days": [1,2,3,4,5]},
  "confidence": 0.8
}
```

### 3. Calendar Preferences (`calendar_preferences`)

Recurring calendar preferences for auto-scheduling (gym, sleep, focus blocks).

**Key Fields:**
- `preference_type` - 'gym', 'sleep', 'focus', 'meal', 'break', 'meditation'
- `title` - Event title
- `day_of_week` - Days of week (1=Mon, 7=Sun), null = daily
- `start_time` - Preferred start time
- `duration_minutes` - Duration
- `auto_schedule` - Whether to automatically add to calendar
- `priority` - 1 (highest) to 10 (lowest)
- `is_flexible` - Can be moved if conflicts
- `source_insight_id` - Link to insight that generated this

## Services

### Agent Observability Service

Logs agent/LLM calls to the database:

```python
from services.agent_observability import agent_observability_service

agent_observability_service.log_agent_call(
    user_id=user.id,
    agent_action="create",
    user_message="Schedule gym tomorrow at 6am",
    agent_response="Created gym event",
    agent_tool="create",
    tool_result={"event_id": "..."},
    execution_time_ms=1500,
    llm_model="gpt-4o-mini",
    llm_total_tokens=250,
    llm_cost_usd=0.001,
)
```

### User Insights Service

Manages LLM-discovered insights:

```python
from services.user_insights import user_insights_service

# Create/update insight
user_insights_service.create_insight(
    user_id=user.id,
    insight_type="preference",
    category="health",
    key="gym_time",
    value={"time": "06:00", "duration": 60},
    confidence=0.8,
)

# Get insights
insights = user_insights_service.get_user_insights(
    user_id=user.id,
    category="health"
)
```

### Calendar Event Emitter

Emits calendar events based on preferences:

```python
from services.calendar_event_emitter import calendar_event_emitter

# Process preferences for a user (next 7 days)
calendar_event_emitter.process_user_preferences(user_id, days_ahead=7)
```

## Agent Integration

### Updating User Insights (Async)

The agent can call the `/user-insights/update` endpoint to asynchronously update insights:

```python
# In LangGraph agent, when discovering an insight:
# POST /user-insights/update
{
    "insight_type": "preference",
    "category": "health",
    "key": "gym_time",
    "value": {"time": "06:00", "duration": 60},
    "confidence": 0.8
}
```

This creates an async job that updates the insight in the background.

## Background Workers

### 1. Async Job Processor

Processes async agent jobs:
- Updates user insights
- Emits preference events
- Handles calendar sync operations

**Run:**
```bash
python -m workers.async_job_processor
```

### 2. Preference Emitter Worker

Periodically emits calendar events from preferences:
- Reads active `calendar_preferences`
- Creates events for next 7 days
- Queues async jobs to add to Google Calendar

**Run:**
```bash
python -m workers.preference_emitter_worker
```

## Request Logging Changes

The `RequestLoggingMiddleware` now **only logs agent endpoints** (`/agent/*`), not all requests. For full observability, use `AgentObservabilityService` directly in the agent router.

## Workflow

1. **User makes agent request** → Logged to `agent_observability`
2. **Agent discovers insight** → Calls `/user-insights/update` → Creates async job
3. **Async job processor** → Updates `user_insights` table
4. **Preference emitter worker** → Reads `user_insights` → Creates `calendar_preferences`
5. **Preference emitter worker** → Reads `calendar_preferences` → Emits events → Queues calendar sync jobs
6. **Async job processor** → Processes calendar sync jobs → Adds events to Google Calendar

## Example: Gym Preference Flow

1. User: "I go to the gym every morning at 6am"
2. Agent logs to `agent_observability`
3. Agent calls `/user-insights/update` with:
   ```json
   {
     "insight_type": "preference",
     "category": "health",
     "key": "gym_time",
     "value": {"time": "06:00", "duration": 60, "days": [1,2,3,4,5]},
     "confidence": 0.9
   }
   ```
4. Async job creates/updates `user_insights` record
5. Background process creates `calendar_preference`:
   - `preference_type`: "gym"
   - `title`: "Morning Gym"
   - `start_time`: "06:00"
   - `duration_minutes`: 60
   - `day_of_week`: [1,2,3,4,5]
   - `auto_schedule`: true
6. Preference emitter creates events for next 7 days
7. Events are added to Google Calendar

## Implementation Checklist

- [x] Create `agent_observability` table
- [x] Create `user_insights` table
- [x] Create `calendar_preferences` table
- [x] Create Pydantic models for all tables
- [x] Create `AgentObservabilityService`
- [x] Create `UserInsightsService`
- [x] Create `CalendarEventEmitter`
- [x] Create `/user-insights/update` endpoint
- [x] Update agent router to use observability service
- [x] Refactor request logging to only log agent endpoints
- [x] Create async job processor worker
- [x] Create preference emitter worker
- [ ] Integrate LangGraph agent with `/user-insights/update` endpoint
- [ ] Add actual Google Calendar event creation in async jobs
- [ ] Add monitoring/alerting for workers

