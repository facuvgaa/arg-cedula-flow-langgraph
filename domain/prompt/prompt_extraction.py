def PromptExtraction():
    prompt = """Analiza minuciosamente la imagen de la cédula de identificación del vehículo (cédula verde/azul de Argentina).
                
                Extrae todos los datos del vehículo y del titular de manera exacta. 
                Determina correctamente si se trata de un automóvil (CAR) o de una motocicleta (MOTORBIKE).

                Devuelve la información estrictamente en formato JSON con la siguiente estructura:
                {
                  "tipo_vehiculo": "CAR" o "MOTORBIKE",
                  "dominio": "Patente del vehículo",
                  "marca": "Marca",
                  "modelo": "Modelo",
                  "tipo": "Tipo",
                  "chasis": "Número de chasis/cuadro",
                  "motor": "Número de motor",
                  "titular_nombre": "Nombre completo del titular",
                  "titular_documento": "DNI/CUIL del titular"
                }
                
                No incluyas introducciones, explicaciones ni formato markdown fuera del JSON."""
    return prompt