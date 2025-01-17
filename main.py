from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from static.template.verifications.isVerification import isVerification
from static.template.connectAccount.routerConnectAccount import personal_account

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(isVerification, prefix="/Verification" , tags=["Verification client"])
app.include_router(personal_account, prefix="/personal_account")


@app.get("/")
async def read_root():
    return {"Hello": "World"}
