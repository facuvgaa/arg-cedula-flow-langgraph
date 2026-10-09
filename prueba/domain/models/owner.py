from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Owner:
    full_name: str
    dni: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None