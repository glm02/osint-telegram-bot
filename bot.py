import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from commands.start import router as start_router
from commands.sherlock import router as sherlock_router
from commands.maigret import router as maigret_router
from commands.email_cmd import router as email_router
from commands.breach import router as breach_router
from commands.phone import router as phone_router
from commands.ip_cmd import router as ip_router
from commands.whois_cmd import router as whois_router
from commands.domain import router as domain_router
from commands.callbacks import router as cb_router
from commands.states import router as states_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TOKEN        = os.getenv("TELEGRAM_TOKEN", "")
WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "")   # ex: https://mon-app.onrender.com
WEBHOOK_PATH = "/webhook"
PORT         = int(os.getenv("PORT", 8080))


async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        url = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(url)
        logger.info(f"✅ Webhook défini : {url}")
    else:
        logger.info("ℹ️  Pas de WEBHOOK_URL — mode polling (dev local)")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


def build_dp() -> Dispatcher:
    dp = Dispatcher()
    for r in [cb_router, states_router, start_router, sherlock_router,
              maigret_router, email_router, breach_router, phone_router,
              ip_router, whois_router, domain_router]:
        dp.include_router(r)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    return dp


async def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN manquant dans .env")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp  = build_dp()

    if WEBHOOK_URL:
        # --- Mode webhook (Render / production) ---
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
        await site.start()
        logger.info(f"🚀 Serveur webhook démarré sur le port {PORT}")
        await asyncio.Event().wait()          # tourne indéfiniment
    else:
        # --- Mode polling (dev local) ---
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
