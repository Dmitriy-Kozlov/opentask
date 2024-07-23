from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task
from .schemas import TaskAdd, TaskRel
from auth.models import User

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

@router.get("/", response_model=list[TaskRel])
async def get_tasks(session: AsyncSession = Depends(get_async_session)):
    query = select(Task).options(joinedload(Task.users))
    result = await session.execute(query)
    tasks = result.unique().scalars().all()
    return tasks
