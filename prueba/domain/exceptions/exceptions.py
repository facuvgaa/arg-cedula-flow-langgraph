from abc import ABC


class DomainError(Exception):
    """Excepción base de dominio."""
    """Domain base exception."""
    pass

class IvalidVehicleCardError(DomainError):
    """Se dispara cuando la cédula no cumple con las invariantes de negocio."""
    """It is triggered when the ID card does not comply with the business invariants."""
    pass

class DocumentExtrationError(DomainError):
      """Se dispara cuando el extractor no logra procesar la imagen correctamente."""
      "It triggers when the extractor fails to process the image correctly."
      pass
