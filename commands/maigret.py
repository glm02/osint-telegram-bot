import asyncio
import sys
import tempfile
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
_maigret_installed = False


async def _ensure_maigret():
    """Installe maigret sans ses dépendances pour éviter le conflit aiohttp."""
    global _maigret_installed
    if _maigret_installed:
        return True
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install",
            "maigret==0.4.4", "--no-deps", "-q",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        _maigret_installed = True
        return True
    except Exception:
        return False


async def _run_maigret(pseudo: str, message: Message):
    await message.answer(
        f"🕵️ Maigret : analyse de `{pseudo}`...\n"
        "_Patiente 60-120s — rapport complet en cours_"
    )

    ok = await _ensure_maigret()
    if not ok:
        await message.answer("❌ Impossible d'installer maigret.", reply_markup=back_main())
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable, "-m", "maigret", pseudo,
            "--no-color",
            "--print-found",
            "--timeout", "15",
            "--folderoutput", tmpdir,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=150)
        except asyncio.TimeoutError:
            await message.answer("⏱️ Timeout Maigret.", reply_markup=back_main())
            return
        except Exception as e:
            await message.answer(f"❌ Erreur lancement : `{e}`", reply_markup=back_main())
            return

        result = stdout.decode(errors="replace").strip()
        lines = [
            l for l in result.splitlines()
            if not l.startswith("[!") and "Checking" not in l
        ]
        clean = "\n".join(lines).strip()

        html_files = list(Path(tmpdir).glob("*.html"))

        if html_files:
            html_bytes = html_files[0].read_bytes()
            await message.answer_document(
                BufferedInputFile(html_bytes, filename=f"maigret_{pseudo}.html"),
                caption=f"📊 *Maigret — rapport `{pseudo}`*",
            )

        if clean:
            if len(clean) > 3800:
                await message.answer_document(
                    BufferedInputFile(clean.encode(), filename=f"maigret_{pseudo}.txt"),
                    caption=f"📄 Résultats texte `{pseudo}`",
                    reply_markup=back_main()
                )
            else:
                for chunk in chunk_text(f"📋 *Maigret — {pseudo}*\n\n```\n{clean}\n```"):
                    await message.answer(chunk)
                await message.answer("✅ Terminé.", reply_markup=back_main())
        elif not html_files:
            await message.answer(f"❌ Aucun résultat pour `{pseudo}`.", reply_markup=back_main())
        else:
            await message.answer("✅ Rapport envoyé.", reply_markup=back_main())


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
