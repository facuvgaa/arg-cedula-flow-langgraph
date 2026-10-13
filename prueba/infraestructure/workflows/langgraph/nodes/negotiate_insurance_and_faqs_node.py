from typing import Any, Dict, Optional
from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from infraestructure.workflows.langgraph.state.cedula_workflow_state import CedulaWorkflowState
from domain.ports.policy_knowledge_port import PolicyKnowledgePort


class NegotiateInsuranceAndFaqsNode:
    def __init__(self, negotitation_port: InsuranceNegotiatorPort, knowledge_port: Optional[PolicyKnowledgePort] = None):
        self._negotiator = negotitation_port
        self._knowledge = knowledge_port




    async def __call__(self, state: CedulaWorkflowState)-> Dict[str, Any]:
        user_message = state.get("user_message") or ""
        history = list(state.get("chat_history") or [])

        existing_email = state.get("customer_email")
        existing_phone = state.get("customer_phone")
        existing_coverage = state.get("selected_coverage")

        clauses = []

        if self._knowledge and user_message:
            clauses = await self._knowledge.search_relevant_clauses(
                query=user_message,
                top_k=2,
                coverage_filter=existing_coverage
            )

        context = {
            "vehiculo": state.get("vehicle_data"),
            "year": state.get("year"),
            "cotizaciones": state.get("quote_result"),
            "cobertura_seleccionada": existing_coverage,
            "email_registrado": existing_email,
            "celular_registrado": existing_phone,
            "clausulas_oficiales_poliza": clauses,
        }

        result = await self._negotiator.negotiate(
            user_message=user_message,
            context=context,
            chat_history=history,
        )

        updated_history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": result["reply"]},
        ]

        email = result.get("customer_email") or existing_email
        phone = result.get("customer_phone") or existing_phone
        coverage = result.get("selected_coverage") or existing_coverage

        if result.get("intent") == "HIRE_SELECTED":
            # Si ya tenemos cobertura y ambos datos de contacto, estamos listos para emitir
            if coverage and email and phone:
                status = "READY_TO_HIRE"
            elif coverage and not email and not phone:
                status = "WAITING_CONTACT_DATA"
            elif coverage and not email:
                status = "WAITING_EMAIL"
            elif coverage and not phone:
                status = "WAITING_PHONE"
            else:
                status = "READY_TO_HIRE"

            return {
                "selected_coverage": coverage,
                "customer_email": email,
                "customer_phone": phone,
                "status": status,
                "message": result["reply"],
                "chat_history": updated_history,
            }

        return {
            "status": "IN_NEGOTIATION",
            "message": result["reply"],
            "chat_history": updated_history,
        }