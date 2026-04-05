import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.formatter import chunk_text
from utils.keyboards import back_main

router = Router()


async def _run_maigret(pseudo: str, message: Message):
    await message.answer(f"🕵️ Maigret : analyse de `{pseudo}`...\n_Patiente 60-120s_")
    try:
        proc = await asyncio.create_subprocess_exec(
            "maigret", pseudo, "--no-color", "--print-found",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Maigret.", reply_markup=back_main())
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`", reply_markup=back_main())
        return

    result = stdout.decode(errors="replace").strip()
    if not result:
        await message.answer(f"❌ Aucun résultat pour `{pseudo}`.", reply_markup=back_main())
        return

    if len(result) > 4000:
        file = BufferedInputFile(result.encode(), filename=f"maigret_{pseudo}.txt")
        await message.answer_document(file, caption=f"📄 Maigret — `{pseudo}`", reply_markup=back_main())
    else:
        for chunk in chunk_text(f"📋 *Maigret — {pseudo}*\n\n```\n{result}\n```"):
            await message.answer(chunk)
        await message.answer("✅ Terminé.", reply_markup=back_main())


@router.message(OSINTForm.waiting_maigret)
@admin_only
@rate_limit(seconds=30)
async def state_maigret(message: Message, state: FSMContext):
    await state.clear()
    await _run_maigret(message.text.strip(), message)


@router.message(Command("maigret"))
@admin_only
@rate_limit(seconds=30)
async def cmd_maigret(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/maigret <pseudo>`")
        return
    await _run_maigret(parts[1].strip(), message)
