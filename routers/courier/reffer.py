# routers/courier/reffer.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import COURIER_BOT_USERNAME

router = Router()

@router.message(Command("get_ref_link"))
async def get_ref_link(message: Message):
    user_id = message.from_user.id
    link = f"https://t.me/{COURIER_BOT_USERNAME}?start={user_id}"
    await message.answer(f"Твоя реферальная ссылка:\n{link}")
