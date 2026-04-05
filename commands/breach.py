import os
import hashlib
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.keyboards import back_main

router = Router()
HIBP_KEY = os.getenv("HIBP_API_KEY", "")


async def _check_hibp(email: str, message: Message):
    await message.answer(f"🔓 Vérification des fuites pour `{email}`...")
    if not HIBP_KEY:
        await message.answer("❌ `HIBP_API_KEY` non configurée dans `.env`.", reply_markup=back_main())
        return

    headers = {"hibp-api-key": HIBP_KEY, "user-agent": "OSINTBot"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers,
                params={"truncateResponse": False},
            )
    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`", reply_markup=back_main())
        return

    if resp.status_code == 404:
        await message.answer(f"✅ *Aucune fuite détectée* pour `{email}` 🎉", reply_markup=back_main())
        return
    if resp.status_code == 401:
        await message.answer("❌ Clé HIBP invalide ou expirée.", reply_markup=back_main())
        return

    breaches = resp.json()
    total = len(breaches)
    lines = [f"⚠️ *{total} fuite(s) détectée(s)* pour `{email}`\n"]
    for b in breaches[:15]:
        dc = ", ".join(b.get("DataClasses", [])[:4])
        lines.append(
            f"• 📅 `{b['BreachDate']}` — *{b['Name']}*\n"
            f"  👥 {b['PwnCount']:,} comptes | 📋 {dc}"
        )
    if total > 15:
        lines.append(f"\n_... et {total - 15} autre(s) fuite(s)._")

    await message.answer("\n".join(lines), reply_markup=back_main())


async def _check_pwned(password: str, message: Message):
    sha1   = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"Add-Padding": "true"},
            )
    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`", reply_markup=back_main())
        return

    for line in resp.text.splitlines():
        h, count = line.split(":")
        if h.strip() == suffix:
            await message.answer(
                f"🚨 *Mot de passe compromis !*\n"
                f"Trouvé *{int(count):,} fois* dans des fuites.\n"
                f"_Changez-le immédiatement._",
                reply_markup=back_main()
            )
            return
    await message.answer("✅ *Mot de passe non compromis* dans les bases connues.", reply_markup=back_main())


# ── FSM states ───────────────────────────────────────────────────────────────

@router.message(OSINTForm.waiting_breach)
@admin_only
@rate_limit(seconds=10)
async def state_breach(message: Message, state: FSMContext):
    await state.clear()
    await _check_hibp(message.text.strip(), message)


@router.message(OSINTForm.waiting_pwned)
@admin_only
@rate_limit(seconds=5)
async def state_pwned(message: Message, state: FSMContext):
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    await _check_pwned(message.text.strip(), message)


# ── Commandes directes ───────────────────────────────────────────────────────

@router.message(Command("breach"))
@admin_only
@rate_limit(seconds=10)
async def cmd_breach(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/breach <email>`")
        return
    await _check_hibp(parts[1].strip(), message)


@router.message(Command("pwned"))
@admin_only
@rate_limit(seconds=5)
async def cmd_pwned(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/pwned <password>`")
        return
    try:
        await message.delete()
    except Exception:
        pass
    await _check_pwned(parts[1].strip(), message)
