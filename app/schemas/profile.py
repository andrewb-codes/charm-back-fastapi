from datetime import date, datetime

from pydantic import BaseModel

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
