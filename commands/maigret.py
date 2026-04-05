import asyncio
import os
import tempfile
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile, FSInputFile

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.formatter import chunk_text
from utils.keyboards import back_main

router = Router()


async def _run_maigret(pseudo: str, message: Message):
    await message.answer(
        f"🕵️ Maigret : analyse de `{pseudo}`...\n"
        "_Patiente 60-120s — rapport complet en cours_"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "python3", "-m", "maigret", pseudo,
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

        # Filtrer les lignes parasites
        lines = [
            l for l in result.splitlines()
            if not l.startswith("[!") and "Checking" not in l
            and "Nothing found" not in l
        ]
        clean = "\n".join(lines).strip()

        # Chercher le rapport HTML généré
        html_files = list(Path(tmpdir).glob("*.html"))
        pdf_files  = list(Path(tmpdir).glob("*.pdf"))

        # Envoyer le rapport HTML si dispo
        if html_files:
            html_path = html_files[0]
            html_bytes = html_path.read_bytes()
            await message.answer_document(
                BufferedInputFile(html_bytes, filename=f"maigret_{pseudo}.html"),
                caption=f"📊 *Maigret — rapport complet `{pseudo}`*",
            )

        # Envoyer aussi le texte résumé
        if clean:
            if len(clean) > 3800:
                await message.answer_document(
                    BufferedInputFile(clean.encode(), filename=f"maigret_{pseudo}.txt"),
                    caption=f"📄 Maigret — résultats texte `{pseudo}`",
                    reply_markup=back_main()
                )
            else:
                for chunk in chunk_text(
                    f"📋 *Maigret — {pseudo}*\n\n```\n{clean}\n```"
                ):
                    await message.answer(chunk)
                await message.answer("✅ Terminé.", reply_markup=back_main())
        elif not html_files:
            await message.answer(
                f"❌ Aucun résultat pour `{pseudo}`.",
                reply_markup=back_main()
            )
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
