import os
import httpx
import phonenumbers
from phonenumbers import geocoder, carrier, timezone as pn_tz
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.keyboards import back_main

router = Router()
VERIPHONE_KEY = os.getenv("VERIPHONE_API_KEY", "")

TYPE_MAP = {
    phonenumbers.PhoneNumberType.MOBILE:              "📱 Mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE:           "☎️ Fixe",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Fixe/Mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE:            "🆓 Numéro gratuit",
    phonenumbers.PhoneNumberType.PREMIUM_RATE:         "💰 Surtaxé",
    phonenumbers.PhoneNumberType.VOIP:                 "🌐 VoIP",
}


async def _run_phone(numero: str, message: Message):
    try:
        parsed = phonenumbers.parse(numero, None)
    except phonenumbers.NumberParseException as e:
        await message.answer(f"❌ Numéro invalide : `{e}`", reply_markup=back_main())
        return

    valide   = phonenumbers.is_valid_number(parsed)
    pays     = geocoder.description_for_number(parsed, "fr") or "Inconnu"
    oper     = carrier.name_for_number(parsed, "fr") or "Inconnu"
    fuseaux  = list(pn_tz.time_zones_for_number(parsed))
    e164     = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    intl     = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    ptype    = TYPE_MAP.get(phonenumbers.number_type(parsed), "❓ Inconnu")

    result = (
        f"📱 *Analyse — {intl}*\n\n"
        f"{'✅' if valide else '❌'} Valide : `{valide}`\n"
        f"🌍 Pays : `{pays}`\n"
        f"📡 Opérateur : `{oper}`\n"
        f"📋 Type : {ptype}\n"
        f"🕐 Fuseau : `{', '.join(fuseaux) or 'N/A'}`\n"
        f"🔢 E164 : `{e164}`"
    )

    if VERIPHONE_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                vdata = (await client.get(
                    "https://api.veriphone.io/v2/verify",
                    params={"phone": numero, "key": VERIPHONE_KEY},
                )).json()
            if vdata.get("phone_valid"):
                result += (
                    f"\n\n🔎 *Veriphone :*\n"
                    f"  • Ligne : `{vdata.get('line_type', 'N/A')}`\n"
                    f"  • Réseau : `{vdata.get('carrier', 'N/A')}`"
                )
        except Exception:
            pass

    await message.answer(result, reply_markup=back_main())


@router.message(OSINTForm.waiting_phone)
@admin_only
@rate_limit(seconds=10)
async def state_phone(message: Message, state: FSMContext):
    await state.clear()
    await _run_phone(message.text.strip(), message)


@router.message(Command("phone"))
@admin_only
@rate_limit(seconds=10)
async def cmd_phone(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/phone <+33612345678>`")
        return
    await _run_phone(parts[1].strip(), message)
