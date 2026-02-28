import asyncio
import inspect
import os
import shutil
import traceback
from fastapi import Cookie,APIRouter, File, HTTPException, UploadFile
from typing import Annotated

from fastapi.responses import FileResponse
from errors.errors import error_safe
from fast_api.router.defs import get_folders_only
from telegram.main import send_file
from fast_api.models import Site_id
from fastapi import APIRouter, Response
from database.requests import DBRequests
from pydantic import BaseModel
import asyncio
UPLOAD_FOLDER = "files"
router_api = APIRouter(prefix="/api", tags=["API"])

class TextMessageModel(BaseModel):
    text: str


@router_api.post("/saitid")
async def get_id(data: Site_id, response: Response):
    try:
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
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))

@router_api.get("/check")
async def check_id(telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        if telegram_id:
            db_requests = DBRequests()
            if db_requests.check_time_from_telegram_id(telegram_id):
                return True
        return False
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))


@router_api.post("/upload")
async def upload_file(file: UploadFile = File(...), telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        file_location = os.path.join(f"{UPLOAD_FOLDER}/{telegram_id}", file.filename)

        if not DBRequests().check_time_from_telegram_id(telegram_id):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        DBRequests().new_file(telegram_id, str(file_location))

        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        asyncio.create_task(send_file(telegram_id, file_location))
        return {"message": "Файл успешно загружен"}
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))


@router_api.get("/download")
async def download_file(telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        if not DBRequests().check_time_from_telegram_id(telegram_id):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        folder_path = f"get_files/{telegram_id}"
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        spisok_folders = await get_folders_only(folder_path)
        folder_path = f"{folder_path}/{max(spisok_folders)}"

        files = os.listdir(folder_path)
        file_path = os.path.join(folder_path, files[0])
        filename = os.path.basename(file_path)
        print(f"Filename: {filename}") 
        return FileResponse(
                path=file_path,
                filename=filename,  # оригинальное имя файла
                media_type='application/octet-stream'
            )
    except HTTPException: 
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))


# API endpoints для текстовых сообщений
@router_api.post("/send_text")
async def send_text_to_telegram(data: TextMessageModel, telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        if not telegram_id:
            raise HTTPException(status_code=401, detail="Не авторизован")
        
        if not DBRequests().check_time_from_telegram_id(telegram_id):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        # Сохраняем сообщение в базе
        db_requests = DBRequests()
        db_requests.save_text_message(telegram_id, data.text, "to_telegram")
        
        # Отправляем сообщение в Telegram
        from telegram.main import send_text_message
        asyncio.create_task(send_text_message(telegram_id, data.text))
        
        return {"message": "Текст отправлен в Telegram", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))
        return {"message": "Ошибка при отправке", "success": False}


@router_api.get("/get_text_messages")
async def get_text_messages(telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        if not telegram_id:
            raise HTTPException(status_code=401, detail="Не авторизован")
        
        if not DBRequests().check_time_from_telegram_id(telegram_id):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        db_requests = DBRequests()
        # Получаем сообщения от Telegram (направление 'to_site')
        messages = db_requests.get_text_messages(telegram_id, "to_site")
        
        # Отмечаем как прочитанные
        db_requests.mark_messages_read(telegram_id, "to_site")
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.text,
                    "time": msg.time_send,
                    "direction": msg.direction
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))


@router_api.get("/check_new_text")
async def check_new_text_messages(telegram_id: Annotated[str | None, Cookie()] = None):
    try:
        if not telegram_id:
            raise HTTPException(status_code=401, detail="Не авторизован")
        
        if not DBRequests().check_time_from_telegram_id(telegram_id):
            raise HTTPException(status_code=403, detail="Cloud выключен!")
        
        db_requests = DBRequests()
        unread = db_requests.get_unread_messages(telegram_id, "to_site")
        
        return {"has_new": len(unread) > 0, "count": len(unread)}
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        def_name = inspect.currentframe().f_code.co_name
        asyncio.create_task(error_safe(def_name, error_trace))