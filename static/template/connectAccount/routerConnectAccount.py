from fastapi import APIRouter, HTTPException, Header, Depends
from static.template.token import generateToken,decryptToken
from fastapi.responses import JSONResponse
from database.database_app import engine_a
from models_db.models_request import User
from sqlalchemy.ext.asyncio import AsyncSession
from ..criptoPassword import decrypt, encrypt,secretKey
from ..randomPassword import generate_temp_password
from sqlalchemy.future import select
from .setModels import ConnectModel, registrationModel
from .setModels import UpdateUserModel
import jwt

personal_account = APIRouter()

@personal_account.post("/user")
async def connection(request: ConnectModel):
    async with AsyncSession(engine_a) as session:

        login = request.UserLogin
        password = request.UserPassword

        if not login or not password:
            return JSONResponse(
                content={"code": 400, "message": "Логин и пароль обязательны."}, status_code=400
            )

        try:
            client = await session.execute(select(User).filter(User.login == login))
            client = client.scalar()

            if not client:
                return JSONResponse(
                    content={"code": 404, "message": "Пользователь не найден."}, status_code=404
                )

            # Расшифровка пароля
            decrypted_password = decrypt({"iv": client.iv, "content": client.password})
            print("Расшифрованный пароль:", decrypted_password)

            if decrypted_password == password:
                payload_client = {
                    "id": str(client.id),  
                    "lastname": client.lastname,
                    "firstname": client.firstname,
                    "middlename": client.middlename,
                    "email": client.email,
                    "phone": client.phone,
                    "login": client.login
                }

                token_client = jwt.encode(payload_client, secretKey, algorithm="HS256")

                return JSONResponse(
                    content={
                        "code": 202,
                        "userId": str(client.id), 
                        "token": token_client
                    },
                    status_code=202
                )
            else:
                return JSONResponse(
                    content={"code": 401, "message": "Неверный логин или пароль."}, status_code=401
                )
        except Exception as e:
            print("Ошибка авторизации:", str(e))
            return JSONResponse(
                content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
            )


@personal_account.post("/registration")
async def create(request: registrationModel):
    async with AsyncSession(engine_a) as session:
        login = request.Login
        email = request.Email
        password = request.Password

        if not login or not email or not password:
            return JSONResponse(
                content={"code": 400, "message": "Логин, email и пароль обязательны."}, status_code=400
            )

        try:
            result = await session.execute(
                select(User).filter((User.login == login) | (User.email == email))
            )
            existing_user = result.scalar()

            if existing_user:
                return JSONResponse(
                    content={"code": 409, "message": "Пользователь с таким логином или email уже существует."},
                    status_code=409,
                )

            newPassword = encrypt(password)
            print("Зашифрованный пароль:", newPassword)

            New_user = User(
                lastname="",
                firstname="",
                middlename="",
                phone="",
                email=email,
                login=login,
                password=newPassword["content"],
                iv=newPassword["iv"],
            )
            session.add(New_user)
            await session.commit()
            await session.refresh(New_user) 

            token_data = {
                "id": str(New_user.id),
                "login": New_user.login,
                "email": New_user.email,
                "lastname": New_user.lastname,
                "firstname": New_user.firstname,
                "middlename": New_user.middlename,
                "phone": New_user.phone,
            }
            token = jwt.encode(token_data, secretKey, algorithm="HS256")

            return JSONResponse(
                content={
                    "code": 201,
                    "message": "Пользователь успешно зарегистрирован.",
                    "id": str(New_user.id),  
                    "token": token
                },
                status_code=201
            )
        except Exception as e:
            print("Ошибка регистрации:", str(e))
            return JSONResponse(
                content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
            )


from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@personal_account.get("/personal_account/user")
async def get_user_data(token: str = Depends(oauth2_scheme)):
    try:
        # Расшифровка токена
        decoded_token = decryptToken(token)
        print("decoded_token",decoded_token)
        user_id = decoded_token.get("id")

        if not user_id:
            return JSONResponse(
                content={"code": 401, "message": "Токен недействителен или истек."}, status_code=401
            )

        # Получение данных пользователя из базы
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

from fastapi import Depends

@personal_account.get("/debug/token")
async def debug_token(token: str = Depends(oauth2_scheme)):
    return {"received_token": token}


# Удаление пользователя
@personal_account.delete("/user")
async def delete_user(token: str = Depends(oauth2_scheme)):
    
    if not token:
        return JSONResponse(
            content={"code": 401, "message": "Токен авторизации обязателен."}, status_code=401
        )

    try:
        decoded_token = decryptToken(token)
        user_id = decoded_token.get("user_id")

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


# Изменение данных пользователя
@personal_account.patch("/user")
async def update_user(request: UpdateUserModel, Authorization: str = Header(None)):
    if not Authorization:
        return JSONResponse(
            content={"code": 401, "message": "Токен авторизации обязателен."}, status_code=401
        )

    try:
        decoded_token = decryptToken(Authorization)
        user_id = decoded_token.get("user_id")

        async with AsyncSession(engine_a) as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalar()

            if not user:
                return JSONResponse(
                    content={"code": 404, "message": "Пользователь не найден."}, status_code=404
                )

            # Обновляем поля пользователя, если они переданы в запросе
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
                content={"code": 200, "message": "Данные пользователя успешно обновлены."},
                status_code=200,
            )
    except Exception as e:
        print("Ошибка изменения данных пользователя:", str(e))
        return JSONResponse(
            content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
        )


