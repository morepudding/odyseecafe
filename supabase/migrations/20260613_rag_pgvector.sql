create extension if not exists vector with schema extensions;

create table if not exists public.rag_chunks (
  id text primary key,
  character_id text not null,
  source text not null,
  chunk_index integer not null,
  text text not null,
  embedding extensions.halfvec(2048) not null,
  content_hash text not null,
  token_count integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists rag_chunks_character_idx
  on public.rag_chunks (character_id);

create index if not exists rag_chunks_source_idx
  on public.rag_chunks (character_id, source);

create index if not exists rag_chunks_embedding_hnsw_idx
  on public.rag_chunks
  using hnsw (embedding extensions.halfvec_cosine_ops);

create or replace function public.set_rag_chunks_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists rag_chunks_set_updated_at on public.rag_chunks;
create trigger rag_chunks_set_updated_at
before update on public.rag_chunks
for each row
execute function public.set_rag_chunks_updated_at();

alter table public.rag_chunks enable row level security;

drop policy if exists "service_role manages rag_chunks" on public.rag_chunks;
create policy "service_role manages rag_chunks"
on public.rag_chunks
for all
to service_role
using (true)
with check (true);

drop policy if exists "public reads rag_chunks" on public.rag_chunks;
create policy "public reads rag_chunks"
on public.rag_chunks
for select
to anon, authenticated
using (true);

create or replace function public.match_rag_chunks(
  query_embedding extensions.halfvec(2048),
  match_character text,
  match_count integer default 5
)
returns table (
  id text,
  character_id text,
  source text,
  chunk_index integer,
  text text,
  similarity double precision
)
language sql
stable
set search_path = public, extensions
as $$
  select
    rag_chunks.id,
    rag_chunks.character_id,
    rag_chunks.source,
    rag_chunks.chunk_index,
    rag_chunks.text,
    1 - (rag_chunks.embedding <=> query_embedding) as similarity
  from public.rag_chunks
  where rag_chunks.character_id = match_character
  order by rag_chunks.embedding <=> query_embedding
  limit match_count;
$$;

grant usage on schema public to anon, authenticated;
grant select on public.rag_chunks to anon, authenticated;
grant execute on function public.match_rag_chunks(extensions.halfvec, text, integer) to anon, authenticated;
