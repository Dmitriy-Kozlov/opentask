from datetime import datetime
from pydantic import BaseModel


class FileAdd(BaseModel):
    name: str
    mimetype: str


class FileRead(FileAdd):
    id: int
    created_at: datetime


class TaskAdd(BaseModel):
    headline: str
    text: str


class TaskRead(TaskAdd):
    id: int
    created_at: datetime
    files: list[FileRead]
    class Config:
        from_attributes = True


from auth.schemas import UserRead, UserReadSimple


class UserTaskRead(BaseModel):
    completed: bool
    user: UserReadSimple


class TaskUserRead(BaseModel):
    completed: bool
    task: TaskRead


class TaskRel(TaskRead):
    users: list[UserTaskRead]
    files: list[FileRead]