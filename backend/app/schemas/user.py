from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt silently truncates (older versions) or raises (current versions)
    # on passwords over 72 bytes, so the upper bound isn't arbitrary.
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1)


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
