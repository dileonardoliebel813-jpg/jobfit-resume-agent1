from typing import Literal

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from urllib.parse import quote

from app.schemas.resume_schema import ResumeJSON
from app.services.resume_pdf_export import ContactInfo, build_resume_pdf

router = APIRouter(prefix="/export", tags=["export"])


class ContactInfoPayload(BaseModel):
    name: str = ""
    age: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    github: str = ""
    target_title: str = ""

    def to_contact_info(self) -> ContactInfo:
        return ContactInfo(
            name=self.name,
            age=self.age,
            phone=self.phone,
            email=self.email,
            location=self.location,
            github=self.github,
            target_title=self.target_title,
        )


class ExportRequest(BaseModel):
    resume_json: ResumeJSON
    format: str = "pdf"
    layout: str = "one_page"
    contact_info: ContactInfoPayload | None = None
    photo_mode: Literal["placeholder"] = "placeholder"


class ExportResponse(BaseModel):
    format: str
    filename: str
    download_url: str
    mock: bool = True


@router.post("/resume", response_model=None)
def export_resume(payload: ExportRequest) -> Response | ExportResponse:
    if payload.format.lower() != "pdf":
        return ExportResponse(
            format=payload.format,
            filename=f"{payload.resume_json.candidate_name.replace(' ', '_')}_resume.{payload.format}",
            download_url="/mock-downloads/resume",
        )

    pdf_bytes = build_resume_pdf(
        payload.resume_json,
        layout=payload.layout,
        contact_info=payload.contact_info.to_contact_info() if payload.contact_info else None,
        photo_mode=payload.photo_mode,
    )
    filename = f"{payload.resume_json.candidate_name.replace(' ', '_')}_resume.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=resume.pdf; filename*=UTF-8''{quote(filename)}"
        },
    )
