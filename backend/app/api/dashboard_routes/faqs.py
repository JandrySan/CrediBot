from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.dashboard import FAQDeleteResponse, FAQItem, FAQUploadResponse
from app.services.dashboard.faq_service import FAQAdminService

router = APIRouter(prefix="/faq")


@router.post("/upload", response_model=FAQUploadResponse)
async def upload_faq(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        raw_content = (await file.read()).decode("utf-8-sig")
        return FAQAdminService(db).upload(file.filename or "", raw_content)
    except (UnicodeDecodeError, ValueError) as exc:
        return {"success": False, "message": str(exc)}


@router.get("", response_model=list[FAQItem])
def list_faqs(db: Session = Depends(get_db)) -> list[FAQItem]:
    return FAQAdminService(db).list_active()


@router.delete("/{faq_id}", response_model=FAQDeleteResponse)
def delete_faq(faq_id: int, db: Session = Depends(get_db)) -> dict:
    return FAQAdminService(db).delete(faq_id)
