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

HIBP_KEY          = os.getenv("HIBP_API_KEY", "")
RAPIDAPI_KEY      = os.getenv("RAPIDAPI_KEY", "")
LEAKCHECK_KEY     = os.getenv("LEAKCHECK_API_KEY", "")


# ── BreachDirectory (RapidAPI) ───────────────────────────────────────────────

async def _check_breachdirectory(query: str) -> str:
    """Recherche email/pseudo/password dans BreachDirectory via RapidAPI."""
    if not RAPIDAPI_KEY:
        return "\u274c `RAPIDAPI_KEY` non configur\u00e9e."
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://breachdirectory.p.rapidapi.com/",
                params={"func": "auto", "term": query},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "breachdirectory.p.rapidapi.com",
                },
            )
        if resp.status_code == 403:
            return "\u274c Cl\u00e9 RapidAPI invalide ou quota d\u00e9pass\u00e9."
        data = resp.json()
        if not data.get("found") or not data.get("result"):
            return "\u2705 Aucune fuite dans BreachDirectory."

        results = data["result"][:20]
        lines = [f"\U0001f4cb *BreachDirectory* \u2014 {data.get('found', 0)} entr\u00e9e(s)\n"]
        for r in results:
            src    = r.get("sources", ["?"])
            pwd    = r.get("password", "")
            sha1   = r.get("sha1", "")
            line = f"\u2022 Source: `{'`, `'.join(src[:3])}`"
            if pwd:
                line += f" | MDP: `{pwd}`"
            elif sha1:
                line += f" | SHA1: `{sha1[:20]}...`"
            lines.append(line)
        if data.get("found", 0) > 20:
            lines.append(f"_... et {data['found'] - 20} autre(s)._")
        return "\n".join(lines)
    except Exception as e:
        return f"\u274c BreachDirectory erreur: `{e}`"


# ── LeakCheck.io ─────────────────────────────────────────────────────────────

async def _check_leakcheck(query: str) -> str:
    """Recherche email/pseudo dans LeakCheck.io."""
    if not LEAKCHECK_KEY:
        return "\u274c `LEAKCHECK_API_KEY` non configur\u00e9e."
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://leakcheck.io/api/v2/query",
                params={"query": query},
                headers={"X-API-Key": LEAKCHECK_KEY},
            )
        if resp.status_code == 401:
            return "\u274c Cl\u00e9 LeakCheck invalide."
        if resp.status_code == 429:
            return "\u23f3 LeakCheck: quota journalier atteint."
        data = resp.json()
        if not data.get("success") or not data.get("result"):
            return "\u2705 Aucune fuite dans LeakCheck."

        results = data["result"][:20]
        found   = data.get("found", len(results))
        lines   = [f"\U0001f6e1\ufe0f *LeakCheck.io* \u2014 {found} source(s)\n"]
        for r in results:
            src    = r.get("sources", [{}])
            src_names = ", ".join(s.get("name", "?") for s in src[:3])
            pwd    = r.get("password", "")
            line   = f"\u2022 `{src_names}`"
            if pwd:
                line += f" | MDP: `{pwd}`"
            lines.append(line)
        if found > 20:
            lines.append(f"_... et {found - 20} autre(s)._")
        return "\n".join(lines)
    except Exception as e:
        return f"\u274c LeakCheck erreur: `{e}`"


# ── HIBP ─────────────────────────────────────────────────────────────────────

async def _check_hibp(email: str) -> str:
    if not HIBP_KEY:
        return ""  # Pas configur\u00e9, on skippe silencieusement
    headers = {"hibp-api-key": HIBP_KEY, "user-agent": "OSINTBot"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers,
                params={"truncateResponse": False},
            )
    except Exception as e:
        return f"\u274c HIBP erreur: `{e}`"

    if resp.status_code == 404:
        return "\u2705 Aucune fuite HIBP."
    if resp.status_code == 401:
        return "\u274c Cl\u00e9 HIBP invalide."

    breaches = resp.json()
    total    = len(breaches)
    lines    = [f"\u26a0\ufe0f *HaveIBeenPwned* \u2014 {total} fuite(s)\n"]
    for b in breaches[:10]:
        dc = ", ".join(b.get("DataClasses", [])[:3])
        lines.append(f"\u2022 `{b['BreachDate']}` \u2014 *{b['Name']}* | {dc}")
    if total > 10:
        lines.append(f"_... et {total - 10} autre(s)._")
    return "\n".join(lines)


# ── Recherche combin\u00e9e ──────────────────────────────────────────────────────

async def _full_leak_search(query: str, message: Message):
    await message.answer(f"\U0001f50d Recherche de fuites pour `{query}`...\n_Interrogation de 3 bases en parall\u00e8le..._")

    import asyncio
    bd_task  = asyncio.create_task(_check_breachdirectory(query))
    lc_task  = asyncio.create_task(_check_leakcheck(query))
    hibp_task = asyncio.create_task(_check_hibp(query))

    bd_result, lc_result, hibp_result = await asyncio.gather(bd_task, lc_task, hibp_task)

    sections = []
    if bd_result:   sections.append(bd_result)
    if lc_result:   sections.append(lc_result)
    if hibp_result: sections.append(hibp_result)

    full = "\n\n".join(sections)
    if not full.strip():
        await message.answer(f"\u2705 Aucune fuite trouv\u00e9e pour `{query}`.", reply_markup=back_main())
        return

    if len(full) > 3800:
        from aiogram.types import BufferedInputFile
        await message.answer_document(
            BufferedInputFile(full.encode(), filename=f"leaks_{query}.txt"),
            caption=f"\U0001f4c4 R\u00e9sultats complets pour `{query}`",
            reply_markup=back_main()
        )
    else:
        await message.answer(full, reply_markup=back_main())


# ── Mot de passe (HIBP Pwned Passwords) ──────────────────────────────────────

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
        await message.answer(f"\u274c Erreur r\u00e9seau : `{e}`", reply_markup=back_main())
        return

    for line in resp.text.splitlines():
        h, count = line.split(":")
        if h.strip() == suffix:
            await message.answer(
                f"\U0001f6a8 *Mot de passe compromis !*\n"
                f"Trouv\u00e9 *{int(count):,} fois* dans des fuites.\n"
                f"_Changez-le imm\u00e9diatement._",
                reply_markup=back_main()
            )
            return
    await message.answer("\u2705 *Mot de passe non compromis* dans les bases connues.", reply_markup=back_main())


# ── FSM states ────────────────────────────────────────────────────────────────

@router.message(OSINTForm.waiting_breach)
@admin_only
@rate_limit(seconds=10)
async def state_breach(message: Message, state: FSMContext):
    await state.clear()
    await _full_leak_search(message.text.strip(), message)


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


# ── Commandes directes ────────────────────────────────────────────────────────

@router.message(Command("breach"))
@admin_only
@rate_limit(seconds=10)
async def cmd_breach(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/breach <email ou pseudo>`")
        return
    await _full_leak_search(parts[1].strip(), message)


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
