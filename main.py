import asyncio
import random
import logging
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    datefmt="%H:%M:%S"
)

@dataclass
class EnrichedCustomer:
    customer_id: int
    profile: Optional[dict] = None
    billing_status: Optional[dict] = None
    error: Optional[str] = None


# --- 1. SIMULACIÓN DE APIS EXTERNAS (I/O Bound) ---

async def fetch_customer_profile(customer_id: int) -> dict:
    """Simula una API de CRM (tarda entre 0.2s y 0.6s)."""
    delay = random.uniform(0.2, 0.6)
    await asyncio.sleep(delay)
    
    # Simulamos fallo aleatorio del 10%
    if random.random() < 0.10:
        raise ConnectionError(f"CRM API no responde para ID {customer_id}")
    
    return {"plan": "Premium", "region": "Sur"}


async def fetch_billing_status(customer_id: int) -> dict:
    """Simula una API de Facturación (tarda entre 0.3s y 0.7s)."""
    delay = random.uniform(0.3, 0.7)
    await asyncio.sleep(delay)
    
    # Simulamos fallo aleatorio del 10%
    if random.random() < 0.10:
        raise TimeoutError(f"Billing API timeout para ID {customer_id}")
    
    return {"debt_amount": 0.0, "status": "UP_TO_DATE"}


# --- 2. WORKER CON SEMÁFORO Y TOLERANCIA A FALLOS ---

async def enrich_single_customer(
    customer_id: int, 
    sem: asyncio.Semaphore, 
    results_queue: asyncio.Queue
):
    """
    Coordina la obtención de datos para un cliente sin bloquear
    y respetando el límite de concurrencia.
    """
    async with sem:
        logging.info(f"-> Procesando cliente {customer_id}...")
        
        profile_task = fetch_customer_profile(customer_id)
        billing_task = fetch_billing_status(customer_id)

        results = await asyncio.gather(profile_task, billing_task, return_exceptions=True)
        
        profile_res, billing_res = results
        
        errors = []
        profile_data = None
        billing_data = None

        if isinstance(profile_res, Exception):
            errors.append(f"ProfileError: {profile_res}")
        else:
            profile_data = profile_res

        if isinstance(billing_res, Exception):
            errors.append(f"BillingError: {billing_res}")
        else:
            billing_data = billing_res

        error_msg = "; ".join(errors) if errors else None
        
        enriched = EnrichedCustomer(
            customer_id=customer_id,
            profile=profile_data,
            billing_status=billing_data,
            error=error_msg
        )
        
        await results_queue.put(enriched)
        logging.info(f"<- Completado cliente {customer_id} (Con errores: {bool(error_msg)})")



async def pipeline_consumer(results_queue: asyncio.Queue, total_expected: int):
    """
    Simula el proceso downstream (ej. persistencia o publicación a Kafka).
    Consume los elementos a medida que van terminando.
    """
    processed = 0
    while processed < total_expected:
        item: EnrichedCustomer = await results_queue.get()
        processed += 1
        
        if item.error:
            logging.warning(f"[DLQ/Atención] Cliente {item.customer_id} tuvo fallos: {item.error}")
        else:
            logging.info(f"[Persistido] Cliente {item.customer_id} listo con plan {item.profile['plan']}.")
            
        results_queue.task_done()


# --- 4. ORQUESTADOR PRINCIPAL ---

async def main():
    customer_ids = list(range(1, 21))  # 20 clientes a procesar
    max_concurrency = 5                 # Límite estricto de llamadas simultáneas
    
    sem = asyncio.Semaphore(max_concurrency)
    results_queue = asyncio.Queue()

    logging.info(f"Iniciando batch de {len(customer_ids)} clientes con concurrencia máxima de {max_concurrency}")

    # Levantamos el consumidor en background
    consumer_task = asyncio.create_task(pipeline_consumer(results_queue, len(customer_ids)))

    # Ejecutamos las tareas dentro de un TaskGroup estructurado
    async with asyncio.TaskGroup() as tg:
        for cid in customer_ids:
            tg.create_task(enrich_single_customer(cid, sem, results_queue))

    # Esperamos a que el consumidor termine de procesar todos los elementos en cola
    await results_queue.join()
    await consumer_task
    logging.info("Batch finalizado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())