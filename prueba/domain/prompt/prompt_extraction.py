def PromptExtraction() -> str:
    prompt = """Analiza minuciosamente la imagen de la cédula de identificación del vehículo (cédula verde o azul de Argentina) o documento del titular.

Determina qué cara de la cédula estás viendo:
1. FRENTE: Contiene los datos técnicos del vehículo (Dominio/Patente, Marca, Modelo, Tipo, Uso, Chasis/Cuadro, Motor, Vencimiento, y a veces año/modelo).
2. DORSO / REVERSO: Contiene los datos del titular (Nombre y apellido, DNI/Documento, Domicilio completo con localidad y provincia).

REGLAS DE EXTRACCIÓN E INFERENCIA:
- Si un campo no está presente o no es legible en la imagen, debes dejar ese campo en null.
- NUNCA escribas textos como "NO VISIBLE", "NO APLICA", "DESCONOCIDO", "N/A" ni strings vacíos. Si no se ve, pon null.
- Si ves el FRENTE:
  * Extrae con exactitud el dominio (patente), marca, modelo, motor y chasis.
  * Si en el modelo o texto figura el año de fabricación (ej: "ECOSPORT XLS 1.6 / 2010" o "MOD 2015"), extrae el año como número entero (ej: 2010). Si no figura, deja null.
- Si ves el DORSO:
  * Extrae nombre completo del titular, DNI y domicilio completo.
  * A partir de la localidad, partido o provincia del domicilio (ej: "San Miguel de Tucumán, Tucumán", "Córdoba Capital", "Rosario", "La Plata", "Palermo, CABA"), infiere el Código Postal de 4 dígitos correspondiente (ej: "4000", "5000", "2000", "1900", "1425"). Si no puedes deducirlo con certeza, deja null.
"""
    return prompt