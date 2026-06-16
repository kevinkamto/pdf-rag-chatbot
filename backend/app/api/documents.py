"""Document-management endpoints: list, upload (add context), delete (remove context)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import require_management_secret
from app.core.config import get_settings
from app.models.schemas import DocumentList, DocumentOut
from app.services import document_service
from app.services.document_service import IngestionError

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_management_secret)],
)


@router.get("", response_model=DocumentList)
async def list_documents() -> DocumentList:
    docs = await document_service.list_documents()
    return DocumentList(documents=[DocumentOut.model_validate(d) for d in docs])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile) -> DocumentOut:
    settings = get_settings()
    filename = file.filename or "document.pdf"

    if not filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_mb} MB limit.",
        )

    try:
        doc = await document_service.add_pdf(data, filename)
    except IngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str) -> None:
    removed = await document_service.remove_document(document_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
