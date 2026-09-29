from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    user_type: str | None = None
    age_range: str | None = None
    monthly_income: float | None = None
    currency: str | None = None
    monthly_budget: float | None = None


class ProfileOut(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
