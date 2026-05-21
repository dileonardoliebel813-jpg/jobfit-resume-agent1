from pydantic import BaseModel, ConfigDict, Field


class ProfileParseRequest(BaseModel):
    profile_text: str = Field(..., min_length=1)


class WorkExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    role: str
    duration: str
    highlights: list[str]
    skills: list[str]


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    headline: str
    skills: list[str]
    experiences: list[WorkExperience]
    education: list[str]


USER_PROFILE_JSON_SCHEMA = UserProfile.model_json_schema()


class ProfileParseResponse(BaseModel):
    user_profile: UserProfile
