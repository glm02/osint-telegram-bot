import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from utils.rate_limit import rate_limit
from utils.admin import admin_only
from utils.formatter import chunk_text

router = Router()


@router.message(Command("domain"))
@admin_only
@rate_limit(seconds=20)
async def cmd_domain(message: Message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/domain <domaine.com>`")
        return

    domain = parts[1].strip().lower()
    await message.answer(
        f"🌐 Reconnaissance de `{domain}`...\n"
        f"_Sous-domaines, emails, IPs — patiente 30-60s_"
    )

    results = {}

    # --- theHarvester ---
    try:
        proc = await asyncio.create_subprocess_exec(
            "theHarvester",
            "-d", domain,
            "-b", "google,bing,duckduckgo,certspotter",
            "-l", "100",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
        results["harvester"] = stdout.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        results["harvester"] = "Timeout"
    except FileNotFoundError:
        results["harvester"] = "theHarvester non installé (pip install theHarvester)"
    except Exception as e:
        results["harvester"] = str(e)

    # --- DNS basique via dig/nslookup ---
    try:
        proc_dns = await asyncio.create_subprocess_exec(
            "nslookup", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_dns, _ = await asyncio.wait_for(proc_dns.communicate(), timeout=10)
        results["dns"] = stdout_dns.decode(errors="replace").strip()
    except Exception:
        results["dns"] = "N/A"

    # --- Assemblage du rapport ---
    report = f"🌐 *Recon DNS — {domain}*\n\n"
    report += f"📡 *DNS Lookup :*\n```\n{results['dns'][:500]}\n```\n\n"
    report += f"🔍 *theHarvester :*\n```\n{results['harvester'][:2000]}\n```"

    if len(report) > 4000:
        file = BufferedInputFile(report.encode(), filename=f"domain_{domain}.txt")
        await message.answer_document(file, caption=f"📄 Rapport domain recon `{domain}`")
    else:
        for chunk in chunk_text(report):
            await message.answer(chunk)
