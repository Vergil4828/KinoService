from fastapi import APIRouter, Depends, Request
from backend.schemas.user import LoginUserRequest
from backend.schemas.token import RefreshTokenRequest
from backend.services.admin_auth_service import AdminAuthService
from backend.core.dependencies import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin_Authentication"])


@router.post("/login", summary="Авторизация администратора")
async def admin_login_route(request_data: LoginUserRequest, request: Request):
    """
    **Эндпоинт для входа администратора в систему.**

    Принимает email и пароль администратора.

    **Возвращает:**
    - `access_token`: JWT токен для аутентификации в последующих запросах.
    - `refresh_token`: Токен для обновления `access_token`.

    """
    return await AdminAuthService.admin_login(request_data, request)


@router.post("/refresh-token", summary="Обновление refresh-токена администратора")
async def admin_refresh_token_route(
    request_data: RefreshTokenRequest, request: Request
):
    """
    **Эндпоинт для обновления refresh-токена администратора.**

    Принимает refresh-токен и возвращает новый access-токен.

    **Возвращает:**

    - `access_token`: Новый JWT токен для аутентификации в последующих запросах.
    - `refresh_token`: Новый токен для обновления `access_token`.

    """
    return await AdminAuthService.admin_refresh_token(request_data, request)


@router.post("/logout", summary="Выход администратора из системы")
async def admin_logout_route(request_data: RefreshTokenRequest):
    """
    **Эндпоинт для выхода администратора из системы.**

    Принимает refresh-токен и удаляет его из базы данных.

    **Возвращает:**

    - `success`: True, если выход прошел успешно.
    - `message`: Сообщение об успешном выходе.

    """
    return await AdminAuthService.admin_logout(request_data)


@router.get(
    "/check",
    dependencies=[Depends(get_admin_user)],
    summary="Проверка аутентификации администратора",
)
async def admin_check_route():
    """
    **Эндпоинт для проверки аутентификации администратора.**

    **Возвращает:**

    - `isAuthenticated`: True, если администратор аутентифицирован.
    - `message`: Сообщение об успешной аутентификации.

    """
    return {"isAuthenticated": True, "message": "Admin is authenticated"}
