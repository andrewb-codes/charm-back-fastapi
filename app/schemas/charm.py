import enum
from datetime import date

from pydantic import BaseModel, Field


class CharmAction(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"


class CharmRequest(BaseModel):
    to_profile_id: int = Field(gt=0)
    action: CharmAction


class CharmProfileResponse(BaseModel):
    id: int
    name: str | None
    surname: str | None
    birthdate: date | None
    age: int | None
    about: str | None
    photo: str | None


class NextCharmResponse(BaseModel):
    profile: CharmProfileResponse | None
