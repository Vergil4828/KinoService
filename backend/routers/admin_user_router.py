from fastapi import APIRouter, Depends, Request, Query
from beanie import PydanticObjectId

from backend.models.user import User
from backend.schemas.admin import AdminChangeUserRequest
from backend.services.admin_user_service import AdminUserService
from backend.core.dependencies import get_admin_user


router = APIRouter(prefix="/api/admin", tags=["Admin_Users"])


@router.get(
    "/users",
    dependencies=[Depends(get_admin_user)],
    summary="Получить список пользователей",
)
async def get_users_route(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(
        25, ge=0, description="Количество пользователей на странице (0 для всех)"
    ),
    search: str = Query("", alias="search", description="Поиск по email или username"),
):
    """
    **Эндпоинт для получения списка пользователей.**

    Принимает номер страницы и количество пользователей на странице.
    Возвращает список пользователей с их данными.

    **Параметры:**

    - `page`: Номер страницы (по умолчанию 1).
    - `limit`: Количество пользователей на странице (по умолчанию 25, 0 для всех).
    - `search`: Поиск по email или username (по умолчанию пустая строка).

    **Возвращает:**

    - `users`: Список пользователей с их данными.

    """
    return await AdminUserService.get_admin_users(page=page, limit=limit, search=search)


@router.put("/user/change/{userId}", summary="Изменить данные пользователя")
async def change_user_route(
    userId: PydanticObjectId,
    request_data: AdminChangeUserRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user),
):
    """
    **Эндпоинт для изменения данных пользователя.**

    Принимает ID пользователя и новые данные о пользователе.
    Изменяет данные в системе.

    **Возвращает:**

    - `user`: Объект измененного пользователя.
    - `message`: Сообщение об успешном изменении.

    """
    return await AdminUserService.admin_change_user(
        userId, request_data, request, admin_user
    )


@router.delete("/user/delete/{userId}", summary="Удалить пользователя")
async def delete_user_route(
    userId: PydanticObjectId,
    request: Request,
    admin_user: User = Depends(get_admin_user),
):
    """
    **Эндпоинт для удаления пользователя.**

    Принимает ID пользователя и удаляет его из системы.

    **Возвращает:**

    - `success`: True, если удаление прошло успешно.
    - `message`: Сообщение об успешном удалении.

    """
    return await AdminUserService.admin_delete_user(userId, request, admin_user)
