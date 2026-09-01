"""Bounded upload validation for hostile email input."""

from __future__ import annotations

from pathlib import PurePosixPath

from fastapi import UploadFile

from .errors import AppError

READ_CHUNK_BYTES = 64 * 1024
MAX_FILENAME_LENGTH = 255


def safe_eml_filename(filename: str | None) -> str:
    """Return display-only basename metadata after validating the MVP extension."""

    if filename is None or not filename.strip():
        raise AppError(
            status_code=400,
            code="MISSING_FILENAME",
            message="The uploaded file must have a filename.",
            field="file",
        )
    basename = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1].strip()
    if basename in {"", ".", ".."} or len(basename) > MAX_FILENAME_LENGTH:
        raise AppError(
            status_code=400,
            code="INVALID_FILENAME",
            message="The uploaded filename is invalid.",
            field="file",
        )
    if PurePosixPath(basename).suffix.casefold() != ".eml":
        raise AppError(
            status_code=415,
            code="UNSUPPORTED_FILE_TYPE",
            message="Only .eml files are accepted.",
            field="file",
        )
    return basename


async def read_bounded_upload(upload: UploadFile, max_upload_bytes: int) -> bytes:
    """Read at most the configured limit plus one byte, then reject overflow."""

    content = bytearray()
    try:
        while chunk := await upload.read(READ_CHUNK_BYTES):
            content.extend(chunk)
            if len(content) > max_upload_bytes:
                raise AppError(
                    status_code=413,
                    code="UPLOAD_TOO_LARGE",
                    message="The uploaded file exceeds the configured size limit.",
                    field="file",
                )
    finally:
        await upload.close()
    if not content:
        raise AppError(
            status_code=400,
            code="EMPTY_FILE",
            message="The uploaded .eml file is empty.",
            field="file",
        )
    return bytes(content)

