import asyncio
import json
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

class McpInsuranceClientAdapter:
    """Cliente SSE / JSON-RPC para comunicarse con el servidor Spring Boot MCP."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self._base_url = base_url.rstrip("/")

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una herramienta en el servidor Spring Boot MCP vía SSE y JSON-RPC."""
        sse_url = f"{self._base_url}/sse"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            async with client.stream("GET", sse_url, headers={"Accept": "text/event-stream"}) as sse_stream:
                lines_iter = sse_stream.aiter_lines()
                
                # 1. Obtener endpoint de mensajes
                message_endpoint = None
                async for line in lines_iter:
                    if line.startswith("data:"):
                        message_endpoint = line.replace("data:", "").strip()
                        break
                
                if not message_endpoint:
                    raise RuntimeError("No se pudo obtener el endpoint de mensajes desde SSE")

                post_url = f"{self._base_url}{message_endpoint}"

                # 2. Inicializar sesión MCP
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "fastapi-langgraph-client", "version": "1.0"}
                    }
                }
                await client.post(post_url, json=init_payload)

                # 3. Invocar herramienta tools/call
                call_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                await client.post(post_url, json=call_payload)

                # 4. Leer respuesta desde el stream SSE activo
                async for line in lines_iter:
                    if line.startswith("data:"):
                        data_str = line.replace("data:", "").strip()
                        try:
                            event_data = json.loads(data_str)
                            if event_data.get("id") == 2:
                                result = event_data.get("result", {})
                                content = result.get("content", [])
                                if content and "text" in content[0]:
                                    return json.loads(content[0]["text"])
                                return result
                        except Exception as e:
                            logger.error(f"Error parseando respuesta MCP: {e}")

        raise RuntimeError(f"No se recibió respuesta para la herramienta {tool_name}")

    async def calculate_quote(self, brand: str, model: str, year: int, postal_code: str) -> Dict[str, Any]:
        """Invoca calculate_insurance_quote en el servidor MCP."""
        args = {
            "brand": brand,
            "model": model,
            "year": int(year),
            "postalCode": str(postal_code)
        }
        return await self._execute_tool("calculate_insurance_quote", args)

    async def hire_policy(
        self,
        customer_name: str,
        customer_dni: str,
        customer_email: str,
        license_plate: str,
        brand: str,
        model: str,
        year: int,
        postal_code: str,
        coverage_type: str,
        green_card_url: Optional[str] = None,
        inspection_photos_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoca hire_insurance_policy en el servidor MCP."""
        args = {
            "customerName": customer_name,
            "customerDni": customer_dni or "",
            "customerEmail": customer_email or "",
            "licensePlate": license_plate or "",
            "brand": brand,
            "model": model,
            "year": int(year),
            "postalCode": str(postal_code),
            "coverageType": coverage_type.upper(),
            "greenCardPhotoUrl": green_card_url or "",
            "inspectionPhotosUrl": inspection_photos_url or ""
        }
        return await self._execute_tool("hire_insurance_policy", args)

