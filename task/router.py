from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import NoResultFound

from auth.usermanager import current_active_user
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task, UserTask
from .schemas import TaskRel, TaskUserRead, TaskAdd
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
async def get_my_tasks(session: AsyncSession = Depends(get_async_session),
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
async def get_task_by_id(task_id: int,
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
async def complete_task(task_id: int,
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


@router.post("/")
async def create_task(new_task: TaskAdd,
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user),
                      ):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create task")
    new_task_db = Task(**new_task.dict())
    session.add(new_task_db)
    await session.commit()
    return {"message": "Task created"}


@router.put("/{task_id}", response_model=TaskRel)
async def update_task_add_users(task_id: int, users_id: list[int],
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update task")
    try:
        query = select(Task).filter_by(id=task_id).options(joinedload(Task.users).joinedload(UserTask.user))
        result = await session.execute(query)
        task = result.unique().scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    for id in users_id:
        new_user_task = UserTask(users_id=id, tasks_id=task_id)
        session.add(new_user_task)
        await session.commit()
    await session.refresh(task)
    return task
