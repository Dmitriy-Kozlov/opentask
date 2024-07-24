from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from auth.usermanager import current_active_user
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task, UserTask
from .schemas import TaskRel, TaskUserRead
from auth.models import User

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=list[TaskRel])
async def get_tasks(session: AsyncSession = Depends(get_async_session)):
    query = select(Task).options(joinedload(Task.users).joinedload(UserTask.user))
    result = await session.execute(query)
    tasks = result.unique().scalars().all()
    return tasks


@router.get("/me", response_model=list[TaskUserRead])
async def get_tasks(session: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user),
                    is_completed: bool = None
                    ):
    query = (
        select(UserTask)
        .options(joinedload(UserTask.task))
        .filter(UserTask.users_id == user.id)
    )
    if is_completed is not None:
        query = query.filter(UserTask.completed == is_completed)

    result = await session.execute(query)
    tasks = result.unique().scalars().all()

    return tasks
