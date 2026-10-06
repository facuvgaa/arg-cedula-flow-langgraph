from dataclasses import dataclass
from typing import Optional



@dataclass(frozen=True)
class ContactOwner:
    phone_numer: Optional[str] = None
    mail: Optional[str] = None
