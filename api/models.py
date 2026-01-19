import datetime as dt
from sqlmodel import SQLModel, Field

################# Users ########################

class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field()
    image_url: str | None = Field(default=None)
    arrival: dt.datetime | None = Field(default=None)
    is_disabled: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    is_visible: bool = Field(default=True)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)

# class ActiveSession(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     username: str = Field(index=True)
#     access_token: str = Field()
#     expiry_time: dt.datetime = Field()