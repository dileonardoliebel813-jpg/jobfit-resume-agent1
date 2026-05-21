from pydantic import BaseModel, ConfigDict


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str
    matched_experience: str
    evidence_snippet: str
    confidence: float


class EvidenceBuildResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: list[EvidenceItem]
