from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database.database_app import engine_a
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from static.template.criptoPassword import decrypt, encrypt
from sqlalchemy.future import select
from .setModels import ConnectModel, registrationModel
import jwt

router = APIRouter()

@router.post("/auth", summary="Авторизация пользователя")
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
                    "id": str(client.id),  
                    "lastname": client.lastname,
                    "firstname": client.firstname,
                    "middlename": client.middlename,
                    "email": client.email,
                    "phone": client.phone,
                    "login": client.login
                }

                token_client = jwt.encode(payload_client, "1e9cb1ff6950647229010fb1af7d932ba0e33f15688c59dd2e6252ab4a7e96e9", algorithm="HS256")

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


@router.post("/registration", summary="Регистрация нового пользователя")
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
            token = jwt.encode(token_data, "1e9cb1ff6950647229010fb1af7d932ba0e33f15688c59dd2e6252ab4a7e96e9", algorithm="HS256")

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



