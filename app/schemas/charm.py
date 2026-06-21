import enum

from pydantic import BaseModel, Field


class CharmAction(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"


class CharmRequest(BaseModel):
    to_profile_id: int = Field(gt=0)
    action: CharmAction
