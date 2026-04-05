import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.rate_limit import rate_limit
from utils.admin import admin_only

router = Router()


@router.message(Command("email"))
@admin_only
@rate_limit(seconds=15)
async def cmd_email(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/email <adresse@email.com>`")
        return

    email = parts[1].strip()
    await message.answer(f"📧 Recherche des comptes liés à `{email}`...")

    try:
        proc = await asyncio.create_subprocess_exec(
            "holehe", email, "--only-used",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Holehe.")
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`")
        return

    result = stdout.decode(errors="replace").strip()
    lines = [l for l in result.splitlines() if "[+]" in l or "[-]" in l]

    if not lines:
        await message.answer(f"🤷 Aucun compte trouvé pour `{email}`.")
        return

    found = [l for l in lines if "[+]" in l]
    not_found = [l for l in lines if "[-]" in l]

    response = f"📧 *Holehe — {email}*\n\n"
    if found:
        response += f"✅ *Trouvé sur {len(found)} site(s) :*\n"
        response += "\n".join(f"  • {l.split('[+]')[-1].strip()}" for l in found)
    response += f"\n\n❌ _Non trouvé sur {len(not_found)} site(s)_"

    await message.answer(response)
