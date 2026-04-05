import asyncio
import sys
import os
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

def _find_data_json() -> str | None:
    """Cherche le fichier data.json installé avec sherlock-project."""
    candidates = []
    for p in sys.path:
        candidate = Path(p) / "sherlock" / "resources" / "data.json"
        if candidate.exists():
            candidates.append(str(candidate))
    # Aussi via le package installé
    try:
        import sherlock
        pkg_path = Path(sherlock.__file__).parent / "resources" / "data.json"
        if pkg_path.exists():
            candidates.insert(0, str(pkg_path))
    except Exception:
        pass
    return candidates[0] if candidates else None


async def _run_sherlock(pseudo: str, message: Message):
    await message.answer(f"🔍 Sherlock : recherche de `{pseudo}` en cours...\n_Patiente 30-60s_")

    data_json = _find_data_json()
    cmd = [
        "python3", "-m", "sherlock", pseudo,
        "--print-found", "--no-color",
        "--timeout", "10",
    ]
    if data_json:
        cmd += ["--local", "--json", data_json]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Sherlock.", reply_markup=back_main())
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`", reply_markup=back_main())
        return

    result = stdout.decode(errors="replace").strip()
    # Filtrer les lignes d'erreur résiduelles
    lines = [l for l in result.splitlines() if not l.startswith("ERROR") and not l.startswith("A problem")]
    result = "\n".join(lines).strip()

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


# Commande directe
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
