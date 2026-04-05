import os
import httpx
import phonenumbers
from phonenumbers import geocoder, carrier, timezone as pn_timezone
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.rate_limit import rate_limit
from utils.admin import admin_only

router = Router()

VERIPHONE_KEY = os.getenv("VERIPHONE_API_KEY", "")


@router.message(Command("phone"))
@admin_only
@rate_limit(seconds=10)
async def cmd_phone(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/phone <+33612345678>`")
        return

    numero = parts[1].strip()

    # --- Analyse locale (phonenumbers, 100% offline) ---
    try:
        parsed = phonenumbers.parse(numero, None)
    except phonenumbers.NumberParseException as e:
        await message.answer(f"❌ Numéro invalide : `{e}`")
        return

    valide = phonenumbers.is_valid_number(parsed)
    pays = geocoder.description_for_number(parsed, "fr") or "Inconnu"
    operateur = carrier.name_for_number(parsed, "fr") or "Inconnu"
    fuseaux = list(pn_timezone.time_zones_for_number(parsed))
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    nt = phonenumbers.number_type(parsed)
    type_map = {
        phonenumbers.PhoneNumberType.MOBILE: "📱 Mobile",
        phonenumbers.PhoneNumberType.FIXED_LINE: "☎️ Fixe",
        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Fixe/Mobile",
        phonenumbers.PhoneNumberType.TOLL_FREE: "🆓 Numéro gratuit",
        phonenumbers.PhoneNumberType.PREMIUM_RATE: "💰 Surtaxé",
        phonenumbers.PhoneNumberType.VOIP: "🌐 VoIP",
    }
    phone_type = type_map.get(nt, "❓ Inconnu")

    result = (
        f"📱 *Analyse — {intl}*\n\n"
        f"{'✅' if valide else '❌'} Valide : `{valide}`\n"
        f"🌍 Pays : `{pays}`\n"
        f"📡 Opérateur : `{operateur}`\n"
        f"📋 Type : {phone_type}\n"
        f"🕐 Fuseau : `{', '.join(fuseaux) if fuseaux else 'N/A'}`\n"
        f"🔢 E164 : `{e164}`\n"
    )

    # --- Enrichissement Veriphone (API) ---
    if VERIPHONE_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                vdata = (await client.get(
                    "https://api.veriphone.io/v2/verify",
                    params={"phone": numero, "key": VERIPHONE_KEY},
                )).json()
            if vdata.get("phone_valid"):
                result += f"\n🔎 *Veriphone enrichi :*\n"
                result += f"  • Ligne active : `{vdata.get('line_type', 'N/A')}`\n"
                result += f"  • Pays ISO : `{vdata.get('country_code', 'N/A')}`\n"
                result += f"  • Réseau : `{vdata.get('carrier', 'N/A')}`"
        except Exception:
            pass

    await message.answer(result)
