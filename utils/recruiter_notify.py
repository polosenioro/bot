# utils/recruiter_notify.py

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from config import BOT_TOKEN_RECRUITER

async def notify_recruiter(ref_id: int, first_name: str, last_name: str, username: str = None):
    try:
        if username:
            name_link = f"<a href='https://t.me/{username}'>{first_name} {last_name}</a>"
        else:
            name_link = f"{first_name} {last_name}"

        recruiter_bot = Bot(token=BOT_TOKEN_RECRUITER)

        await recruiter_bot.send_message(
            chat_id=ref_id,
            text=f"👤 <b>+1 потенциальный курьер!</b>\n{name_link}",
            parse_mode="HTML"
        )

        await recruiter_bot.session.close()
        print(f"[OK] Уведомление отправлено рекрутеру: {ref_id}")

    except TelegramForbiddenError:
        print(f"[!] Нельзя писать пользователю {ref_id} — TelegramForbiddenError")
    except Exception as e:
        import traceback
        traceback.print_exc()
