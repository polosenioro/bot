from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from utils.geocode import get_city_from_coordinates
from database import cursor
from states.city import CitySelect

router = Router()

# Клавиатура с буквами А-Я
from database import get_used_city_letters

def letter_keyboard():
    available = get_used_city_letters()
    rows, row, count = [], [], 0

    for letter in "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ":
        if letter in available:
            row.append(InlineKeyboardButton(text=letter, callback_data=f"letter:{letter}"))
            count += 1
            if count % 6 == 0:
                rows.append(row)
                row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="income_info")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# показать выбор способа
@router.callback_query(F.data == "income_info")
async def show_income_options(callback: CallbackQuery, state: FSMContext):
    from database import cursor

    user_id = callback.from_user.id
    cursor.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    city_line = f"📍 Ваш текущий город: <b>{result[0]}</b>\n\n" if result and result[0] else ""

    # если есть город — сразу запуск расчёта
    if result and result[0]:
        from .income_math import start_income_calc
        await callback.message.delete()
        await start_income_calc(callback, state)
        return

    # иначе выбор города
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Отправить геолокацию", callback_data="send_location")],
        [InlineKeyboardButton(text="🏙 Выбрать город из списка", callback_data="select_city_manual")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="go_main_menu")]
    ])

    await callback.message.edit_text(
        f"{city_line}"
        "📊 Чтобы рассчитать доход:\n"
        "— отправьте геолокацию\n"
        "— или выберите город вручную",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.clear()

@router.callback_query(F.data == "send_location")
async def ask_geo(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    inline_geo_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⬅ Назад",
            callback_data="income_info"
        )]
    ])

    await callback.message.answer(
        "👇 Отправьте вашу геолокацию или вернитесь назад:",
        reply_markup=inline_geo_kb
    )

@router.callback_query(F.data == "geo_back_to_menu")
async def geo_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🏙 Выберите первую букву города:",
        reply_markup=letter_keyboard()
    )
    await callback.bot.send_message(
        callback.from_user.id
    )
    await state.set_state(CitySelect.waiting_for_letter)

@router.callback_query(F.data == "select_city_manual")
async def ask_letter(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🏙 Выберите первую букву города:",
        reply_markup=letter_keyboard()
    )
    await state.set_state(CitySelect.waiting_for_letter)

# Обработка геолокации
@router.message(F.location)
async def handle_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    city = get_city_from_coordinates(lat, lon)

    await state.update_data(geo_city=city)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="geo_city_yes")
    kb.button(text="❌ Нет", callback_data="geo_city_no")
    kb.adjust(2)

    await message.answer(
        f"📍 Вы находитесь в: <b>{city}</b>\n"
        "Вы действительно проживаете в этом городе?",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    
@router.callback_query(F.data == "geo_city_yes")
async def geo_city_confirmed(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    city = data.get("geo_city")

    if not city:
        lines = callback.message.text.splitlines()
        for line in lines:
            if line.startswith("📍 Вы находитесь в:"):
                city = line.replace("📍 Вы находитесь в:", "").strip()
                break

    if not city:
        await callback.message.edit_text("❌ Не удалось определить город.")
        return

    from database import cursor, conn
    from routers.courier.income_math import start_income_calc

    cursor.execute("SELECT * FROM rates WHERE city = ?", (city,))
    if cursor.fetchone():
        user_id = callback.from_user.id
        cursor.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))
        conn.commit()

        await callback.message.delete()
        await start_income_calc(callback, state)
    else:
        await callback.message.edit_text(
            f"❌ Город <b>{city}</b> не найден в базе.\n"
            "Выберите город вручную:",
            parse_mode="HTML",
            reply_markup=letter_keyboard()
        )


@router.callback_query(F.data == "geo_city_no")
async def geo_city_declined(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏙 Выберите первую букву города:",
        reply_markup=letter_keyboard()
    )
    await state.set_state(CitySelect.waiting_for_letter)

# Обработка выбора буквы
@router.callback_query(F.data.startswith("letter:"))
async def select_letter(callback: CallbackQuery, state: FSMContext):
    letter = callback.data.split(":")[1]
    cursor.execute("SELECT city FROM rates WHERE city LIKE ? ORDER BY city", (f"{letter}%",))
    cities = [row[0] for row in cursor.fetchall()]

    if not cities:
        await callback.message.edit_text(f"❌ Нет городов на букву {letter}")
        return

    await state.update_data(cities=cities, letter=letter, page=0)
    await show_city_page(callback, state)

# Показ списка городов (с пагинацией)
async def show_city_page(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cities = data["cities"]
    page = data.get("page", 0)
    per_page = 8
    start = page * per_page
    end = start + per_page
    total_pages = (len(cities) - 1) // per_page + 1

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=f"city:{city}")]
        for city in cities[start:end]
    ])

    # стрелки
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅", callback_data="page:prev"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡", callback_data="page:next"))
    if nav_row:
        kb.inline_keyboard.append(nav_row)

    # назад
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_letters")])

    await callback.message.edit_text("📍 Выберите город:", reply_markup=kb)


# обработка выбора города из списка
@router.callback_query(F.data.startswith("city:"))
async def city_selected(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":", 1)[1]
    await state.update_data(geo_city=city)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="confirm_city_yes")
    kb.button(text="❌ Нет", callback_data="confirm_city_no")
    kb.adjust(2)

    await callback.message.edit_text(
        f"🏙 Вы выбрали город: <b>{city}</b>\nПодтвердить выбор города?",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "confirm_city_yes")
async def confirm_city_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    city = data.get("geo_city", "")

    from database import cursor, conn
    from routers.courier.income_math import start_income_calc

    cursor.execute("SELECT * FROM rates WHERE city = ?", (city,))
    if cursor.fetchone():
        user_id = callback.from_user.id
        cursor.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))
        conn.commit()

        await callback.message.delete()
        await start_income_calc(callback, state)
    else:
        await callback.message.edit_text(
            f"❌ Город <b>{city}</b> не найден в базе.\nВыберите город вручную:",
            parse_mode="HTML",
            reply_markup=letter_keyboard()
        )


@router.callback_query(F.data == "confirm_city_no")
async def confirm_city_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏙 Выберите первую букву города:",
        reply_markup=letter_keyboard()
    )
    await state.set_state(CitySelect.waiting_for_letter)

# пагинация: вперёд / назад
@router.callback_query(F.data.in_(["page:next", "page:prev"]))
async def change_page(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("page", 0)
    if callback.data == "page:next":
        page += 1
    else:
        page -= 1
    await state.update_data(page=page)
    await show_city_page(callback, state)

# назад к буквам
@router.callback_query(F.data == "back_letters")
async def back_to_letters(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏙 Выберите первую букву города:",
        reply_markup=letter_keyboard()
    )
    await state.set_state(CitySelect.waiting_for_letter)
