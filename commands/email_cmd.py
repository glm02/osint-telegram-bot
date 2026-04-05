import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.keyboards import back_main

router = Router()


async def _run_holehe(email: str, message: Message):
    await message.answer(f"📧 Holehe : recherche des comptes liés à `{email}`...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "holehe", email, "--only-used",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        await message.answer("⏱️ Timeout Holehe.", reply_markup=back_main())
        return
    except Exception as e:
        await message.answer(f"❌ Erreur : `{e}`", reply_markup=back_main())
        return

    result = stdout.decode(errors="replace").strip()
    lines  = [l for l in result.splitlines() if "[+]" in l or "[-]" in l]

    if not lines:
        await message.answer(f"🤷 Aucun compte trouvé pour `{email}`.", reply_markup=back_main())
        return

    found     = [l for l in lines if "[+]" in l]
    not_found = [l for l in lines if "[-]" in l]

    resp = f"📧 *Holehe — {email}*\n\n"
    if found:
        resp += f"✅ *Trouvé sur {len(found)} site(s) :*\n"
        resp += "\n".join(f"  • {l.split('[+]')[-1].strip()}" for l in found)
    resp += f"\n\n❌ _Non trouvé sur {len(not_found)} site(s)_"

    await message.answer(resp, reply_markup=back_main())


@router.message(OSINTForm.waiting_email)
@admin_only
@rate_limit(seconds=15)
async def state_email(message: Message, state: FSMContext):
    await state.clear()
    await _run_holehe(message.text.strip(), message)


@router.message(Command("email"))
@admin_only
@rate_limit(seconds=15)
async def cmd_email(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/email <adresse@email.com>`")
        return
    await _run_holehe(parts[1].strip(), message)
