import os
from functools import wraps
from aiogram.types import Message


def get_admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


def admin_only(func):
    """
    Décorateur : bloque la commande si l'utilisateur n'est pas admin.
    """
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in get_admin_ids():
            await message.answer("🚫 Accès réservé aux admins.")
            return
        return await func(message, *args, **kwargs)
    return wrapper
