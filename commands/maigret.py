import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from utils.rate_limit import rate_limit
from utils.admin import admin_only
from utils.formatter import chunk_text

router = Router()


@router.message(Command("maigret"))
@admin_only
@rate_limit(seconds=30)
async def cmd_maigret(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/maigret <pseudo>`")
        return

    pseudo = parts[1].strip()
    await message.answer(f"🔎 Maigret analyse `{pseudo}`...\n_Recherche approfondie, patiente 60-120s_")

    try:
        proc = await asyncio.create_subprocess_exec(
            "maigret", pseudo,
            "--no-color", "--print-found",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Maigret.")
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`")
        return

    result = stdout.decode(errors="replace").strip()
    if not result:
        await message.answer(f"❌ Aucun résultat pour `{pseudo}`.")
        return

    if len(result) > 4000:
        file = BufferedInputFile(result.encode(), filename=f"maigret_{pseudo}.txt")
        await message.answer_document(file, caption=f"📄 Résultats Maigret pour `{pseudo}`")
    else:
        for chunk in chunk_text(f"📋 *Maigret — {pseudo}*\n\n```\n{result}\n```"):
            await message.answer(chunk)
