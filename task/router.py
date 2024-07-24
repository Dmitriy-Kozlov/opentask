from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, selectinload

from auth.schemas import UserRel
from auth.usermanager import current_active_user
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task, UserTask
from .schemas import TaskRel
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


@router.get("/me", response_model=UserRel)
async def get_tasks(session: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user)):
    query = (
        select(User)
        .options(joinedload(User.tasks).joinedload(UserTask.task))
        .filter_by(id=user.id)
    )
    result = await session.execute(query)
    tasks = result.unique().scalars().first()

    return tasks
