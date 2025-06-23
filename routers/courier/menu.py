# routers/courier/menu.py

from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from database import cursor  # нужен для получения ref_id из users

router = Router()


async def go_main_menu_target(message: Message | CallbackQuery):
    user_id = message.from_user.id if isinstance(message, (Message, CallbackQuery)) else None

    cursor.execute("SELECT ref_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    ref_id = result[0] if result and result[0] else "None"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Регистрация",
                web_app=WebAppInfo(
                    url=f"https://reg.eda.yandex.ru/?advertisement_campaign=forms_for_agents&user_invite_code=0d2ded991e71475aabdb658c01a9dcfe&utm_source=voronka&utm_content={ref_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ Информация", callback_data="work_info"),
            InlineKeyboardButton(text="💸 Доход курьера", callback_data="income_info")
        ],
        [
            InlineKeyboardButton(text="🛠 Поддержка", url="https://t.me/durov")
        ]
    ])

    text = "📍 Главное меню:\nВыберите нужный пункт:"
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "go_main_menu")
async def go_main_menu(callback: CallbackQuery):
    await go_main_menu_target(callback)
