import chromadb
from typing import Optional, List
from domain.ports.policy_knowledge_port import PolicyKnowledgePort
from google import genai
from pypdf import PdfReader

class ChromaPolicyKnowledgeAdapter(PolicyKnowledgePort):
    def __init__(
        self,
        api_key,
        chroma_host: str = "localhost",
        chroma_port: int = 8000,
        collection_name: str = "insurance_policies",
        embedding_model: str = "gemini-embedding-001",
        chroma_client: Optional[chromadb.HttpClient] = None,
    ):
        self._genai_client = genai.Client(api_key=api_key)
        self._embedding_model = embedding_model
        self._chroma = chroma_client or chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self._collection = self._chroma.get_or_create_collection(collection_name)

    async def search_relevant_clauses(
        self,
        query: str,
        top_k: int = 3,
        coverage_filter: Optional[str] = None,
    ) -> List[str]:
        if self._collection.count() == 0:
            return []

        embed_res = await self._genai_client.aio.models.embed_content(
            model=self._embedding_model,
            contents=query,
        )

        query_vector = embed_res.embeddings[0].values

        query_args = {
            "query_embeddings": [query_vector],
            "n_results": top_k,
        }

        if coverage_filter:
            query_args["where"] = {"coverage": coverage_filter}

        results = self._collection.query(**query_args)
        docs = results.get("documents", [])
        return docs[0] if docs else []