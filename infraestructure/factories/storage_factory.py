import os
from domain.ports.file_storage_port import FileStoragePort
from infraestructure.adapters.minio_file_storage_adapter import MinioFileStorageAdapter

class StorageFactory:
    @staticmethod
    def create() -> FileStoragePort:
        provider = os.getenv("STORAGE_PROVIDER", "minio").lower()
        
        if provider in ("minio", "s3"):
            return MinioFileStorageAdapter(
                endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                bucket_name=os.getenv("MINIO_BUCKET", "cedulas"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            )
        raise ValueError(f"Proveedor de Storage no soportado: '{provider}'")