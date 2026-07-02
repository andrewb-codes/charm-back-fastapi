from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

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


class PublicProfileResponse(BaseModel):
    id: int
    name: str | None
    surname: str | None
    birthdate: date | None
    age: int | None
    about: str | None
    gender: Gender | None
    photo: str | None


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100, pattern=r"\S")
    surname: str | None = Field(default=None, max_length=100, pattern=r"\S")
    birthdate: date | None = None
    about: str | None = Field(default=None, max_length=1000, pattern=r"\S")
    gender: Gender | None = None
    version: int

    @field_validator("birthdate")
    @classmethod
    def birthdate_must_be_in_past(cls, value: date | None) -> date | None:
        if value is not None and value >= date.today():
            raise ValueError("birthdate must be in the past")
        return value


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    current_password: str = Field(min_length=1)
    version: int


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)
    version: int


class MatchesResponse(BaseModel):
    items: list[PublicProfileResponse]
    has_next: bool


class AdminProfilesPageResponse(BaseModel):
    items: list[ProfileResponse]
    has_next: bool


class AdminProfileStatusUpdateRequest(BaseModel):
    status: Status
    version: int = Field(ge=0)


class AdminProfileRoleUpdateRequest(BaseModel):
    role: Role
    version: int = Field(ge=0)
