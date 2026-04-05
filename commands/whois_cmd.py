import whois
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.rate_limit import rate_limit
from utils.admin import admin_only

router = Router()


@router.message(Command("whois"))
@admin_only
@rate_limit(seconds=10)
async def cmd_whois(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/whois <domaine.com>`")
        return

    domain = parts[1].strip().lower()
    await message.answer(f"🔎 WHOIS pour `{domain}`...")

    try:
        w = whois.whois(domain)
    except Exception as e:
        await message.answer(f"❌ Erreur WHOIS : `{e}`")
        return

    def fmt(val):
        if isinstance(val, list):
            return ", ".join(str(v) for v in val[:3])
        return str(val) if val else "N/A"

    result = (
        f"📋 *WHOIS — {domain}*\n\n"
        f"🏢 Registrant : `{fmt(w.get('name') or w.get('org'))}`\n"
        f"📧 Email : `{fmt(w.get('emails'))}`\n"
        f"🌍 Pays : `{fmt(w.get('country'))}`\n"
        f"🗓️ Créé le : `{fmt(w.get('creation_date'))}`\n"
        f"🔄 Mis à jour : `{fmt(w.get('updated_date'))}`\n"
        f"⏳ Expire le : `{fmt(w.get('expiration_date'))}`\n"
        f"🖥️ Nameservers : `{fmt(w.get('name_servers'))}`\n"
        f"📦 Registrar : `{fmt(w.get('registrar'))}`"
    )

    await message.answer(result)
