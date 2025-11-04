import time
import asyncio
import aiohttp
from docx import Document
from .schemas import User

def generate_fake_document(user: User, content_type: str) -> str:
    if content_type == "docx":
        doc = Document()
        doc.add.heading(f'Карточка пользователя: {user.first_name}', 0)
        doc.add.paragraph(f'ИИН: {user.iin}')
        doc.add.paragraph(f'Номер телефона: {user.phone_number}')
        doc.add.paragpaph(f'Личное фото: {user.photo or "Отсутствует"}')
    else:
        time.sleep(3)
    fake_filename = f"user_{user.id}_document.{content_type}"
    fake_url = f"/generated_docs/{fake_filename}"
    return fake_url


async def send_callback(callback_url: str, document_url: str):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"status": "success", "document_url": document_url}
            async with session.post(callback_url, json=payload) as response:
                if response.status != 200:
                    print(f"Ошибка отправки, статус: {response.status}")
                else:
                    print(f"Успешно доставлено")
    except Exception as e:
        print(f"Критическая ошибка {callback_url}: {e}")


async def generate_and_send_callback(user: User, content_type: str, callback_url: str):
    from . import repository
    try:
        user = repository.get_user_by_id(user.id)
        link = generate_fake_document(user, content_type)
        await send_callback(callback_url, link)
    except Exception as e:
        error_payload = {"status": "error", "detail": str(e)}
        await send_callback(callback_url, str(error_payload))