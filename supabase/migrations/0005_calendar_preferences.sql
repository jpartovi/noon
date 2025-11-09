-- Calendar preferences table for recurring events/activities (gym, sleep, focus blocks)
create table if not exists public.calendar_preferences (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    
    -- Preference details
    preference_type text not null,  -- 'gym', 'sleep', 'focus', 'meal', 'break', 'meditation', etc.
    title text not null,  -- e.g., 'Morning Gym', 'Deep Work Block', 'Lunch Break'
    description text,  -- Optional description
    
    -- Scheduling
    day_of_week integer[],  -- Days of week (1=Mon, 7=Sun), empty = daily
    start_time time not null,  -- Preferred start time
    duration_minutes integer not null,  -- Duration in minutes
    timezone text not null default 'UTC',
    
    -- Constraints
    priority integer default 5,  -- 1 (highest) to 10 (lowest)
    is_flexible boolean default true,  -- Can be moved if conflicts
    buffer_before_minutes integer default 0,  -- Buffer before event
    buffer_after_minutes integer default 0,  -- Buffer after event
    
    -- Auto-scheduling
    auto_schedule boolean default false,  -- Automatically add to calendar
    calendar_id text,  -- Which calendar to add to (null = primary)
    
    -- Source
    source text not null default 'insight',  -- 'insight', 'explicit', 'pattern'
    source_insight_id uuid references public.user_insights (id) on delete set null,
    
    -- Status
    is_active boolean default true,  -- Whether this preference is active
    
    -- Metadata
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now()),
    
    -- Constraints
    constraint valid_day_of_week check (
        day_of_week is null or 
        array_length(day_of_week, 1) = 0 or
        (select bool_and(d >= 1 and d <= 7) from unnest(day_of_week) as d)
    ),
    constraint valid_priority check (priority >= 1 and priority <= 10),
    constraint valid_duration check (duration_minutes > 0)
);

-- Indexes
create index if not exists idx_calendar_prefs_user_id on public.calendar_preferences(user_id);
create index if not exists idx_calendar_prefs_type on public.calendar_preferences(preference_type);
create index if not exists idx_calendar_prefs_active on public.calendar_preferences(user_id, is_active) where is_active = true;
create index if not exists idx_calendar_prefs_auto_schedule on public.calendar_preferences(user_id, auto_schedule) where auto_schedule = true;

-- Trigger to update updated_at
create trigger handle_calendar_prefs_updated_at
    before update on public.calendar_preferences
    for each row
    execute procedure public.set_updated_at();

-- Row Level Security
alter table public.calendar_preferences enable row level security;

-- Users can manage their own preferences
create policy "Users can manage their own calendar preferences"
    on public.calendar_preferences
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- Service role can manage preferences (for background workers)
create policy "Service role can manage calendar preferences"
    on public.calendar_preferences
    for all
    using (true)
    with check (true);

-- Comments
comment on table public.calendar_preferences is 'Recurring calendar preferences (gym, sleep, focus blocks) for auto-scheduling';
comment on column public.calendar_preferences.preference_type is 'Type: gym, sleep, focus, meal, break, meditation, etc.';
comment on column public.calendar_preferences.auto_schedule is 'Whether to automatically add these events to calendar';
comment on column public.calendar_preferences.source is 'Source: insight (from LLM), explicit (user set), pattern (analyzed)';

