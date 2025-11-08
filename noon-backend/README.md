# Noon Backend

FastAPI service that orchestrates Supabase phone OTP auth and Google account linking.

## Setup

1. Install dependencies (using [uv](https://docs.astral.sh/uv/)):
   ```bash
   cd noon-backend
   uv sync
   ```

2. Create an environment file (e.g. `.env`) with the Supabase credentials:
   ```bash
   SUPABASE_URL="https://<project-ref>.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY="service-role-secret"
   SUPABASE_ANON_KEY="anon-public-key"
   SUPABASE_JWT_SECRET="your-jwt-secret"
   ```

3. Start the dev server:
   ```bash
    uv run uvicorn main:app --reload
   ```

## API

- `POST /auth/otp` — Trigger an SMS OTP to the provided phone number.
- `POST /auth/verify` — Verify the OTP, returning Supabase session tokens.
- `GET /google-accounts` — List linked Google accounts for the authenticated user.
- `POST /google-accounts` — Upsert a Google account for the authenticated user.
- `DELETE /google-accounts/{account_id}` — Remove a linked Google account.

All Google account routes require a `Bearer` token using the Supabase access token returned from `/auth/verify`.

