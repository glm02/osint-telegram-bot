from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start", "help"))
async def cmd_start(message: Message):
    text = (
        "🕵️ *OSINT Bot* — Reconnaissance open source\n\n"
        "*👤 Identité / Pseudo*\n"
        "`/sherlock <pseudo>` — 300+ réseaux sociaux\n"
        "`/maigret <pseudo>` — Profil enrichi multi-sources\n\n"
        "*📧 Email*\n"
        "`/email <email>` — Comptes associés (Holehe)\n"
        "`/breach <email>` — Fuites de données (HIBP)\n\n"
        "*🔐 Sécurité*\n"
        "`/pwned <password>` — Mot de passe compromis ?\n\n"
        "*📱 Téléphone*\n"
        "`/phone <+33...>` — Pays, opérateur, type\n\n"
        "*🌐 Réseau / Domaine*\n"
        "`/ip <adresse>` — Géoloc + ASN + VPN detect\n"
        "`/whois <domaine>` — Infos WHOIS\n"
        "`/domain <domaine>` — Recon DNS (sous-domaines, emails)\n\n"
        "⚠️ _Usage légal uniquement._"
    )
    await message.answer(text)
