from pydantic import BaseModel, ConfigDict, Field, field_validator


class JDAnalyzeRequest(BaseModel):
    raw_jd: str = Field(..., min_length=1)

    @field_validator("raw_jd")
    @classmethod
    def raw_jd_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("raw_jd cannot be empty")
        return value


class ResumeStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_highlight: list[str]
    should_weaken: list[str]
    tone: str


class JDProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: str
    job_level: str
    job_type: str
    hard_requirements: list[str]
    core_tasks: list[str]
    required_skills: list[str]
    preferred_experience: list[str]
    hidden_preferences: list[str]
    resume_strategy: ResumeStrategy


JD_PROFILE_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "position": {"type": "string"},
        "job_level": {"type": "string"},
        "job_type": {"type": "string"},
        "hard_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 8,
        },
        "core_tasks": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 6,
        },
        "required_skills": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10,
        },
        "preferred_experience": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 6,
        },
        "hidden_preferences": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5,
        },
        "resume_strategy": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "must_highlight": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                },
                "should_weaken": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 4,
                },
                "tone": {"type": "string"},
            },
            "required": ["must_highlight", "should_weaken", "tone"],
        },
    },
    "required": [
        "position",
        "job_level",
        "job_type",
        "hard_requirements",
        "core_tasks",
        "required_skills",
        "preferred_experience",
        "hidden_preferences",
        "resume_strategy",
    ],
}


class JDAnalyzeResponse(BaseModel):
    jd_profile: JDProfile
