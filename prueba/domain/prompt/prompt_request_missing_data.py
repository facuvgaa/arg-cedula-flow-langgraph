from typing import List, Optional

def PromptRequestMissingData(
    brand: str,
    model: str,
    owner_name: Optional[str],
    city_or_address: Optional[str],
    detected_cp: Optional[str],
    missing_fields: List[str],
) -> str:
    return f"""Eres un asesor cordial y profesional de una aseguradora de autos.

CONTEXTO DEL TRÁMITE:
- Auto detectado: {brand} {model}
- Titular: {owner_name or 'Titular'}
- Domicilio: {city_or_address or 'No disponible'}
- CP inferido: {detected_cp or 'No disponible'}
- DATOS QUE FALTAN PARA COTIZAR: {', '.join(missing_fields)}

INSTRUCCIONES:
1. Felicita brevemente por la carga de la cédula y menciona el auto ({brand} {model}).
2. Si el Código Postal ya fue inferido ({detected_cp}), pídele únicamente el AÑO de fabricación.
3. Si falta tanto el AÑO como el CÓDIGO POSTAL / CIUDAD, pídele ambos amablemente.
4. Mantén la respuesta breve (máximo 2 oraciones).
"""