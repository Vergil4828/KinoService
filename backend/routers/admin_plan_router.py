from fastapi import APIRouter, Depends, Request
from beanie import PydanticObjectId

from backend.models.user import User
from backend.schemas.admin import AdminChangePlanRequest
from backend.services.admin_plan_service import AdminPlanService
from backend.core.dependencies import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin_Plans"])


@router.post("/plans/create", summary="Создать новый тарифный план")
async def create_plan_route(
    request_data: AdminChangePlanRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    """
    **Эндпоинт для создания нового тарифного плана.**
    
    Принимает данные о тарифном плане и создает новый план в системе.
    
    **Возвращает:**
    
    - `plan`: Объект созданного тарифного плана.
    - `message`: Сообщение об успешном создании.
    
    """
    return await AdminPlanService.admin_create_plan(request_data, request, admin_user)

@router.put("/plans/change/{planId}", summary="Изменить тарифный план")
async def change_plan_route(
    planId: PydanticObjectId,
    request_data: AdminChangePlanRequest,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    """
    **Эндпоинт для изменения существующего тарифного плана.**
    
    Принимает ID тарифного плана и новые данные о тарифном плане.
    Изменяет данные в системе.
    
    **Возвращает:**
    
    - `plan`: Объект измененного тарифного плана.
    - `message`: Сообщение об успешном изменении.
    
    """
    return await AdminPlanService.admin_change_plan(planId, request_data, request, admin_user)

@router.delete("/plans/delete/{planId}", summary="Удалить тарифный план")
async def delete_plan_route(
    planId: PydanticObjectId,
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    """
    **Эндпоинт для удаления тарифного плана.**
    
    Принимает ID тарифного плана и удаляет его из системы.
    
    **Возвращает:**
    
    - `success`: True, если удаление прошло успешно.
    - `message`: Сообщение об успешном удалении.
    
    """
    return await AdminPlanService.admin_delete_plan(planId, request, admin_user)
