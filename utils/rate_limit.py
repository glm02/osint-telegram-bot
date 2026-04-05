import time
from functools import wraps
from aiogram.types import Message

# {user_id: {command: last_call_timestamp}}
_rate_cache: dict[int, dict[str, float]] = {}


def rate_limit(seconds: int = 10):
    """
    Décorateur anti-flood par commande et par utilisateur.
    seconds : délai minimum entre deux appels de la même commande.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            user_id = message.from_user.id
            cmd = func.__name__
            now = time.time()

            user_cache = _rate_cache.setdefault(user_id, {})
            last = user_cache.get(cmd, 0)

            if now - last < seconds:
                wait = int(seconds - (now - last))
                await message.answer(
                    f"⏳ Patiente encore *{wait}s* avant de relancer cette commande."
                )
                return

            user_cache[cmd] = now
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator
