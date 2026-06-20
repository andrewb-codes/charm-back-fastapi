from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.profile import Gender, Role, Status


class ProfileResponse(BaseModel):
    id: int
    email: str
    name: str | None
    surname: str | None
    birthdate: date | None
    age: int | None
    about: str | None
    gender: Gender | None
    photo: str | None
    status: Status
    role: Role
    version: int
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    surname: str | None = Field(default=None, max_length=100)
    birthdate: date | None = None
    about: str | None = Field(default=None, max_length=1000)
    gender: Gender | None = None
    version: int

    @field_validator("birthdate")
    @classmethod
    def birthdate_must_be_in_past(cls, value: date | None) -> date | None:
        if value is not None and value >= date.today():
            raise ValueError("birthdate must be in the past")
        return value
