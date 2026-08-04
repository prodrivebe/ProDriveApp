"""Local filesystem storage implementation."""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.common.exceptions import ValidationError
from app.config.settings import Settings

ALLOWED_LOGO_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
    }
)
LOGO_EXTENSION_BY_CONTENT_TYPE: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
ALLOWED_PHOTO_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
    }
)
PHOTO_EXTENSION_BY_CONTENT_TYPE: dict[str, str] = LOGO_EXTENSION_BY_CONTENT_TYPE
ALLOWED_DOCUMENT_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/pdf",
    }
)
DOCUMENT_EXTENSION_BY_CONTENT_TYPE: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


class LocalFileStorage:
    """Store uploaded files on the local filesystem."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._root = Path(settings.upload_root_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def save_company_logo(
        self,
        *,
        company_id: uuid.UUID,
        upload_file: UploadFile,
    ) -> str:
        """Validate and persist a company logo upload."""
        if upload_file.content_type not in ALLOWED_LOGO_CONTENT_TYPES:
            raise ValidationError(
                code="INVALID_LOGO_TYPE",
                message="Logo must be a PNG, JPEG, or WEBP image.",
            )

        content = upload_file.file.read()
        max_bytes = self._settings.max_logo_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                code="LOGO_TOO_LARGE",
                message=(
                    f"Logo must be smaller than {self._settings.max_logo_size_mb} MB."
                ),
            )

        extension = LOGO_EXTENSION_BY_CONTENT_TYPE[upload_file.content_type or ""]
        company_dir = self._root / "companies" / str(company_id)
        company_dir.mkdir(parents=True, exist_ok=True)

        for existing_logo in company_dir.glob("logo.*"):
            existing_logo.unlink(missing_ok=True)

        logo_path = company_dir / f"logo{extension}"
        logo_path.write_bytes(content)

        relative_path = logo_path.relative_to(self._root).as_posix()
        return f"/uploads/{relative_path}"

    def save_vehicle_photo(
        self,
        *,
        company_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        upload_file: UploadFile,
    ) -> str:
        """Validate and persist a vehicle photo upload."""
        if upload_file.content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            raise ValidationError(
                code="INVALID_PHOTO_TYPE",
                message="Photo must be a PNG, JPEG, or WEBP image.",
            )

        content = upload_file.file.read()
        max_bytes = self._settings.max_photo_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                code="PHOTO_TOO_LARGE",
                message=f"Photo must be smaller than {self._settings.max_photo_size_mb} MB.",
            )

        extension = PHOTO_EXTENSION_BY_CONTENT_TYPE[upload_file.content_type or ""]
        photo_dir = self._root / "companies" / str(company_id) / "vehicles" / str(vehicle_id)
        photo_dir.mkdir(parents=True, exist_ok=True)
        photo_path = photo_dir / f"{uuid.uuid4()}{extension}"
        photo_path.write_bytes(content)
        relative_path = photo_path.relative_to(self._root).as_posix()
        return f"/uploads/{relative_path}"

    def save_order_document(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        filename: str,
        content: bytes,
    ) -> str:
        """Persist generated document bytes for an order."""
        document_dir = self._root / "companies" / str(company_id) / "orders" / str(order_id)
        document_dir.mkdir(parents=True, exist_ok=True)
        document_path = document_dir / filename
        document_path.write_bytes(content)
        relative_path = document_path.relative_to(self._root).as_posix()
        return f"/uploads/{relative_path}"

    def save_signed_document(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        upload_file: UploadFile,
    ) -> str:
        """Validate and persist an uploaded signed document."""
        if upload_file.content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
            raise ValidationError(
                code="INVALID_DOCUMENT_TYPE",
                message="Document must be a PNG, JPEG, WEBP, or PDF file.",
            )

        content = upload_file.file.read()
        max_bytes = self._settings.max_document_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                code="DOCUMENT_TOO_LARGE",
                message=(
                    f"Document must be smaller than {self._settings.max_document_size_mb} MB."
                ),
            )

        extension = DOCUMENT_EXTENSION_BY_CONTENT_TYPE[upload_file.content_type or ""]
        document_dir = self._root / "companies" / str(company_id) / "orders" / str(order_id)
        document_dir.mkdir(parents=True, exist_ok=True)
        document_path = document_dir / f"signed-{uuid.uuid4()}{extension}"
        document_path.write_bytes(content)
        relative_path = document_path.relative_to(self._root).as_posix()
        return f"/uploads/{relative_path}"

    def delete_file(self, file_path: str) -> None:
        """Delete a stored file referenced by its public upload path."""
        if not file_path.startswith("/uploads/"):
            return
        relative_path = file_path.removeprefix("/uploads/")
        target = self._root / relative_path
        target.unlink(missing_ok=True)
