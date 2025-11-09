-- Agent observability table for tracking LangGraph agent calls and LLM interactions
create table if not exists public.agent_observability (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    
    -- Agent execution details
    agent_run_id text,  -- LangGraph run ID for tracing
    agent_action text not null,  -- 'create', 'read', 'update', 'delete', 'search', 'schedule'
    agent_tool text,  -- Tool name that was called
    
    -- LLM interaction details
    llm_model text,  -- Model used (e.g., 'gpt-4o-mini')
    llm_prompt_tokens integer,  -- Tokens in prompt
    llm_completion_tokens integer,  -- Tokens in completion
    llm_total_tokens integer,  -- Total tokens
    llm_cost_usd numeric(10, 6),  -- Estimated cost in USD
    
    -- Input/Output
    user_message text not null,  -- User's input message
    agent_response text,  -- Agent's response/summary
    agent_state jsonb,  -- Full agent state at execution
    tool_result jsonb,  -- Tool execution result
    
    -- Performance
    execution_time_ms integer,  -- Total execution time
    success boolean not null default true,
    error_message text,  -- Error if failed
    
    -- Pattern analysis
    intent_category text,  -- Extracted intent
    entities jsonb,  -- Extracted entities
    
    -- Metadata
    created_at timestamptz not null default timezone('utc'::text, now()),
    
    -- Constraints
    constraint valid_tokens check (
        (llm_prompt_tokens is null and llm_completion_tokens is null and llm_total_tokens is null) or
        (llm_total_tokens >= 0 and llm_prompt_tokens >= 0 and llm_completion_tokens >= 0)
    )
);

-- Indexes for fast queries
create index if not exists idx_agent_obs_user_id on public.agent_observability(user_id);
create index if not exists idx_agent_obs_created_at on public.agent_observability(created_at desc);
create index if not exists idx_agent_obs_action on public.agent_observability(agent_action);
create index if not exists idx_agent_obs_run_id on public.agent_observability(agent_run_id) where agent_run_id is not null;
create index if not exists idx_agent_obs_success on public.agent_observability(user_id, success, created_at desc);

-- GIN indexes for JSONB
create index if not exists idx_agent_obs_state_gin 
    on public.agent_observability using gin(agent_state);
create index if not exists idx_agent_obs_result_gin 
    on public.agent_observability using gin(tool_result);
create index if not exists idx_agent_obs_entities_gin 
    on public.agent_observability using gin(entities);

-- Composite index for user behavior analysis
create index if not exists idx_agent_obs_user_behavior 
    on public.agent_observability(user_id, created_at desc, agent_action, success);

-- Row Level Security
alter table public.agent_observability enable row level security;

-- Users can view their own agent calls
create policy "Users can view their own agent observability"
    on public.agent_observability
    for select
    using (auth.uid() = user_id);

-- Service role can insert/update (for agent logging)
create policy "Service role can manage agent observability"
    on public.agent_observability
    for all
    using (true)
    with check (true);

-- Comments
comment on table public.agent_observability is 'Observability data for LangGraph agent calls and LLM interactions';
comment on column public.agent_observability.agent_run_id is 'LangGraph run ID for tracing and debugging';
comment on column public.agent_observability.llm_cost_usd is 'Estimated cost of LLM call in USD';

