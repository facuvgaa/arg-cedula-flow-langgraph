def PromptExtraction() -> str:
    prompt = """Analiza minuciosamente la imagen de la cédula de identificación del vehículo (cédula verde o azul de Argentina).

Determina qué cara de la cédula estás viendo:
1. FRENTE: Contiene los datos técnicos del vehículo (Dominio/Patente, Marca, Modelo, Tipo, Uso, Chasis/Cuadro, Motor, Vencimiento).
2. DORSO / REVERSO: Contiene los datos del titular (Nombre y apellido, DNI/Documento, Domicilio).

REGLAS ESTRICTAS DE EXTRACCIÓN:
- Si un campo no está presente o no es visible en la imagen (por ejemplo, al ver solo el dorso no hay patente ni motor), debes dejar ese campo en null. 
- NUNCA escribas textos como "NO VISIBLE", "NO APLICA", "DESCONOCIDO", "N/A" ni strings vacíos. Si no se ve, pon null.
- Si ves el frente, extrae con exactitud el dominio (patente), marca, modelo, motor y chasis.
- Si ves el dorso, extrae con exactitud el nombre completo del titular, DNI y domicilio completo.
"""
    return prompt