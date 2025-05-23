import bcrypt # Для хеширования и проверки паролей
from jose import JWTError, jwt
from typing import Dict # Для типизации словарей и любых типов данных
from fastapi import HTTPException, status, Request, Query, Depends # HTTPException и status для обработки ошибок FastAPI, Request для доступа к заголовкам
from beanie import PydanticObjectId # Для работы с ID документов MongoDB (PydanticObjectId) # Для зависимостей FastAPI
from backend.core.config import JWT_ALGORITHM, REFRESH_SECRET_KEY,logger # Конфигурация для JWT
from backend.core.dependencies import get_admin_user,generate_tokens # Зависимость для получения администратора
from backend.models.user import User # Модель пользователя
from backend.schemas.token import RefreshTokenRequest # Схема для запроса refresh-токена
from backend.schemas.user import LoginUserRequest # Схема для запроса логина
from backend.models.embedded import RefreshTokenEmbedded # Вложенная модель для refresh-токена




class AdminAuthService:
    @staticmethod
    async def admin_check(admin_user: User = Depends(get_admin_user)):
        return {"isAuthenticated": True}
    
    @staticmethod
    async def admin_login(request_data: LoginUserRequest, request: Request):
        """
        **Метод для входа администратора в систему.**
        Принимает email и пароль администратора.
        **Возвращает:**
        - `access_token`: JWT токен для аутентификации в последующих запросах.
        - `refresh_token`: Токен для обновления `access_token`.
        """
        try:
            admin = await User.find_one({"email": request_data.email, "role": "admin"})
            if not admin:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверные учетные данные или недостаточно прав')

            is_match = bcrypt.checkpw(request_data.password.encode('utf-8'), admin.password.encode('utf-8'))
            if not is_match:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Неверные учетные данные')

            tokens = generate_tokens(admin)
            admin_agent = request.headers.get('user-agent', 'Unknown')
            refresh_token_data = RefreshTokenEmbedded(token=tokens['refreshToken'], userAgent=admin_agent)

            await User.find_one(User.id == admin.id).update({"$push": {'refreshTokens': refresh_token_data}})

            return {
                'success': True,
                'accessToken': tokens['accessToken'],
                'refreshToken': tokens['refreshToken'],
                'admin': {
                    'id': str(admin.id),
                    'email': admin.email,
                    'role': admin.role
                }
            }

        except Exception as err:
            logger.error(f'Ошибка при логине администратора: {err}', exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при логине администратора')

    @staticmethod
    async def admin_refresh_token(request_data: RefreshTokenRequest, request: Request):
        """
        **Метод для обновления refresh-токена администратора.**
        Принимает refresh-токен и возвращает новый access-токен.
        **Возвращает:**
        - `access_token`: Новый JWT токен для аутентификации в последующих запросах.
        - `refresh_token`: Новый токен для обновления `access_token`.
        """
        try:
            
            try:
                payload = jwt.decode(
                    request_data.refreshToken,
                    REFRESH_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM]
                )
                user_id = payload.get("userId")
                role = payload.get("role")

                if not user_id or role != "admin":
                    logger.warning(f"Invalid refresh token payload: userId={user_id}, role={role}")
                    raise JWTError("Invalid token payload")
            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            
            admin = await User.get(PydanticObjectId(user_id))

            if not admin or admin.role != "admin":
               
                logger.warning(f"User with ID {user_id} not found or not admin during refresh token.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or insufficient privileges"
                )

            
            old_refresh_token_found = False
            updated_refresh_tokens = []
            for rt in admin.refreshTokens:
                if rt.token == request_data.refreshToken:
                    old_refresh_token_found = True
                else:
                    updated_refresh_tokens.append(rt)

            if not old_refresh_token_found:
                logger.warning(
                    f"Old refresh token {request_data.refreshToken[:10]}... not found in user's refreshTokens array "
                    f"for user {user_id}. Possible replay attack or race condition."
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token already used or invalid"
                )

            
            tokens = generate_tokens(admin) 
            admin_agent = request.headers.get("user-agent", "Unknown")
            new_refresh_token_data = RefreshTokenEmbedded(
                token=tokens["refreshToken"],
                userAgent=admin_agent
            )

            
            updated_refresh_tokens.append(new_refresh_token_data)
            admin.refreshTokens = updated_refresh_tokens

            
            try:
                await admin.save()
            except Exception as save_err:
                logger.error(
                    f"Failed to save user {user_id} during refresh token: {save_err}. "
                    "Another process might have modified the document.", exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="Server conflict: Please try again."
                )

            return {
                "success": True,
                "accessToken": tokens["accessToken"],
                "refreshToken": tokens["refreshToken"]
            }

        except HTTPException:
            raise 
        except Exception as e:
            logger.error(f"Critical error during admin refresh token process: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed due to internal server error"
            )
            
            
    @staticmethod
    async def admin_logout(request_data: RefreshTokenRequest):
        """
        **Метод для выхода администратора из системы.**
        Принимает refresh-токен и удаляет его из базы данных.
        **Возвращает:**
        - `success`: True, если выход прошел успешно.
        - `message`: Сообщение об успешном выходе.
        """
        try:
            if not request_data.refreshToken:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Refresh token is required')

            update_result = await User.find_one(
                {"role": "admin", 'refreshTokens.token': request_data.refreshToken}
            ).update({"$pull": {'refreshTokens': {'token': request_data.refreshToken}}})

            if update_result.modified_count == 0:
                user_with_token = await User.find_one({'refreshTokens.token': request_data.refreshToken})
                if not user_with_token:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Refresh токен не найден или уже недействителен')

            return {
                "success": True,
                "message": "Logout successful"
            }

        except Exception as err:
            logger.error('Admin logout error:', err, exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера при выходе администратора')

    