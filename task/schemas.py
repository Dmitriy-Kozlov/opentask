from pydantic import BaseModel


class TaskAdd(BaseModel):
    headline: str
    text: str


class TaskRead(TaskAdd):
    id: int
    file_name: str | None
    file_mimetype: str | None
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