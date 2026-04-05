import asyncio
import sys
from pathlib import Path
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


async def _run_sherlock(pseudo: str, message: Message):
    await message.answer(f"🔍 Sherlock : recherche de `{pseudo}`...\n_Patiente 30-90s_")

    cmd = [
        sys.executable, "-m", "sherlock", pseudo,
        "--print-found",
        "--no-color",
        "--timeout", "10",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Sherlock (120s).", reply_markup=back_main())
        return
    except Exception as e:
        await message.answer(f"❌ Erreur lancement : `{e}`", reply_markup=back_main())
        return

    raw_out = stdout.decode(errors="replace").strip()
    raw_err = stderr.decode(errors="replace").strip()

    # Garder uniquement les lignes [+] (trouvé) et les infos utiles
    found_lines = []
    info_lines = []
    for line in raw_out.splitlines():
        l = line.strip()
        if l.startswith("[+]"):
            found_lines.append(l)
        elif l.startswith("[*]") or l.startswith("[>"):
            info_lines.append(l)

    if not found_lines:
        # Envoyer le debug pour diagnostiquer
        debug = raw_err[:1500] or raw_out[:1500] or "Aucune sortie."
        await message.answer(
            f"❌ Aucun résultat pour `{pseudo}`.\n\n"
            f"🔧 *Debug stderr :*\n```\n{debug}\n```",
            reply_markup=back_main()
        )
        return

    # Formater les résultats proprement
    count = len(found_lines)
    lines_clean = []
    for l in found_lines:
        # [+] Platform: https://...
        parts = l.replace("[+] ", "").split(": ", 1)
        if len(parts) == 2:
            lines_clean.append(f"✅ *{parts[0].strip()}* — {parts[1].strip()}")
        else:
            lines_clean.append(l)

    header = f"📋 *Sherlock — `{pseudo}`* — {count} profil(s) trouvé(s)\n"
    full_text = header + "\n".join(lines_clean)

    if len(full_text) > 3800:
        await message.answer_document(
            BufferedInputFile(full_text.encode(), filename=f"sherlock_{pseudo}.txt"),
            caption=f"📄 Sherlock — `{pseudo}` ({count} résultats)",
            reply_markup=back_main()
        )
    else:
        await message.answer(full_text, reply_markup=back_main())


@router.message(OSINTForm.waiting_sherlock)
@admin_only
@rate_limit(seconds=30)
async def state_sherlock(message: Message, state: FSMContext):
    await state.clear()
    await _run_sherlock(message.text.strip(), message)


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
