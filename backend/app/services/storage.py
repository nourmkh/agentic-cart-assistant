import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()  # Load .env if present so environment variables are available during imports
try:
    from azure.storage.blob import BlobServiceClient
except Exception:
    BlobServiceClient = None


class LocalFallbackStorage:
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_file(self, data: bytes, filename: str, content_type: str) -> str:
        path = os.path.join(self.upload_dir, filename)
        with open(path, "wb") as f:
            f.write(data)
        # Return a relative path; the frontend can resolve /uploads/filename if served
        return f"/uploads/{filename}"


class AzureBlobStorage:
    def __init__(self, connection_string: str, container: str):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = container
        try:
            self.client.get_container_client(container).create_container()
        except Exception:
            pass

    async def upload_file(self, data: bytes, filename: str, content_type: str) -> str:
        blob = self.client.get_blob_client(container=self.container, blob=filename)
        blob.upload_blob(data, overwrite=True, content_settings=None)
        # Construct blob URL
        account_url = self.client.url
        return f"{account_url}/{self.container}/{filename}"


# Initialize storage service using environment variables
AZURE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "images")

if AZURE_CONN and BlobServiceClient:
    storage_service = AzureBlobStorage(AZURE_CONN, AZURE_CONTAINER)
else:
    if AZURE_CONN and not BlobServiceClient:
        logger.warning("azure-storage-blob not installed; falling back to local storage")
    storage_service = LocalFallbackStorage()
