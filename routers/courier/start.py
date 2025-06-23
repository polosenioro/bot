# routers/courier/start.py

from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError

from keyboards.menu import main_menu_keyboard
from database import insert_user_if_not_exists, get_user_by_id
from config import BOT_TOKEN_RECRUITER

from utils.recruiter_notify import notify_recruiter
from routers.courier.menu import go_main_menu_target

router = Router()

@router.message(CommandStart())
async def start_with_ref(message: Message, command: CommandObject):
    ref_id = command.args or None
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    if ref_id and str(ref_id) == str(user_id):
        await message.answer("Привет! Это бот для курьеров Яндекс Еды 👋")
        print(f"[!] Игнор: пользователь {user_id} перешёл по своей реф-ссылке")
        return

    existing_user = get_user_by_id(user_id)
    is_new_user = existing_user is None

    if is_new_user:
        insert_user_if_not_exists(
            user_id=user_id,
            username=username,
            ref_id=ref_id,
            city=None,
            first_name=first_name,
            last_name=last_name
        )
        await message.answer("Привет! Это бот для курьеров Яндекс Еды 👋", reply_markup=main_menu_keyboard)
    else:
        await go_main_menu_target(message)

    if is_new_user and ref_id:
        await notify_recruiter(
            ref_id=int(ref_id),
            first_name=first_name,
            last_name=last_name,
            username=username
        )
