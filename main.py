from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from static.template.verifications.isVerification import isVerification
from static.routers import authUser, user, transmissionType, engineVolume, carBrand, application
from fastapi.openapi.utils import get_openapi
from database.database_app import create_db_if_not_exists, create_tables 
import subprocess

def run_migrations():
    """Выполнить миграции перед запуском приложения."""
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"], 
            check=True,
            capture_output=True,
            text=True
        )
        print("Миграции успешно выполнены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении миграций: {e.stderr}")


create_db_if_not_exists()
create_tables()

run_migrations()


app = FastAPI()

# Используем OAuth2PasswordBearer для аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# app.include_router(isVerification, prefix="/verification", tags=["Подтверждение клиента"])
app.include_router(authUser.router, prefix="/authUser", tags=["Авторизация пользователя"])
app.include_router(user.router, prefix="/profile", tags=["Профиль"])
app.include_router(transmissionType.router, prefix="/transmissionType", tags=["Тип трансмиссии"])
app.include_router(carBrand.router, prefix="/carBrand", tags=["Марка автомобиля"])
app.include_router(engineVolume.router, prefix="/engineVolume", tags=["Объем двигателя"])
app.include_router(application.router, prefix="/application", tags=["Заявка"])


@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Защищенный маршрут (чтобы Swagger показывал "Authorize")
@app.get("/secure-data", tags=["Protected"])
async def secure_data(token: str = Depends(oauth2_scheme)):
    return {"message": "This is a protected route", "token": token}

# Функция для изменения OpenAPI-схемы (убираем Bearer)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="Описание API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization", 
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Заменяем стандартную OpenAPI-схему
app.openapi = custom_openapi






