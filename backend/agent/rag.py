import logging
import os

from supabase import Client, create_client

from .openai_client import get_openai_client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
RAG_ENABLED = os.getenv("RAG_ENABLED", "False").strip().lower() in {"1", "true", "yes", "on", "sim"}

supabase: Client | None = None
if RAG_ENABLED and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        logger.exception("Falha ao criar cliente Supabase")


def buscar_rag(query: str, limite: int = 5) -> list[dict]:
    if not RAG_ENABLED:
        logger.debug("RAG desativado; retornando contexto vazio")
        return []
    if not supabase:
        logger.debug("Supabase nao configurado; RAG retornando vazio")
        return []

    try:
        embedding = get_openai_client().embeddings.create(
            model="text-embedding-3-small",
            input=query,
        ).data[0].embedding
        result = supabase.rpc(
            "match_documents",
            {
                "query_embedding": embedding,
                "match_count": limite,
            },
        ).execute()
        return [
            {
                "content": doc["content"],
                "source": doc.get("metadata", {}).get("source", "desconhecida"),
            }
            for doc in result.data
        ]
    except Exception:
        logger.exception("Falha no RAG")
        return []


def buscar_rag_para_agente(query: str, limite: int = 5) -> str:
    if not RAG_ENABLED:
        return "RAG desativado para este ambiente."
    docs = buscar_rag(query, limite)
    if not docs:
        return "Nenhum documento relevante encontrado."
    linhas = [f"- {doc['content']} (fonte: {doc['source']})" for doc in docs]
    return "\n".join(linhas)
