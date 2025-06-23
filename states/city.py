from aiogram.fsm.state import StatesGroup, State

class CitySelect(StatesGroup):
    waiting_for_letter = State()
    showing_cities = State()
