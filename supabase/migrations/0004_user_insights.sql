-- User insights table for storing LLM-discovered user preferences and behaviors
create table if not exists public.user_insights (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    
    -- Insight details
    insight_type text not null,  -- 'preference', 'habit', 'pattern', 'goal', 'constraint'
    category text not null,  -- 'schedule', 'meetings', 'health', 'work', 'personal', etc.
    key text not null,  -- e.g., 'preferred_gym_time', 'sleep_schedule', 'focus_blocks'
    value jsonb not null,  -- Flexible JSONB for any insight value
    confidence float default 0.5,  -- LLM confidence (0.0 to 1.0)
    
    -- Source tracking
    source text not null default 'agent',  -- 'agent', 'pattern_analysis', 'explicit'
    source_request_id uuid references public.request_logs (id) on delete set null,
    
    -- Metadata
    created_at timestamptz not null default timezone('utc'::text, now()),
    updated_at timestamptz not null default timezone('utc'::text, now()),
    
    -- Ensure unique insights per user/category/key
    unique(user_id, category, key)
);

-- Indexes
create index if not exists idx_user_insights_user_id on public.user_insights(user_id);
create index if not exists idx_user_insights_category on public.user_insights(category);
create index if not exists idx_user_insights_type on public.user_insights(insight_type);
create index if not exists idx_user_insights_created_at on public.user_insights(created_at desc);

-- GIN index for JSONB queries
create index if not exists idx_user_insights_value_gin 
    on public.user_insights using gin(value);

-- Composite index for common queries
create index if not exists idx_user_insights_user_category 
    on public.user_insights(user_id, category, updated_at desc);

-- Trigger to update updated_at
create trigger handle_user_insights_updated_at
    before update on public.user_insights
    for each row
    execute procedure public.set_updated_at();

-- Row Level Security
alter table public.user_insights enable row level security;

-- Users can view their own insights
create policy "Users can view their own insights"
    on public.user_insights
    for select
    using (auth.uid() = user_id);

-- Service role can manage insights (for agent updates)
create policy "Service role can manage insights"
    on public.user_insights
    for all
    using (true)
    with check (true);

-- Comments
comment on table public.user_insights is 'LLM-discovered user preferences, habits, and patterns for personalization';
comment on column public.user_insights.insight_type is 'Type of insight: preference, habit, pattern, goal, constraint';
comment on column public.user_insights.category is 'Category: schedule, meetings, health, work, personal, etc.';
comment on column public.user_insights.key is 'Unique key for this insight within category';
comment on column public.user_insights.value is 'Flexible JSONB value for the insight';
comment on column public.user_insights.confidence is 'LLM confidence score (0.0 to 1.0)';
comment on column public.user_insights.source is 'Source: agent (LLM), pattern_analysis, explicit (user set)';

