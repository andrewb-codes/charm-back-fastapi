from pydantic import BaseModel, EmailStr, Field


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegistrationResponse(BaseModel):
    id: int
