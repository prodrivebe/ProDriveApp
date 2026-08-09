"""File storage protocol for local and future cloud backends."""

from typing import Protocol
from uuid import UUID

from fastapi import UploadFile


class FileStorage(Protocol):
    """Abstract storage for uploaded and generated files."""

    def save_vehicle_photo(
        self,
        *,
        company_id: UUID,
        order_id: UUID,
        vehicle_id: UUID,
        upload_file: UploadFile,
    ) -> tuple[str, str, int, str]:
        """Return file_path, file_name, file_size, content_type."""

    def save_order_document(
        self,
        *,
        company_id: UUID,
        order_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> tuple[str, str, int]:
        """Return file_path, file_name, file_size."""

    def delete_file(self, file_path: str) -> None:
        """Delete a stored file."""
