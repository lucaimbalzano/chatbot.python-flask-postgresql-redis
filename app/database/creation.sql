-- THREADS ----------------------------------------------------
create table public.threads (
  id                bigint generated always as identity primary key,  -- auto-increment
  openai_thread_id  text  unique not null,                            -- thread_xxx
  wa_id             text  not null,
  assistant_id      text  not null,
  first_seen        timestamptz default now(),
  last_seen         timestamptz default now()
);

create index threads_wa_id_ix on public.threads (wa_id);

-- MESSAGES ---------------------------------------------------
create table public.messages (
  id                bigint generated always as identity primary key,
  thread_id         bigint not null references public.threads(id) on delete cascade,
  role              text   not null check (role in ('user','assistant','tool')),
  content           text,
  tokens            int,
  created_at        timestamptz default now()
);

create index messages_thread_id_ix on public.messages (thread_id);
