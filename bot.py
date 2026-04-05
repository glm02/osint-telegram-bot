import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from commands.start import router as start_router
from commands.sherlock import router as sherlock_router
from commands.maigret import router as maigret_router
from commands.email_cmd import router as email_router
from commands.breach import router as breach_router
from commands.phone import router as phone_router
from commands.ip_cmd import router as ip_router
from commands.whois_cmd import router as whois_router
from commands.domain import router as domain_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN manquant dans .env")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(sherlock_router)
    dp.include_router(maigret_router)
    dp.include_router(email_router)
    dp.include_router(breach_router)
    dp.include_router(phone_router)
    dp.include_router(ip_router)
    dp.include_router(whois_router)
    dp.include_router(domain_router)

    logger.info("🕵️ OSINT Bot démarré")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
