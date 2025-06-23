from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def start_recruiter(message: Message):
    await message.answer("Привет! Это бот для рекрутеров Яндекс Еды 👥")
