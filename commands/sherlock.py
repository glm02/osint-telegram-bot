import asyncio
import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from utils.rate_limit import rate_limit
from utils.admin import admin_only
from utils.formatter import chunk_text

router = Router()


@router.message(Command("sherlock"))
@admin_only
@rate_limit(seconds=30)
async def cmd_sherlock(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/sherlock <pseudo>`")
        return

    pseudo = parts[1].strip()
    await message.answer(f"🔍 Recherche de `{pseudo}` sur 300+ réseaux...\n_Peut prendre 30-60s_")

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "python3", "-m", "sherlock", pseudo,
                "--print-found", "--no-color",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=5,
        )
        proc = await asyncio.wait_for(asyncio.shield(asyncio.ensure_future(_run_proc(proc))), timeout=90)
        stdout, stderr = proc
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout — la recherche a pris trop longtemps.")
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`")
        return

    result = stdout.decode(errors="replace").strip()
    if not result:
        await message.answer(f"❌ Aucun résultat pour `{pseudo}`.")
        return

    # Envoi en fichier si trop long
    if len(result) > 4000:
        file = BufferedInputFile(result.encode(), filename=f"sherlock_{pseudo}.txt")
        await message.answer_document(file, caption=f"📄 Résultats Sherlock pour `{pseudo}`")
    else:
        for chunk in chunk_text(f"📋 *Sherlock — {pseudo}*\n\n```\n{result}\n```"):
            await message.answer(chunk)


async def _run_proc(proc):
    stdout, stderr = await proc.communicate()
    return stdout, stderr
