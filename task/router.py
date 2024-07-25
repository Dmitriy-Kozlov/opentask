from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound

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


@router.get("/{task_id}", response_model=TaskUserRead)
async def get_tasks(task_id: int,
                    session: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user),
                    ):
    try:
        query = (select(UserTask).filter_by(tasks_id=task_id).filter_by(users_id=user.id)
                .options(joinedload(UserTask.task)))

        result = await session.execute(query)
        task = result.scalars().one()
        return task
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete")
async def get_tasks(task_id: int,
                    session: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user),
                    ):
    try:
        query = (select(UserTask)
                 .filter_by(tasks_id=task_id)
                 .filter_by(users_id=user.id))
        result = await session.execute(query)
        task = result.scalars().one()
        if task.completed:
            raise HTTPException(status_code=403, detail="Task already completed")
        task.completed = True
        session.add(task)
        await session.commit()
        return {"message": f"Task {task_id} completed"}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
