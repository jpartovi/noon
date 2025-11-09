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

   # Google OAuth for calendar linking (required)
   GOOGLE_CLIENT_ID="your-google-oauth-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-google-client-secret"
   GOOGLE_OAUTH_REDIRECT_URI="https://<backend-host>/google-accounts/oauth/callback"
   GOOGLE_OAUTH_APP_REDIRECT_URI="noon://oauth/google"
   # Optional: override default scopes (space-delimited string)
   GOOGLE_OAUTH_SCOPES="https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid"
   
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
- `POST /google-accounts/oauth/start` — Returns a Google OAuth URL + state token (requires Supabase bearer token).
- `GET /google-accounts/oauth/callback` — Handles Google redirect, exchanges tokens, stores account data, and redirects to the app deep link.
- `GET /google-accounts` — List linked Google accounts for the authenticated user.
- `POST /google-accounts` — Upsert a Google account for the authenticated user.
- `DELETE /google-accounts/{account_id}` — Remove a linked Google account.

All Google account routes require a `Bearer` token using the Supabase access token returned from `/auth/verify`.

### iOS Callback Configuration

- Set the deep-link URL the backend will redirect to (e.g. `noon://oauth/google`) in `GOOGLE_OAUTH_APP_REDIRECT_URI`.
- Add the same value to the iOS app by defining `GoogleOAuthCallbackURL` in `Info.plist` (or setting `GOOGLE_OAUTH_CALLBACK_URL` at runtime) so `ASWebAuthenticationSession` knows which scheme to listen for.

## Google OAuth Setup Checklist

1. In [Google Cloud Console](https://console.cloud.google.com/):
   - Enable the **Google Calendar API** and **People API** for your project.
   - Create an **OAuth 2.0 Client ID** (type: *Web application*).
   - Add the backend redirect URI: `https://<backend-host>/google-accounts/oauth/callback`.
   - Download the client credentials or copy the **Client ID** and **Client secret** into `.env`.
2. In Supabase, ensure the `google_accounts` table exists (see `supabase/migrations/0001_users_google_accounts.sql`).
3. In the iOS app:
   - Register the custom URL scheme (e.g. `noon`) via `Info.plist` `CFBundleURLTypes`.
   - Set `GoogleOAuthCallbackURL` to match `GOOGLE_OAUTH_APP_REDIRECT_URI` (e.g. `noon://oauth/google`).
4. Restart both the FastAPI backend and the iOS simulator/device after updating credentials.

### Agent (LangGraph)
- `POST /agent/runs` — Forward a message to the LangGraph agent.
- `POST /agent/test` — Trigger a test run to verify the agent is working.

#### Example agent request:
```bash
curl -X POST http://localhost:8000/agent/runs \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"human","content":"Schedule lunch tomorrow at 1pm"}]}'
```
