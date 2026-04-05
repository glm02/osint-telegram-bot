import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import Message, BufferedInputFile

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.formatter import chunk_text
from utils.keyboards import back_main

router = Router()


async def _run_sherlock(pseudo: str, message: Message):
    await message.answer(f"🔍 Sherlock : recherche de `{pseudo}` en cours...\n_Patiente 30-60s_")
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-m", "sherlock", pseudo,
            "--print-found", "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Sherlock.", reply_markup=back_main())
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`", reply_markup=back_main())
        return

    result = stdout.decode(errors="replace").strip()
    if not result:
        await message.answer(f"❌ Aucun résultat pour `{pseudo}`.", reply_markup=back_main())
        return

    if len(result) > 4000:
        file = BufferedInputFile(result.encode(), filename=f"sherlock_{pseudo}.txt")
        await message.answer_document(file, caption=f"📄 Sherlock — `{pseudo}`", reply_markup=back_main())
    else:
        for chunk in chunk_text(f"📋 *Sherlock — {pseudo}*\n\n```\n{result}\n```"):
            await message.answer(chunk)
        await message.answer("✅ Terminé.", reply_markup=back_main())


# FSM — réponse au bouton
@router.message(OSINTForm.waiting_sherlock)
@admin_only
@rate_limit(seconds=30)
async def state_sherlock(message: Message, state: FSMContext):
    await state.clear()
    await _run_sherlock(message.text.strip(), message)


# Commande directe (toujours disponible)
@router.message(Command("sherlock"))
@admin_only
@rate_limit(seconds=30)
async def cmd_sherlock(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/sherlock <pseudo>`")
        return
    await _run_sherlock(parts[1].strip(), message)
