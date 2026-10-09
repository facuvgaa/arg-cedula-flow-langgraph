import io
import aioboto3
from domain.ports.file_storage_port import FileStoragePort


class MinioFileStorageAdapter(FileStoragePort):

  def __init__(
      self,
      endpoint: str,
      access_key: str,
      secret_key: str,
      bucket_name: str,
      secure: bool = False,
  ):
    self._bucket_name = bucket_name
    self._endpoint_url = (
        f"{'https' if secure else 'http'}://{endpoint}"
        if not endpoint.startswith("http")
        else endpoint
    )
    self._access_key = access_key
    self._secret_key = secret_key
    self._session = aioboto3.Session()

  def _get_client(self):
    return self._session.client(
        "s3",
        endpoint_url=self._endpoint_url,
        aws_access_key_id=self._access_key,
        aws_secret_access_key=self._secret_key,
    )

  async def upload(
      self, file_bytes: bytes, file_name: str, content_type: str
  ) -> str:
    async with self._get_client() as s3:

      try:
        await s3.head_bucket(Bucket=self._bucket_name)
      except Exception:
        await s3.create_bucket(Bucket=self._bucket_name)


      await s3.put_object(
          Bucket=self._bucket_name,
          Key=file_name,
          Body=file_bytes,
          ContentType=content_type,
      )

    return f"{self._bucket_name}/{file_name}"

  async def get_url(self, file_path: str) -> str:
    object_name = file_path.split("/")[-1]
    async with self._get_client() as s3:
      url = await s3.generate_presigned_url(
          "get_object",
          Params={"Bucket": self._bucket_name, "Key": object_name},
          ExpiresIn=3600,
      )
    return url