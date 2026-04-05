import os
import hashlib
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.rate_limit import rate_limit
from utils.admin import admin_only

router = Router()

HIBP_KEY = os.getenv("HIBP_API_KEY", "")


@router.message(Command("breach"))
@admin_only
@rate_limit(seconds=10)
async def cmd_breach(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/breach <email>`")
        return

    email = parts[1].strip()
    await message.answer(f"🔓 Vérification des fuites pour `{email}`...")

    if not HIBP_KEY:
        await message.answer("❌ `HIBP_API_KEY` non configurée dans `.env`.")
        return

    headers = {"hibp-api-key": HIBP_KEY, "user-agent": "OSINTBot"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers,
                params={"truncateResponse": False},
            )
    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`")
        return

    if resp.status_code == 404:
        await message.answer(f"✅ *Aucune fuite détectée* pour `{email}` 🎉")
        return

    if resp.status_code == 401:
        await message.answer("❌ Clé HIBP invalide ou expirée.")
        return

    breaches = resp.json()
    total = len(breaches)
    lines = [f"⚠️ *{total} fuite(s) détectée(s)* pour `{email}`\n"]

    for b in breaches[:15]:
        data_classes = ", ".join(b.get("DataClasses", [])[:4])
        lines.append(
            f"• 📅 `{b['BreachDate']}` — *{b['Name']}*\n"
            f"  👥 {b['PwnCount']:,} comptes | 📋 {data_classes}"
        )

    if total > 15:
        lines.append(f"\n_... et {total - 15} autre(s) fuite(s)._")

    await message.answer("\n".join(lines))


@router.message(Command("pwned"))
@admin_only
@rate_limit(seconds=5)
async def cmd_pwned(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/pwned <motdepasse>`")
        return

    # Supprime le message contenant le mot de passe
    try:
        await message.delete()
    except Exception:
        pass

    password = parts[1].strip()
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"Add-Padding": "true"},
            )
    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`")
        return

    for line in resp.text.splitlines():
        h, count = line.split(":")
        if h.strip() == suffix:
            await message.answer(
                f"🚨 *Mot de passe compromis !*\n"
                f"Trouvé *{int(count):,} fois* dans des bases de données de fuites.\n"
                f"_Changez-le immédiatement._"
            )
            return

    await message.answer("✅ *Mot de passe non compromis* dans les bases connues.")
