import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

# Carga una imagen local pequeña para probar
with open("auto.jpg", "rb") as f:
  image_bytes = f.read()

try:
    print("Probando análisis de imagen con gemini-3.5-flash...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            "¿Qué ves en esta imagen?",
        ],
    )
    print("\n✅ Respuesta exitosa:")
    print(response.text)
except Exception as e:
    print("\n❌ Error:", e)