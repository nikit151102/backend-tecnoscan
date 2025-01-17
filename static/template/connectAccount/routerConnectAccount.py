from fastapi import APIRouter, HTTPException, Header, Depends
from static.template.token import generateToken,decryptToken
from fastapi.responses import JSONResponse
from database.database_app import engine_a
from models_db.models_request import User
from sqlalchemy.ext.asyncio import AsyncSession
from ..criptoPassword import decrypt, encrypt
from ..randomPassword import generate_temp_password
from sqlalchemy.future import select
from .setModels import ConnectModel, registrationModel
from .setModels import UpdateUserModel

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

            decrypted_password = decrypt({"iv": client.iv, "content": client.password})
            print("Расшифрованный пароль:", decrypted_password)

            if decrypted_password == password:
                payload_client = {
                    "user_id": str(client.id),
                    "LastName": client.lastname,
                    "FirstName": client.firstname,
                    "MiddleName": client.middlename,
                    "Email": client.email,
                    "Phone": client.phone,
                }
                token_client = generateToken(payload_client)
                return JSONResponse(
                    content={"code": 202, "userId": f"{client.id}", "token": token_client}, status_code=202
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


@personal_account.put("/registration")
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
            existing_user = await session.execute(
                select(User).filter((User.login == login) | (User.email == email))
            )
            existing_user = existing_user.scalar()

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

            return JSONResponse(
                content={"code": 201, "message": "Пользователь успешно зарегистрирован."}, status_code=201
            )
        except Exception as e:
            print("Ошибка регистрации:", str(e))
            return JSONResponse(
                content={"code": 500, "message": "Внутренняя ошибка сервера."}, status_code=500
            )




# Получение данных пользователя
@personal_account.get("/user")
async def get_user_data(Authorization: str = Header(None)):
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


# Удаление пользователя
@personal_account.delete("/user")
async def delete_user(Authorization: str = Header(None)):
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
        )backendTecnoScan