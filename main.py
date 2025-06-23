# main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN_COURIER, BOT_TOKEN_RECRUITER
from routers.courier.start import router as courier_router
from routers.recruiter.start import router as recruiter_router

from routers.courier.reffer import router as reffer_router
from routers.courier.menu import router as menu_router
from routers.courier.income import router as income_router
from routers.courier import income_math

logging.basicConfig(level=logging.INFO)

bot_courier = Bot(token=BOT_TOKEN_COURIER)
bot_recruiter = Bot(token=BOT_TOKEN_RECRUITER)

dp_courier = Dispatcher()
dp_recruiter = Dispatcher()

dp_courier.include_router(courier_router)
dp_recruiter.include_router(recruiter_router)

dp_courier.include_router(reffer_router)
dp_courier.include_router(menu_router)
dp_courier.include_router(income_router)
dp_courier.include_router(income_math.router)

async def main():
    await asyncio.gather(
        dp_courier.start_polling(bot_courier),
        dp_recruiter.start_polling(bot_recruiter),
    )

if __name__ == "__main__":
    asyncio.run(main())
