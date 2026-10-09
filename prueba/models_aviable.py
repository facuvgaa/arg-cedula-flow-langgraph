import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

print("--- Modelos disponibles para tu API Key ---")
for model in client.models.list():
  if "generateContent" in model.supported_actions:
    print(f"ID: {model.name}")