# Noon Backend

FastAPI service that handles:
- Supabase phone OTP auth and Google account linking
- Forwarding requests to the deployed LangGraph agent for AI functionality

## Setup

1. Install dependencies (using [uv](https://docs.astral.sh/uv/)):
   ```bash
   cd noon-backend
   uv sync
   ```

2. Create an environment file (`.env`) with the required credentials:
   ```bash
   # Supabase (required)
   SUPABASE_URL="https://<project-ref>.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY="service-role-secret"
   SUPABASE_ANON_KEY="anon-public-key"
   SUPABASE_JWT_SECRET="your-jwt-secret"
   
   # LangGraph (optional - for agent functionality)
   LANGGRAPH_URL="https://your-deployment-url"
   LANGSMITH_API_KEY="your-api-key"
   LANGGRAPH_AGENT_NAME="noon-agent"
   ```

3. Start the dev server:
   ```bash
   uv run uvicorn main:app --reload
   ```

## API

### Authentication
- `GET /healthz` — Health check endpoint.
- `POST /auth/otp` — Trigger an SMS OTP to the provided phone number.
- `POST /auth/verify` — Verify the OTP, returning Supabase session tokens.

### Google Accounts
- `GET /google-accounts` — List linked Google accounts for the authenticated user.
- `POST /google-accounts` — Upsert a Google account for the authenticated user.
- `DELETE /google-accounts/{account_id}` — Remove a linked Google account.

All Google account routes require a `Bearer` token using the Supabase access token returned from `/auth/verify`.

### Agent (LangGraph)
- `POST /agent/runs` — Forward a message to the LangGraph agent.
- `POST /agent/test` — Trigger a test run to verify the agent is working.

#### Example agent request:
```bash
curl -X POST http://localhost:8000/agent/runs \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"human","content":"Schedule lunch tomorrow at 1pm"}]}'
```
