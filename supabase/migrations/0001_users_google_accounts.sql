-- Enable required extensions
create extension if not exists "pgcrypto";

-- Users table anchored to Supabase auth.users (phone OTP auth)
create table if not exists public.users (
    id uuid primary key references auth.users (id) on delete cascade,
    phone text unique not null,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now())
);

-- Trigger function to keep updated_at current
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at := timezone('utc'::text, now());
    return new;
end;
$$;

create trigger handle_users_updated_at
    before update on public.users
    for each row
    execute procedure public.set_updated_at();

-- Google accounts linked to a user (one-to-many)
create table if not exists public.google_accounts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    google_user_id text not null,
    email text not null,
    display_name text,
    avatar_url text,
    access_token text,
    refresh_token text,
    expires_at timestamptz,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now()),
    unique (user_id, google_user_id)
);

create trigger handle_google_accounts_updated_at
    before update on public.google_accounts
    for each row
    execute procedure public.set_updated_at();

-- Row Level Security configuration
alter table public.users enable row level security;
alter table public.google_accounts enable row level security;

-- Users table policies
create policy "Users can view their own profile"
    on public.users
    for select
    using (auth.uid() = id);

create policy "Users can update their own profile"
    on public.users
    for update
    using (auth.uid() = id);

create policy "Users can insert their own profile"
    on public.users
    for insert
    with check (auth.uid() = id);

-- Google accounts policies
create policy "Users can manage their Google accounts"
    on public.google_accounts
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

