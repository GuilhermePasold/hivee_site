# Requisitos Supabase para o RAG do agente HIVEE

O Supabase sera usado apenas pelo agente RAG. O Django ORM/catalogo continua usando o banco local ou a configuracao existente do projeto.

## Variaveis que preciso no `backend/.env`

```env
SUPABASE_URL=https://SEU_PROJECT_REF.supabase.co
SUPABASE_SERVICE_KEY=SEU_SERVICE_ROLE_KEY
```

Onde encontrar:

- `SUPABASE_URL`: Supabase Dashboard -> Project Settings -> API -> Project URL.
- `SUPABASE_SERVICE_KEY`: Supabase Dashboard -> Project Settings -> API -> service_role / secret key.

Nao preciso, para o RAG:

- `DATABASE_URL`
- chaves de Supabase Storage
- anon/public key
- JWT secret
- bucket de arquivos

## Estrutura esperada pelo codigo atual

O arquivo `backend/agent/rag.py` chama:

- embedding OpenAI: `text-embedding-3-small`
- dimensao: `1536`
- RPC Supabase: `match_documents`
- parametros da RPC:
  - `query_embedding`
  - `match_count`
- campos retornados:
  - `content`
  - `metadata`, com `metadata.source` opcional

## SQL minimo esperado

```sql
create extension if not exists vector;

create table if not exists public.documents (
  id bigserial primary key,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536) not null
);

create index if not exists documents_embedding_idx
on public.documents
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

create or replace function public.match_documents(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language sql
stable
as $$
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from public.documents
  order by documents.embedding <=> query_embedding
  limit match_count;
$$;
```

## O que eu preciso confirmar de voce

- Se a tabela ja existe, me passe o nome da tabela e os nomes das colunas.
- Se a funcao RPC ja existe, me confirme se ela se chama `match_documents`.
- Se os embeddings existentes nao foram gerados com `text-embedding-3-small`, me diga qual modelo/dimensao foi usado.
