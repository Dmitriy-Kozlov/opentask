from pydantic import BaseModel


class TaskAdd(BaseModel):
    headline: str
    text: str


class TaskRead(TaskAdd):
    id: int


from auth.schemas import UserRead


class TaskRel(TaskRead):
    users: list["UserRead"]