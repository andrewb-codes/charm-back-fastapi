import enum

from pydantic import BaseModel, Field

from charm.schemas.profile import PublicProfileResponse


class CharmAction(enum.StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"


class CharmRequest(BaseModel):
    to_profile_id: int = Field(gt=0)
    action: CharmAction


class NextCharmResponse(BaseModel):
    profile: PublicProfileResponse | None
