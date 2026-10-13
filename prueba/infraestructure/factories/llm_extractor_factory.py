import os 
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.missing_data_message_port import MissingDataMessagePort
from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from infraestructure.adapters.gemini_insurance_negotiator_adapter import GeminiInsuranceNegotiatorAdapter
from infraestructure.adapters.gemini_vehicle_extractor_adapter import VehicleExtractorAdapter 
from infraestructure.adapters.gemini_missing_data_adapter import GeminiMissingDataAdapter 
from dotenv import load_dotenv

from domain.ports.policy_knowledge_port import PolicyKnowledgePort
from infraestructure.adapters.chroma_policy_knowledge_adapter import ChromaPolicyKnowledgeAdapter

load_dotenv()


class LlmExtractorFactory:
    @staticmethod
    def create() -> VehicleExtractorPort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider == 'gemini':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            return VehicleExtractorAdapter(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_missing_data_adapter() -> MissingDataMessagePort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider == 'gemini':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            return GeminiMissingDataAdapter(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_insurance_negotiator_adapter() -> InsuranceNegotiatorPort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider == 'gemini':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            return GeminiInsuranceNegotiatorAdapter(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Proveedor de LLM no soportado: '{provider}'")

    @staticmethod
    def create_policy_knowledge_adapter() -> PolicyKnowledgePort:
        api_key = os.getenv("GEMINI_API_KEY")
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", 8000))
        return ChromaPolicyKnowledgeAdapter(
            api_key=api_key,
            chroma_host=chroma_host,
            chroma_port=chroma_port,
        )