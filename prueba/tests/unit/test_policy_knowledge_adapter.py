import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.ports.policy_knowledge_port import PolicyKnowledgePort
from infraestructure.adapters.chroma_policy_knowledge_adapter import ChromaPolicyKnowledgeAdapter
from infraestructure.workflows.langgraph.nodes.negotiate_insurance_and_faqs_node import NegotiateInsuranceAndFaqsNode
from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort

@pytest.mark.asyncio
async def test_chroma_policy_knowledge_adapter_search():
    mock_chroma = MagicMock()
    mock_collection = MagicMock()
    mock_chroma.get_or_create_collection.return_value = mock_collection
    
    mock_collection.count.return_value = 191
    mock_collection.query.return_value = {
        "documents": [["La asistencia al vehículo consiste en el servicio de auxilio mecánico o remolque..."]]
    }

    adapter = ChromaPolicyKnowledgeAdapter(
        api_key="fake-key",
        chroma_client=mock_chroma,
    )

    mock_embed = MagicMock()
    mock_content_embed = MagicMock()
    mock_content_embed.values = [0.1, 0.2, 0.3]
    mock_embed.embeddings = [mock_content_embed]
    adapter._genai_client.aio.models.embed_content = AsyncMock(return_value=mock_embed)

    clauses = await adapter.search_relevant_clauses("¿Tienen grúa?", top_k=1)

    assert len(clauses) == 1
    assert "auxilio mecánico o remolque" in clauses[0]
    mock_collection.query.assert_called_once()

@pytest.mark.asyncio
async def test_negotiate_node_injects_rag_clauses():
    negotiator_mock = AsyncMock(spec=InsuranceNegotiatorPort)
    knowledge_mock = AsyncMock(spec=PolicyKnowledgePort)

    knowledge_mock.search_relevant_clauses.return_value = [
        "El servicio de grúa cubre hasta 300 km en Terceros Completo."
    ]

    negotiator_mock.negotiate.return_value = {
        "reply": "Contamos con servicio de grúa hasta 300 km.",
        "intent": "ASKING_QUESTION",
        "selected_coverage": None,
        "customer_email": None,
        "customer_phone": None,
    }

    node = NegotiateInsuranceAndFaqsNode(
        negotitation_port=negotiator_mock,
        knowledge_port=knowledge_mock,
    )

    state = {
        "user_message": "¿Cuántos km de grúa tengo?",
        "quote_result": {"coverages": {"TERCEROS_COMPLETO": 35000}},
        "chat_history": [],
    }

    result = await node(state)

    knowledge_mock.search_relevant_clauses.assert_called_once_with(
        query="¿Cuántos km de grúa tengo?",
        top_k=2,
        coverage_filter=None,
    )

    assert result["status"] == "IN_NEGOTIATION"
    assert "300 km" in result["message"]

