import datetime
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy.exc import NoResultFound
from starlette.responses import FileResponse, StreamingResponse

from auth.schemas import UserRead, UserLinkToTask
from auth.usermanager import current_active_user, get_all_users
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task, UserTask, TaskFile
from .schemas import TaskRel, TaskUserRead, TaskAdd, TaskRead
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
        .options(joinedload(Task.files)).order_by(Task.id.desc())
    )
    if is_completed is not None:
        query = query.filter(UserTask.completed == is_completed)
    result = await session.execute(query)
    tasks = result.unique().scalars().all()
    return tasks


@router.get("/user/{user_id}", response_model=list[TaskUserRead])
async def get_user_tasks(
                    user_id: int,
                    session: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user),
                    is_completed: bool = None
                    ):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to get tasklist")
    query = (
        select(UserTask).options(selectinload(UserTask.task).selectinload(Task.files))
        .filter_by(users_id=user_id).order_by(UserTask.tasks_id.desc())
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
        select(UserTask).options(selectinload(UserTask.task).selectinload(Task.files))
        .filter_by(users_id=user.id).order_by(UserTask.tasks_id.desc())
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
        query = (
            select(UserTask).outerjoin(UserTask.task).outerjoin(Task.files)
            .options(contains_eager(UserTask.task).contains_eager(Task.files))
            .filter(UserTask.tasks_id == task_id).filter(UserTask.users_id == user.id)
        )
        result = await session.execute(query)
        task = result.unique().scalars().one()
        return task
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/{task_id}/{file_id}/download")
async def download_files(
        task_id: int,
        file_id: int,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)):
    try:
        query = select(TaskFile).filter_by(task_id=task_id).filter_by(id=file_id)
        result = await session.execute(query)
        file = result.scalars().one()
        path = f"static/taskfiles/{task_id}/{file.name}"
        return FileResponse(path, media_type='application/octet-stream', filename=file.name)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="File not found")


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
        task.finished_at = datetime.datetime.utcnow()
        session.add(task)
        await session.commit()
        return {"message": f"Task {task_id} completed"}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")

# make change in fastapi/_compat.py for Optional[list[UploadFile]] = File(None)
# def is_sequence_field(field: ModelField) -> bool:
#     return field_annotation_is_sequence(field.field_info.annotation)
#     return field_annotation_is_sequence(
#     field.field_info.annotation
#     ) or field_annotation_is_optional_sequence(field.field_info.annotation)
#
#
# def field_annotation_is_optional_sequence(
#         annotation: Union[Type[Any], None]
#     ) -> bool:
#     origin = get_origin(annotation)
#     if origin is Union:
#         args = get_args(annotation)
#         for arg in args:
#             if hasattr(arg, "__origin__"):
#                 if arg.__origin__ in sequence_types:
#                     return True
#     return False


@router.post("/")
async def create_task(new_task: TaskAdd,
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create task")
    new_task_db = Task(** new_task.dict())
    session.add(new_task_db)
    await session.commit()
    return {"task_id": new_task_db.id}


@router.post("/{task_id}/upload")
async def upload_files_for_task(task_id: int,
                                files: list[UploadFile] = File(...),
                                session: AsyncSession = Depends(get_async_session),
                                user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to upload files")
    try:
        query = (select(Task).filter_by(id=task_id))
        result = await session.execute(query)
        task = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Task not found")
    os.makedirs(f"static/taskfiles/{task_id}", exist_ok=True)
    for file in files:
        new_file_db = TaskFile(name=file.filename, mimetype=file.content_type, task_id=task_id, owner_id=user.id)
        session.add(new_file_db)
        with open(f"static/taskfiles/{task_id}/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    await session.commit()
    return {"message": "Files uploaded"}


@router.put("/{task_id}", response_model=TaskRel)
async def update_task_add_users(task_id: int, new_users: list[UserLinkToTask],
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update task")
    try:
        query = (
            select(Task).filter_by(id=task_id)
            .options(joinedload(Task.users).joinedload(UserTask.user))
            .options(selectinload(Task.files))
        )
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
