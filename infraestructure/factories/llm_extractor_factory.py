import os 
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from infraestructure.adapters.gemini_vehicle_extractor_adapter import VehicleExtractorAdapter 
from dotenv import load_dotenv

load_dotenv()

class LlmExtractorFactory:
    @staticmethod
    def create()-> VehicleExtractorPort:
        provider = os.getenv('LLM_PROVIDER', 'gemini').lower()

        if provider == 'gemini':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
            return VehicleExtractorAdapter(api_key=api_key, model_name=model_name)
        else:
            return ValueError(f"Proveedor de LLM no soportado: '{provider}'")