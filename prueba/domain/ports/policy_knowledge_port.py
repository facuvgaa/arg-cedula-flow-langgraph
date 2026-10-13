from abc import ABC, abstractmethod
from typing import List, Optional

class PolicyKnowledgePort(ABC):
    """Puerto de dominio para la base de conocimiento de pólizas (RAG)."""

    @abstractmethod
    async def search_relevant_clauses(
        self,
        query: str,
        top_k: int = 3,
        coverage_filter: Optional[str] = None
    ) -> List[str]:
        """Busca y retorna las cláusulas o condiciones más relevantes para la consulta del cliente.

        Args:
            query: La pregunta o duda del cliente (ej: "¿cubre granizo?", "¿cuántos km de grúa?").
            top_k: Cantidad máxima de fragmentos relevantes a retornar.
            coverage_filter: Filtro opcional por tipo de cobertura (ej: 'TERCEROS_COMPLETO', 'TODO_RIESGO').

        Returns:
            Lista de fragmentos de texto relevantes extraídos de las pólizas oficiales.
        """
        pass

