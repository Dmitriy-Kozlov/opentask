import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy.exc import NoResultFound
from starlette import status

from auth.schemas import UserRead, UserLinkToTask
from auth.usermanager import current_active_user, get_all_users
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task, UserTask
from .schemas import TaskRel, TaskUserRead, TaskAdd
from auth.models import User

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

"""
query = (
        select(Task.id, Task.headline, UserTask.completed, func.group_concat(User.username).label('users'))
        .join(UserTask, UserTask.tasks_id == Task.id)
        .join(User, User.id == UserTask.users_id)
        .filter(UserTask.completed == is_completed)
        .group_by(Task.id)
    )
    result = await session.execute(query)
    tasks = result.mapping().all()
"""


@router.get("/", response_model=list[TaskRel])
async def get_tasks(session: AsyncSession = Depends(get_async_session),
                    is_completed: bool = None,
                    user: User = Depends(current_active_user)
                    ):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to get tasklist")
    query = (
        select(Task).outerjoin(Task.users).outerjoin(UserTask.user)
        .options(contains_eager(Task.users).contains_eager(UserTask.user))
    )
    if is_completed is not None:
        query = query.filter(UserTask.completed == is_completed)
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


# @router.post("/")
# async def create_task(new_task: TaskAdd,
#                       session: AsyncSession = Depends(get_async_session),
#                       user: User = Depends(current_active_user),
#                       ):
#     if not user.is_superuser:
#         raise HTTPException(status_code=403, detail="Not authorized to create task")
#     new_task_db = Task(**new_task.dict())
#     session.add(new_task_db)
#     await session.commit()
#     return {"message": "Task created"}


def checker(data: str = Form(...)):
    try:
        return TaskAdd.model_validate_json(data)
    except ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


@router.post("/")
async def create_task(new_task: TaskAdd = Depends(checker),
                      file: UploadFile | None = None,
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user),
                      ):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create task")
    new_task_db = Task(**new_task.dict())
    session.add(new_task_db)
    await session.flush()
    if file:
        os.makedirs(f"static/taskfiles/{new_task_db.id}", exist_ok=True)
        print(os.path.isdir(f"static/taskfiles/{new_task_db.id}"))
        with open(f"static/taskfiles/{new_task_db.id}/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        new_task_db.file_name = file.filename
        new_task_db.file_mimetype = file.content_type
    await session.commit()
    return {"message": "Task created"}


@router.put("/{task_id}", response_model=TaskRel)
async def update_task_add_users(task_id: int, new_users: list[UserLinkToTask],
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
    query = select(User.id)
    result = await session.execute(query)
    user_id_from_db = set(result.scalars().all())
    new_users_id = {x.id for x in new_users}
    if not new_users_id.issubset(user_id_from_db):
        raise HTTPException(status_code=404, detail="Users not in database")
    old_task_user_id = {x.users_id for x in task.users}
    inter_user_id = old_task_user_id.intersection(new_users_id)
    for _id in new_users_id:
        if _id not in inter_user_id:
            new_user_task = UserTask(users_id=_id, tasks_id=task_id)
            session.add(new_user_task)
    for _id in old_task_user_id:
        if _id not in inter_user_id:
            stmt = delete(UserTask).filter_by(users_id=_id).filter_by(tasks_id=task_id)
            await session.execute(stmt)
    await session.commit()
    await session.refresh(task)
    return task
