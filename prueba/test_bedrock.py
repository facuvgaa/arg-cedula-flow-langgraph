import os
import boto3
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

MODEL_ID = "amazon.nova-pro-v1:0"  

try:
    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": "¿Qué es un microservicio? Respondé en una sola oración."}],
            }
        ],
    )

    respuesta = response["output"]["message"]["content"][0]["text"]
    print("\n--- Respuesta de AWS Bedrock ---")
    print(respuesta)

except Exception as e:
    print(f"\nError al invocar el modelo: {e}")