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
from utils.keyboards import back_main

router = Router()


def _find_data_json() -> str | None:
    """Localise data.json installé avec sherlock-project."""
    # Méthode 1 : via le package Python
    try:
        import sherlock_project
        p = Path(sherlock_project.__file__).parent / "resources" / "data.json"
        if p.exists():
            return str(p)
    except Exception:
        pass
    try:
        import sherlock
        p = Path(sherlock.__file__).parent / "resources" / "data.json"
        if p.exists():
            return str(p)
    except Exception:
        pass
    # Méthode 2 : chercher dans site-packages
    for sp in sys.path:
        for sub in ["sherlock_project", "sherlock"]:
            p = Path(sp) / sub / "resources" / "data.json"
            if p.exists():
                return str(p)
    # Méthode 3 : find dans /opt/render
    base = Path("/opt/render")
    if base.exists():
        matches = list(base.rglob("sherlock*"))
        for m in matches:
            candidate = m / "resources" / "data.json"
            if candidate.exists():
                return str(candidate)
    return None


async def _run_sherlock(pseudo: str, message: Message):
    await message.answer(f"🔍 Sherlock : recherche de `{pseudo}`...\n_Patiente 30-90s_")

    data_json = _find_data_json()

    if not data_json:
        await message.answer(
            "❌ `data.json` introuvable.\n"
            "Lance `/debug_sherlock` pour diagnostiquer.",
            reply_markup=back_main()
        )
        return

    cmd = [
        sys.executable, "-m", "sherlock", pseudo,
        "--print-found",
        "--no-color",
        "--timeout", "10",
        "--local",
        "--json", data_json,
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

    found_lines = [l.strip() for l in raw_out.splitlines() if l.strip().startswith("[+]")]

    if not found_lines:
        debug = (raw_err or raw_out or "Aucune sortie.")[:1500]
        await message.answer(
            f"❌ Aucun résultat pour `{pseudo}`.\n\n🔧 *Debug :*\n```\n{debug}\n```",
            reply_markup=back_main()
        )
        return

    count = len(found_lines)
    lines_clean = []
    for l in found_lines:
        parts = l.replace("[+] ", "", 1).split(": ", 1)
        if len(parts) == 2:
            lines_clean.append(f"✅ *{parts[0].strip()}* — {parts[1].strip()}")
        else:
            lines_clean.append(l)

    header = f"📋 *Sherlock — `{pseudo}`* — {count} profil(s)\n\n"
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


@router.message(Command("debug_sherlock"))
@admin_only
async def cmd_debug_sherlock(message: Message):
    """Diagnostique l'installation de sherlock."""
    lines = []
    data_json = _find_data_json()
    lines.append(f"data.json : `{data_json or 'INTROUVABLE'}`")
    lines.append(f"sys.executable : `{sys.executable}`")
    # Tester que sherlock se lance
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "sherlock", "--help",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await asyncio.wait_for(proc.communicate(), timeout=10)
        lines.append(f"sherlock --help : OK ({len(out)} bytes)")
    except Exception as e:
        lines.append(f"sherlock --help : ERREUR `{e}`")
    # Lister les dossiers sherlock trouvés
    for sp in sys.path:
        for sub in ["sherlock_project", "sherlock"]:
            p = Path(sp) / sub
            if p.exists():
                lines.append(f"Trouvé : `{p}`")
    await message.answer("🔧 *Debug Sherlock*\n\n" + "\n".join(lines))
