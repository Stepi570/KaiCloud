import os
import shutil
from fastapi import Cookie,APIRouter, File, UploadFile
from typing import Annotated
from fast_api.models import Site_id 
from fastapi import APIRouter, Response
from database.requests import DBRequests
UPLOAD_FOLDER = "files"
router_api = APIRouter(prefix="/api", tags=["API"])

@router_api.post("/saitid")
async def get_id(data: Site_id, response: Response):
    db_requests = DBRequests()  
    telegram_id =  str(db_requests.check_id(data.id))
    if telegram_id == "False":
        return {"message": "ID не найден, зайдите в @kit_raspisanie_bot и получите ID в разделе Cloud"}
    response.set_cookie(
        key="telegram_id", 
        value=telegram_id, 
        httponly=True
    )
    return {"message": True}

@router_api.get("/check")
async def check_id(telegram_id: Annotated[str | None, Cookie()] = None):
    print(f"Проверка телеграм id")
    if telegram_id:
        db_requests = DBRequests()
        if db_requests.check_time_from_telegram_id(telegram_id):
            return True
    return False 


@router_api.post("/upload")
async def upload_file(file: UploadFile = File(...), telegram_id: Annotated[str | None, Cookie()] = None):
    file_location = os.path.join(f"{UPLOAD_FOLDER}/{telegram_id}", file.filename)
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Функция загрузки файла в разработке"}