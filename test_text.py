import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

models_to_test = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

print("=== PROBANDO SOLO TEXTO ===\n")

for model_name in models_to_test:
    print(f"Probando modelo: {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Di 'Hola, funciono correctamente' si puedes leer esto.",
        )
        print(f"✅ ÉXITO con {model_name}: {response.text.strip()}\n")
        break
    except Exception as e:
        print(f"❌ Error con {model_name}: {e}\n")
