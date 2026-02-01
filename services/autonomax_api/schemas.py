from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OpsRunIn(BaseModel):
    # Optional so Cloud Scheduler can call with no body.
    task: str | None = None
    payload: dict | None = None
