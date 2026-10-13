import os
import glob
import time
from pypdf import PdfReader
import chromadb
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai_client = genai.Client(api_key=api_key)

chroma = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma.get_or_create_collection(name="insurance_policies")


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

pdf_files = glob.glob("resources/policies/*.pdf")
print(f"Archivos encontrados: {pdf_files}")

all_chunks = []
all_metadatas = []
all_ids = []

for pdf_path in pdf_files:
    file_name = os.path.basename(pdf_path)
    reader = PdfReader(pdf_path)
    
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
    
    chunks = chunk_text(full_text)
    print(f"📄 {file_name}: {len(chunks)} fragmentos generados.")
    
    for i, chunk in enumerate(chunks):
        all_chunks.append(chunk)
        all_metadatas.append({"source": file_name})
        all_ids.append(f"{file_name}_chunk_{i}")

print(f"\nProcesando y guardando {len(all_chunks)} fragmentos en ChromaDB...")

batch_size = 20

for i in range(0, len(all_chunks), batch_size):
    batch_chunks = all_chunks[i:i + batch_size]
    batch_ids = all_ids[i:i + batch_size]
    batch_metadatas = all_metadatas[i:i + batch_size]

    print(f"➡️ Lote {i+1} a {min(i + batch_size, len(all_chunks))} de {len(all_chunks)}...")

    for attempt in range(8):
        try:
            res = genai_client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch_chunks,
            )
            batch_vectors = [e.values for e in res.embeddings]

            # Guardamos directamente este lote en ChromaDB
            collection.upsert(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=batch_vectors,
                metadatas=batch_metadatas,
            )
            time.sleep(2.0)  # Pausa preventiva entre lotes
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 6
                print(f"   ⚠️ Límite por minuto alcanzado. Esperando {wait_time}s para reanudar...")
                time.sleep(wait_time)
            else:
                raise e

print(f"\n✅ ¡Completado con éxito! Colección 'insurance_policies' tiene {collection.count()} fragmentos indexados.")

  