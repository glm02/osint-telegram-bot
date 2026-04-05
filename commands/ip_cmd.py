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


async def _run_ip(ip: str, message: Message):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            data = (await client.get(
                f"http://ip-api.com/json/{ip}",
                params={
                    "fields": "status,message,country,countryCode,regionName,"
                              "city,zip,lat,lon,isp,org,as,proxy,hosting,mobile,query"
                },
            )).json()
    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`", reply_markup=back_main())
        return

    if data.get("status") == "fail":
        await message.answer(f"❌ IP invalide ou privée : `{data.get('message')}`", reply_markup=back_main())
        return

    flags = []
    if data.get("proxy"):   flags.append("⚠️ VPN/Proxy détecté")
    if data.get("hosting"): flags.append("🖥️ Datacenter/Hébergeur")
    if data.get("mobile"):  flags.append("📱 Réseau mobile")

    result = (
        f"🌐 *Analyse IP — {data['query']}*\n\n"
        f"🏳️ Pays : `{data['country']}` ({data['countryCode']})\n"
        f"🏙️ Ville : `{data['city']}, {data['regionName']}`\n"
        f"📮 Code postal : `{data.get('zip', 'N/A')}`\n"
        f"📍 Coords : `{data['lat']}, {data['lon']}`\n"
        f"📡 FAI : `{data['isp']}`\n"
        f"🏢 Organisation : `{data['org']}`\n"
        f"🔢 ASN : `{data['as']}`"
    )

    if flags:
        result += "\n\n" + "\n".join(flags)

    result += f"\n\n🗺️ [Voir sur la carte](https://www.openstreetmap.org/?mlat={data['lat']}&mlon={data['lon']}&zoom=12)"

    await message.answer(result, reply_markup=back_main())


@router.message(OSINTForm.waiting_ip)
@admin_only
@rate_limit(seconds=5)
async def state_ip(message: Message, state: FSMContext):
    await state.clear()
    await _run_ip(message.text.strip(), message)


@router.message(Command("ip"))
@admin_only
@rate_limit(seconds=5)
async def cmd_ip(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/ip <adresse IP>`")
        return
    await _run_ip(parts[1].strip(), message)
