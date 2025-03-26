from fastapi import APIRouter, Depends
from static.template.token import decryptToken
from fastapi.responses import JSONResponse
from database.database_app import engine_a
from models import User
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .setModels import UpdateUserModel
import jwt

router = APIRouter()

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/", summary="Получение данных пользователя")
async def get_user_data(token: str = Depends(oauth2_scheme)):
    try:
        
        if token.startswith("Bearer "):
            token = token[7:]  
        decoded_token = decryptToken(token)
        print("decoded_token",decoded_token)
        user_id = decoded_token.get("id")

        if not user_id:
            return JSONResponse(
                content={"code": 401, "message": "Токен недействителен или истек."}, status_code=401
            )

        async with AsyncSession(engine_a) as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalar()

            if not user:
                return JSONResponse(
                    content={"code": 404, "message": "Пользователь не найден."}, status_code=404
                )

            return JSONResponse(
                content={
                    "code": 200,
                    "message": "Данные пользователя получены.",
                    "user": {
                        "id": str(user.id),
                        "lastname": user.lastname,
                        "firstname": user.firstname,
                        "middlename": user.middlename,
                        "phone": user.phone,
                        "email": user.email,
                        "login": user.login,
                    },
                },
                status_code=200,
            )
    except Exception as e:
        print("Ошибка получения данных пользователя:", str(e))
        return JSONResponse(
            content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
        )


@router.delete("/", summary="Удаление пользователя")
async def delete_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = decryptToken(token)
        
        user_id = decoded_token.get("id")

        async with AsyncSession(engine_a) as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalar()

            if not user:
                return JSONResponse(
                    content={"code": 404, "message": "Пользователь не найден."}, status_code=404
                )

            await session.delete(user)
            await session.commit()

            return JSONResponse(
                content={"code": 200, "message": "Пользователь успешно удален."}, status_code=200
            )
    except Exception as e:
        print("Ошибка удаления пользователя:", str(e))
        return JSONResponse(
            content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
        )


@router.patch("/", summary="Обновление данных пользователя")
async def update_user(request: UpdateUserModel, token: str = Depends(oauth2_scheme)):
    if not token:
        return JSONResponse(
            content={"code": 401, "message": "Токен авторизации обязателен."}, status_code=401
        )

    try:
        if token.startswith("Bearer "):
            token = token[7:]  
        decoded_token = decryptToken(token)
        user_id = decoded_token.get("id")
        async with AsyncSession(engine_a) as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalar()

            if not user:
                return JSONResponse(
                    content={"code": 404, "message": "Пользователь не найден."}, status_code=404
                )

            if request.lastname is not None:
                user.lastname = request.lastname
            if request.firstname is not None:
                user.firstname = request.firstname
            if request.middlename is not None:
                user.middlename = request.middlename
            if request.phone is not None:
                user.phone = request.phone
            if request.email is not None:
                user.email = request.email
            if request.login is not None:
                user.login = request.login

            await session.commit()

            return JSONResponse(
                content={"code": 200, "message": "Данные пользователя успешно обновлены.",  "user": {
            "lastname": request.lastname,
            "firstname": request.firstname,
            "middlename": request.middlename,
            "phone": request.phone,
            "email": request.email,
            "login": request.login,
        },},
                status_code=200,
            )
    except Exception as e:
        print("Ошибка изменения данных пользователя:", str(e))
        return JSONResponse(
            content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
        )


