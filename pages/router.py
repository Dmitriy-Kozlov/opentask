from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from auth.models import User
from auth.router import get_all_users, get_user
from auth.usermanager import current_active_user
from task.router import get_tasks, get_my_tasks, get_task_by_id, get_user_tasks

router = APIRouter(prefix='/pages', tags=['Фронтенд'])
templates = Jinja2Templates(directory='templates')


@router.get('/')
async def get_index_html(request: Request):
    return templates.TemplateResponse(name='base.html', context={'request': request})


@router.get('/users')
async def get_users_html(request: Request, users=Depends(get_all_users), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='users.html', context={'request': request, "users": users, "user": user})


@router.get('/users/register')
async def get_users_register_form(request: Request):
    return templates.TemplateResponse(name='register_form.html', context={'request': request})


@router.get('/users/login')
async def get_users_login_form(request: Request):
    return templates.TemplateResponse(name='login_form.html', context={'request': request})



@router.get('/tasks')
async def get_tasks_html(request: Request, tasks=Depends(get_tasks), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='tasks.html', context={'request': request, "headline": "Список задач", "tasks": tasks, "user": user})


@router.get('/tasks/me')
async def get_my_tasks_html(request: Request, tasks=Depends(get_my_tasks), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='tasks_my.html', context={'request': request, "headline": "Список моих задач", "tasks": tasks, "user": user})


@router.get('/tasks/user/{user_id}')
async def get_user_tasks_html(request: Request, tasks=Depends(get_user_tasks), point_user: User = Depends(get_user), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='tasks_my.html', context={'request': request, "headline": "Список задач пользователя", "tasks": tasks, "user": user, "point_user": point_user})


@router.get('/tasks/create')
async def create_task_html(request: Request,):
    return templates.TemplateResponse(name='task_form.html', context={'request': request})


@router.get('/tasks/{task_id}')
async def get_my_tasks_html(request: Request, task=Depends(get_task_by_id), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='task.html', context={'request': request, "task": task, "user": user})


@router.get('/tasks/{task_id}/upload')
async def get_my_tasks_html(request: Request, task_id: int):
    return templates.TemplateResponse(name='file_form.html', context={'request': request, "task_id": task_id})


@router.get('/tasks/{task_id}/set_users')
async def get_my_tasks_html(request: Request, task_id: int, users=Depends(get_all_users), user: User = Depends(current_active_user)):
    return templates.TemplateResponse(name='users_choose_form.html', context={'request': request, "task_id": task_id, "users": users, "user": user})