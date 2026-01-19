from typing import Optional
from pydantic import BaseModel
import datetime

################# Users ########################

# Utilisateur dans la base de données
class Users(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    email: str | None = None
    hashed_password: str
    image_url: str | None = None
    arrival: datetime.datetime | None = None
    is_disabled: bool | None = None
    is_admin: bool | None = None
    is_visible: bool | None = None
    created_at: datetime.datetime | None = None

# class ActiveSession(BaseModel):
#     id: int
#     username: str
#     access_token: str
#     expiry_time: datetime.datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_disabled: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_visible: Optional[bool] = None

class UserRead(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    email: str | None = None
    image_url: str | None = None
    arrival: datetime.datetime | None = None
    is_disabled: bool | None = None
    is_admin: bool | None = None
    is_visible: bool | None = None
    created_at: datetime.datetime | None = None

class UserLogin(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str