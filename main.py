from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from static.template.verifications.isVerification import isVerification
from static.template.connectAccount.routerConnectAccount import personal_account
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.openapi.utils import get_openapi

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

app.include_router(isVerification, prefix="/Verification", tags=["Verification client"])
app.include_router(personal_account, prefix="/personal_account")

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
            "name": "Authorization",  # Теперь вводится только токен
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Заменяем стандартную OpenAPI-схему
app.openapi = custom_openapi






