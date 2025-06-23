# keyboards/menu.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚀 Продолжить", callback_data="go_main_menu")]
])
