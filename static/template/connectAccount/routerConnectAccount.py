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

                token_client = jwt.encode(payload_client, SECRET_KEY, algorithm="HS256")

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
            token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

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

# Получение данных пользователя
@personal_account.get("/user")
async def get_user_data(Authorization: str = Header(None)):
    if not Authorization:
        return JSONResponse(
            content={"code": 401, "message": "Токен авторизации обязателен."}, status_code=401
        )

    # Проверка формата Bearer токена
    if not Authorization.startswith("Bearer "):
        return JSONResponse(
            content={"code": 401, "message": "Неверный формат токена. Токен должен начинаться с 'Bearer '."},
            status_code=401,
        )

    # Извлечение токена из заголовка
    token = Authorization[7:]  # Убираем "Bearer "

    try:
        # Расшифровка токена
        decoded_token = decryptToken(token)
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
        )




from yookassa import Configuration, Payment
import uuid

# Настройка идентификатора магазина и секретного ключа
Configuration.account_id = '1015227'
Configuration.secret_key = 'test_mTsXdhSifwi6cApEwep6R0hMRMOHqWcGaWv3CrDSVis'


@personal_account.post("/teatPay")
async def teatPay():
    try:
        idempotence_key = str(uuid.uuid4())

        payment = Payment.create({
            "amount": {
                "value": "2.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "embedded"
            },
            "capture": True,
            "description": "Заказ №72"
        }, idempotence_key)

        confirmation_token = payment.confirmation.confirmation_token
        return confirmation_token

    except Exception as e:
        # Обработка ошибок и возврат сообщения об ошибке
        return {"error": str(e)}


from fastapi import FastAPI, Request, HTTPException
import json
import hmac
import hashlib
import base64

app = FastAPI()

# Ваш секретный ключ для проверки подписи
SECRET_KEY = 'test_mTsXdhSifwi6cApEwep6R0hMRMOHqWcGaWv3CrDSVis'

# Функция для проверки подписи уведомлений
def verify_signature(payload: str, signature: str) -> bool:
    """Проверка подписи уведомления от ЮKassa"""
    computed_signature = base64.b64encode(
        hmac.new(SECRET_KEY.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

    return hmac.compare_digest(computed_signature, signature)

@app.post("/webhook")
async def handle_payment_status(request: Request):
    try:
        # Получаем тело запроса (payload)
        payload = await request.body()
        signature = request.headers.get('X-Ya-Notification-Signature')

        # Проверка подписи
        if not signature or not verify_signature(payload.decode('utf-8'), signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Парсим JSON payload
        data = json.loads(payload)

        # Извлекаем событие и информацию о платеже
        event = data.get('event')
        payment_id = data['object']['id']
        status = data['object']['status']

        # Обработка событий в зависимости от статуса платежа
        if status == "succeeded":
            print(f"Платеж {payment_id} успешен!")
            # Например, обновите заказ в базе данных

        elif status == "canceled":
            print(f"Платеж {payment_id} отменён.")
            # Обработка отмены платежа

        elif status == "waiting_for_capture":
            print(f"Платеж {payment_id} ожидает подтверждения.")
            # Обработка состояния ожидания

        return {"status": "received"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
