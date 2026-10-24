import os 
from typing import Optional
from dotenv import load_dotenv

from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.missing_data_message_port import MissingDataMessagePort
from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from domain.ports.policy_knowledge_port import PolicyKnowledgePort

from infraestructure.adapters.google import (
    VehicleExtractorAdapter as GeminiVehicleExtractorAdapter,
    GeminiMissingDataAdapter,
    GeminiInsuranceNegotiatorAdapter,
)
from infraestructure.adapters.bedrock import (
    BedrockVehicleExtractorAdapter,
    BedrockMissingDataAdapter,
    BedrockInsuranceNegotiatorAdapter,
)
from infraestructure.adapters.chroma import ChromaPolicyKnowledgeAdapter

load_dotenv()


class LlmExtractorFactory:
    @staticmethod
    def create() -> VehicleExtractorPort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider in ('gemini', 'google'):
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            return GeminiVehicleExtractorAdapter(api_key=api_key, model_name=model_name)
        elif provider in ('bedrock', 'aws', 'aws-bedrock'):
            return BedrockVehicleExtractorAdapter()
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_missing_data_adapter() -> MissingDataMessagePort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider in ('gemini', 'google'):
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            return GeminiMissingDataAdapter(api_key=api_key, model_name=model_name)
        elif provider in ('bedrock', 'aws', 'aws-bedrock'):
            return BedrockMissingDataAdapter()
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_insurance_negotiator_adapter() -> InsuranceNegotiatorPort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider in ('gemini', 'google'):
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            return GeminiInsuranceNegotiatorAdapter(api_key=api_key, model_name=model_name)
        elif provider in ('bedrock', 'aws', 'aws-bedrock'):
            return BedrockInsuranceNegotiatorAdapter()
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_policy_knowledge_adapter() -> Optional[PolicyKnowledgePort]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ℹ️ Info: GEMINI_API_KEY no encontrada. Continuando sin RAG de pólizas.")
            return None
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", 8000))
        try:
            return ChromaPolicyKnowledgeAdapter(
                api_key=api_key,
                chroma_host=chroma_host,
                chroma_port=chroma_port,
            )
        except Exception as e:
            print(f"⚠️ Advertencia: No se pudo conectar a ChromaDB ({e}). Continuando sin RAG de pólizas.")
            return None
