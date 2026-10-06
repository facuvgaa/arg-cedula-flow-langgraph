from abc import ABC, abstractmethod


class FileStoragePort(ABC):

    @abstractmethod
    async def upload(self, file_bytes: bytes, file_name: str, content_type: str )-> str:
        """Sube un archivo y devuelve la ruta/key única guardada."""
        """Upload a file and return the saved unique path/key."""
        pass

    @abstractmethod
    async def get_url(self, file_path: str)-> str:
        """Returns a temporary or public read URL."""
        """Devuelve una URL de lectura temporal o pública."""
        pass