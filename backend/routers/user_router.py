from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File
from backend.services.user_service import UserService 
from backend.core.dependencies import get_current_user 

from backend.schemas.user import CreateUserRequest, LoginUserRequest, UserResponseBase, UpdateUserRequest  
from backend.models.user import User
from backend.schemas.token import RefreshTokenRequest

router = APIRouter(prefix="/api", tags=["User"])

@router.post('/create/user', status_code=status.HTTP_201_CREATED)
async def create_user_route(request_data: CreateUserRequest):
    """
    **Эндпоинт для создания нового пользователя.**
    
    Принимает данные о пользователе и создает нового пользователя в системе.
    **Возвращает:**
    - `user`: Объект созданного пользователя.
    - `message`: Сообщение об успешном создании.
    """
    return await UserService.create_user(request_data)

@router.post('/login/user') 
async def login_user_route(request_data: LoginUserRequest):
    """
    **Эндпоинт для входа пользователя в систему.**
    Принимает email и пароль пользователя.
    **Возвращает:**
    - `access_token`: JWT токен для аутентификации в последующих запросах.
    - `refresh_token`: Токен для обновления `access_token`.
    """
    return await UserService.login_user(request_data)

@router.get('/user/data')
async def get_user_data_route(current_user: User = Depends(get_current_user)):
    """
    **Эндпоинт для получения данных о текущем пользователе.**
    Возвращает информацию о текущем пользователе.
    **Возвращает:**
    - `user`: Объект пользователя с его данными.
    """
    return await UserService.get_user_data(current_user)

@router.put('/update/user')
async def update_user_route(
    request_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user)
):
    """
    **Эндпоинт для обновления данных пользователя.**
    Принимает данные о пользователе и обновляет информацию в системе.
    **Параметры:**
    - `request_data`: Данные о пользователе (имя, email и т.д.).
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `user`: Объект обновленного пользователя.
    - `message`: Сообщение об успешном обновлении.
    """
    return await UserService.update_user(request_data, current_user)

@router.post('/logout')
async def logout_user_route(): 
    """
    **Эндпоинт для выхода пользователя из системы.**
    Принимает refresh-токен и удаляет его из базы данных.
    **Возвращает:**
    - `success`: True, если выход прошел успешно.
    - `message`: Сообщение об успешном выходе.
    """
    return await UserService.logout_user()

@router.post('/refresh-token')
async def refresh_access_token_route(request_data: RefreshTokenRequest): 
    """
    **Эндпоинт для обновления refresh-токена пользователя.**
    Принимает refresh-токен и возвращает новый access-токен.
    **Возвращает:**
    - `access_token`: Новый JWT токен для аутентификации в последующих запросах.
    - `refresh_token`: Новый токен для обновления `access_token
    """
    return await UserService.refresh_access_token(request_data) 

@router.post('/user/avatar')
async def upload_avatar_route(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    **Эндпоинт для загрузки аватара пользователя.**
    Принимает файл аватара и обновляет его в системе.
    **Параметры:**
    - `avatar`: Файл аватара (тип: image/*).
    - `current_user`: Текущий пользователь.
    **Возвращает:**
    - `avatar_url`: URL загруженного аватара.
    - `message`: Сообщение об успешной загрузке.
    """
    return await UserService.upload_avatar(avatar, current_user)