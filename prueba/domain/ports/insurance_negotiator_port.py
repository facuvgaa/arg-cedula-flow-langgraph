from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class InsuranceNegotiatorPort(ABC):
    @abstractmethod
    async def negotiate(
        self,
        user_message: str,
        context: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Negociación comercial y respuesta a dudas basándose en el contexto del vehículo y cotizaciones.

        Retorna un diccionario estructurado garantizado:
        {
            "reply": str,                      # Respuesta para el usuario
            "intent": "ASKING_QUESTION" | "HIRE_SELECTED",
            "selected_coverage": Optional[str] # "RESPONSABILIDAD_CIVIL" | "TERCEROS_COMPLETO" | "TODO_RIESGO" | None
        }
        """
        pass


