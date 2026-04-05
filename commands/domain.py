import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.formatter import chunk_text
from utils.keyboards import back_main

router = Router()


async def _run_domain(domain: str, message: Message):
    await message.answer(
        f"🌐 Reconnaissance de `{domain}`...\n"
        f"_Sous-domaines, emails, IPs — patiente 30-60s_"
    )

    results = {}

    try:
        proc = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", domain,
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

    report = (
        f"🌐 *Recon DNS — {domain}*\n\n"
        f"📡 *DNS Lookup :*\n```\n{results['dns'][:500]}\n```\n\n"
        f"🔍 *theHarvester :*\n```\n{results['harvester'][:2000]}\n```"
    )

    if len(report) > 4000:
        file = BufferedInputFile(report.encode(), filename=f"domain_{domain}.txt")
        await message.answer_document(file, caption=f"📄 Recon `{domain}`", reply_markup=back_main())
    else:
        for chunk in chunk_text(report):
            await message.answer(chunk)
        await message.answer("✅ Terminé.", reply_markup=back_main())


@router.message(OSINTForm.waiting_domain)
@admin_only
@rate_limit(seconds=20)
async def state_domain(message: Message, state: FSMContext):
    await state.clear()
    await _run_domain(message.text.strip(), message)


@router.message(Command("domain"))
@admin_only
@rate_limit(seconds=20)
async def cmd_domain(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/domain <domaine.com>`")
        return
    await _run_domain(parts[1].strip(), message)
