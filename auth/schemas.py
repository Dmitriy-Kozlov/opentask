from typing import Optional
from pydantic import BaseModel

from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    username: str
    lastname: str
    firstname: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: str
    password: str
    lastname: str
    firstname: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserReadSimple(BaseModel):
    id: int
    email: str
    username: str


from task.schemas import TaskUserRead


class UserRel(UserReadSimple):
    tasks: list[TaskUserRead]


class UserLinkToTask(BaseModel):
    id: int