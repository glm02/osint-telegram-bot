import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.rate_limit import rate_limit
from utils.admin import admin_only

router = Router()


@router.message(Command("ip"))
@admin_only
@rate_limit(seconds=5)
async def cmd_ip(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/ip <adresse IP>`")
        return

    ip = parts[1].strip()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # ip-api.com : 45 req/min, gratuit
            data = (await client.get(
                f"http://ip-api.com/json/{ip}",
                params={
                    "fields": "status,message,country,countryCode,regionName,city,"
                              "zip,lat,lon,isp,org,as,proxy,hosting,mobile,query"
                },
            )).json()

            # AbuseIPDB check (sans clé, infos limitées)
            abuse = (await client.get(
                f"https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": 90},
                headers={"Key": "placeholder", "Accept": "application/json"},
            )) if False else None  # Désactivé sans clé

    except Exception as e:
        await message.answer(f"❌ Erreur réseau : `{e}`")
        return

    if data.get("status") == "fail":
        await message.answer(f"❌ IP invalide ou privée : `{data.get('message')}`")
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
        f"📍 Coordonnées : `{data['lat']}, {data['lon']}`\n"
        f"📡 FAI : `{data['isp']}`\n"
        f"🏢 Organisation : `{data['org']}`\n"
        f"🔢 ASN : `{data['as']}`\n"
    )

    if flags:
        result += "\n" + "\n".join(flags)

    result += f"\n\n🗺️ [Voir sur la carte](https://www.openstreetmap.org/?mlat={data['lat']}&mlon={data['lon']}&zoom=12)"

    await message.answer(result)
