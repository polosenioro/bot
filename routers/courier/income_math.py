from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from database import cursor
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram.exceptions import TelegramBadRequest

router = Router()

DEFAULT_STATE = {
    "transport": "bike",  # walk | bike | car
    "days": 20,
    "hours": 8
}

TRANSPORT_LABELS = {
    "walk": "🚶 Пешком",
    "bike": "🚲 Вело",
    "car": "🚗 Авто"
}

def income_keyboard(data: dict) -> InlineKeyboardMarkup:
    transport = data.get("transport", "walk")
    days = data.get("days", 20)
    hours = data.get("hours", 8)

    return InlineKeyboardMarkup(inline_keyboard=[
        # 🔹 Кнопка "Изменить город"
        [InlineKeyboardButton(text="🌆 Изменить город", callback_data="select_city_manual")],

        # 🔹 Заголовок "Как будете доставлять?"
        [InlineKeyboardButton(text="🚚 Как будете доставлять?", callback_data="noop")],

        # 🔹 Транспорт
        [
            InlineKeyboardButton(
                text=f"Пешком{' ✅' if transport == 'walk' else ''}",
                callback_data="inc_set_transport:walk"
            ),
            InlineKeyboardButton(
                text=f"Вело{' ✅' if transport == 'bike' else ''}",
                callback_data="inc_set_transport:bike"
            ),
            InlineKeyboardButton(
                text=f"Авто{' ✅' if transport == 'car' else ''}",
                callback_data="inc_set_transport:car"
            ),
        ],

        # 🔹 Заголовок "Рабочих дней"
        [InlineKeyboardButton(text="📅 Рабочих дней:", callback_data="noop")],

        # 🔹 Дни
        [
            InlineKeyboardButton(
                text=f"{d}{' ✅' if days == d else ''}",
                callback_data=f"inc_set_days:{d}"
            ) for d in [10, 15, 20, 25, 30]
        ],

        # 🔹 Заголовок "Часов в день"
        [InlineKeyboardButton(text="⏱ Часов в день:", callback_data="noop")],

        # 🔹 Часы (по 4 в ряд)
        *[
            [
                InlineKeyboardButton(
                    text=f"{h}{' ✅' if hours == h else ''}",
                    callback_data=f"inc_set_hours:{h}"
                ) for h in chunk
            ] for chunk in [range(4, 8), range(8, 13)]
        ],

        # 🔹 Назад
        [InlineKeyboardButton(text="⬅ Назад", callback_data="go_main_menu")]
    ])

@router.callback_query(F.data == "income_calc")
async def start_income_calc(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    cursor.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    city = result[0] if result and result[0] else None

    if not city:
        await callback.message.answer("❌ Сначала укажите город в разделе 'Доход курьера'.")
        return

    # получаем ставку по городу
    cursor.execute("SELECT walk FROM rates WHERE city = ?", (city,))
    row = cursor.fetchone()
    if not row:
        await callback.message.answer(f"❌ В городе <b>{city}</b> ставка не найдена.", parse_mode="HTML")
        return

    await state.set_data(DEFAULT_STATE)

    await callback.message.answer(
        f"📍 Ваш текущий город: <b>{city}</b>\n\n"
        f"📊 Чтобы рассчитать доход:\n"
        f"— по умолчанию: 8 часов в день × 20 дней\n"
        f"— нажимайте кнопки ниже, чтобы корректировать параметры",
        reply_markup=income_keyboard(DEFAULT_STATE),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("inc_set_transport:"))
async def set_transport(callback: CallbackQuery, state: FSMContext):
    transport = callback.data.split(":")[1]
    data = await state.get_data()
    data["transport"] = transport
    await state.set_data(data)
    await update_income_message(callback, data)

@router.callback_query(F.data.startswith("inc_set_days:"))
async def set_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split(":")[1])
    data = await state.get_data()
    data["days"] = days
    await state.set_data(data)
    await update_income_message(callback, data)

@router.callback_query(F.data.startswith("inc_set_hours:"))
async def set_hours(callback: CallbackQuery, state: FSMContext):
    hours = int(callback.data.split(":")[1])
    data = await state.get_data()
    data["hours"] = hours
    await state.set_data(data)
    await update_income_message(callback, data)

@router.callback_query(F.data == "noop")
async def ignore(callback: CallbackQuery):
    await callback.answer(cache_time=1)

async def update_income_message(callback: CallbackQuery, data: dict):
    user_id = callback.from_user.id

    from database import cursor
    cursor.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    city = result[0] if result and result[0] else None

    if not city:
        await callback.message.edit_text("❌ Сначала укажите город в разделе 'Доход курьера'.")
        return

    transport = data.get("transport")
    days = data.get("days")
    hours = data.get("hours")

    if not all([transport, days, hours]):
        await callback.message.edit_text("⚠️ Данные неполные. Повторите выбор.")
        return

    cursor.execute(f"SELECT {transport} FROM rates WHERE city = ?", (city,))
    row = cursor.fetchone()
    if not row:
        await callback.message.edit_text("❌ Ставка не найдена.")
        return

    rate = row[0]
    total = rate * days * hours

    new_text = (
        f"📍 Ваш текущий город: <b>{city}</b>\n\n"
        f"💼 График: <b>{days}</b> дней × <b>{hours}</b> часов\n"
        f"🚚 Тип: <b>{TRANSPORT_LABELS[transport]}</b>\n\n"
        f"💰 Потенциальный доход: <b>{total} ₽</b>"
    )
    new_markup = income_keyboard(data)

    try:
        await callback.message.edit_text(
            new_text,
            reply_markup=new_markup,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise e










