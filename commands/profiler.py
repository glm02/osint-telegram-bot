import asyncio
import re
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from commands.states import OSINTForm
from utils.admin import admin_only
from utils.rate_limit import rate_limit
from utils.keyboards import back_main

router = Router()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ── Scrapers par plateforme ───────────────────────────────────────────────────

async def scrape_github(username: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"https://api.github.com/users/{username}", timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {
                "platform": "GitHub",
                "url": d.get("html_url", ""),
                "name": d.get("name") or "",
                "bio": d.get("bio") or "",
                "location": d.get("location") or "",
                "followers": d.get("followers", 0),
                "repos": d.get("public_repos", 0),
                "created": d.get("created_at", "")[:10],
                "avatar": d.get("avatar_url", ""),
                "company": d.get("company") or "",
                "email": d.get("email") or "",
                "twitter": d.get("twitter_username") or "",
            }
    except Exception:
        pass
    return {}


async def scrape_reddit(username: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(
            f"https://www.reddit.com/user/{username}/about.json",
            timeout=8, headers={**HEADERS, "Accept": "application/json"}
        )
        if r.status_code == 200:
            d = r.json().get("data", {})
            karma = d.get("link_karma", 0) + d.get("comment_karma", 0)
            import datetime
            created = datetime.datetime.utcfromtimestamp(d.get("created_utc", 0)).strftime("%Y-%m-%d")
            return {
                "platform": "Reddit",
                "url": f"https://reddit.com/u/{username}",
                "name": d.get("subreddit", {}).get("title") or "",
                "bio": d.get("subreddit", {}).get("public_description") or "",
                "karma": karma,
                "created": created,
                "verified": d.get("verified", False),
                "avatar": d.get("icon_img", "").split("?")[0],
            }
    except Exception:
        pass
    return {}


async def scrape_twitter(username: str, client: httpx.AsyncClient) -> dict:
    """Vérification d'existence uniquement (pas d'API publique)."""
    try:
        r = await client.get(f"https://twitter.com/{username}", timeout=8, headers=HEADERS)
        if r.status_code == 200 and "This account doesn" not in r.text:
            return {
                "platform": "Twitter/X",
                "url": f"https://twitter.com/{username}",
            }
    except Exception:
        pass
    return {}


async def scrape_instagram(username: str, client: httpx.AsyncClient) -> dict:
    """Vérification d'existence via page publique."""
    try:
        r = await client.get(
            f"https://www.instagram.com/{username}/",
            timeout=8, headers=HEADERS, follow_redirects=True
        )
        if r.status_code == 200 and '"username":' in r.text:
            # Extraire quelques infos basiques
            bio_match = re.search(r'"biography":"([^"]*?)"', r.text)
            name_match = re.search(r'"full_name":"([^"]*?)"', r.text)
            followers_match = re.search(r'"edge_followed_by":\{"count":(\d+)\}', r.text)
            return {
                "platform": "Instagram",
                "url": f"https://instagram.com/{username}",
                "name": name_match.group(1) if name_match else "",
                "bio": bio_match.group(1) if bio_match else "",
                "followers": int(followers_match.group(1)) if followers_match else None,
            }
        elif r.status_code == 200:
            return {"platform": "Instagram", "url": f"https://instagram.com/{username}"}
    except Exception:
        pass
    return {}


async def scrape_tiktok(username: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(
            f"https://www.tiktok.com/@{username}",
            timeout=8, headers=HEADERS, follow_redirects=True
        )
        if r.status_code == 200 and username.lower() in r.text.lower():
            return {"platform": "TikTok", "url": f"https://tiktok.com/@{username}"}
    except Exception:
        pass
    return {}


async def scrape_twitch(username: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(
            f"https://www.twitch.tv/{username}",
            timeout=8, headers=HEADERS
        )
        if r.status_code == 200 and '"login":' in r.text:
            return {"platform": "Twitch", "url": f"https://twitch.tv/{username}"}
    except Exception:
        pass
    return {}


async def scrape_steam(username: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(
            f"https://steamcommunity.com/id/{username}/",
            timeout=8, headers=HEADERS
        )
        if r.status_code == 200 and "profile_header" in r.text:
            name_m = re.search(r'<span class="actual_persona_name">([^<]+)</span>', r.text)
            return {
                "platform": "Steam",
                "url": f"https://steamcommunity.com/id/{username}/",
                "name": name_m.group(1) if name_m else "",
            }
    except Exception:
        pass
    return {}


# ── Sherlock runner ───────────────────────────────────────────────────────────

async def _run_sherlock_urls(pseudo: str) -> list[str]:
    """Lance Sherlock et retourne la liste des URLs trouvées."""
    import sys
    from pathlib import Path

    # Trouver data.json local
    extra = []
    try:
        import sherlock as _sh
        dj = Path(_sh.__file__).parent / "resources" / "data.json"
        if dj.exists():
            extra = ["--local", "--json", str(dj)]
    except Exception:
        pass

    cmd = [sys.executable, "-m", "sherlock", pseudo,
           "--print-found", "--no-color", "--timeout", "10"] + extra
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
    except Exception:
        return []

    urls = []
    for line in stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("[+]"):
            # Format: [+] Platform: https://...
            parts = line.split(": ", 1)
            if len(parts) == 2 and parts[1].startswith("http"):
                urls.append(parts[1].strip())
    return urls


# ── Formateur de résultat ─────────────────────────────────────────────────────

def _format_profile(p: dict) -> str:
    lines = [f"\n🌐 *{p['platform']}* — {p.get('url', '')}"]
    if p.get("name"):      lines.append(f"  👤 Nom : `{p['name']}`")
    if p.get("bio"):       lines.append(f"  📝 Bio : _{p['bio'][:120]}_")
    if p.get("location"): lines.append(f"  📍 Lieu : `{p['location']}`")
    if p.get("email"):     lines.append(f"  📧 Email : `{p['email']}`")
    if p.get("company"):   lines.append(f"  🏢 Société : `{p['company']}`")
    if p.get("twitter"):   lines.append(f"  🐦 Twitter : `@{p['twitter']}`")
    if p.get("followers") is not None:
        lines.append(f"  👥 Followers : `{p['followers']:,}`")
    if p.get("karma"):     lines.append(f"  ⭐ Karma : `{p['karma']:,}`")
    if p.get("repos"):     lines.append(f"  💻 Repos : `{p['repos']}`")
    if p.get("created"):   lines.append(f"  📅 Créé le : `{p['created']}`")
    return "\n".join(lines)


# ── Handler principal ─────────────────────────────────────────────────────────

async def _run_profiler(pseudo: str, message: Message):
    await message.answer(
        f"🕵️ *Profiling de `{pseudo}`...*\n"
        "_Étape 1/2 — Sherlock scan (300+ sites)..._"
    )

    # Étape 1 : Sherlock
    urls = await _run_sherlock_urls(pseudo)
    found_count = len(urls)

    await message.answer(
        f"✅ Sherlock : *{found_count} profil(s) trouvé(s)*\n"
        "_Étape 2/2 — Enrichissement des profils..._"
    )

    # Étape 2 : Scraping enrichi en parallèle
    enriched = []
    simple_urls = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        tasks = {
            "github":    scrape_github(pseudo, client),
            "reddit":    scrape_reddit(pseudo, client),
            "instagram": scrape_instagram(pseudo, client),
            "twitter":   scrape_twitter(pseudo, client),
            "tiktok":    scrape_tiktok(pseudo, client),
            "twitch":    scrape_twitch(pseudo, client),
            "steam":     scrape_steam(pseudo, client),
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for res in results:
        if isinstance(res, dict) and res.get("platform"):
            enriched.append(res)

    # URLs Sherlock non enrichies
    enriched_platforms = {e["platform"].lower() for e in enriched}
    for url in urls:
        skip = any(p in url.lower() for p in enriched_platforms)
        if not skip:
            simple_urls.append(url)

    # Construction du message
    header = (
        f"🕵️ *Rapport OSINT — `{pseudo}`*\n"
        f"📊 {found_count} site(s) Sherlock | "
        f"{len(enriched)} profil(s) enrichi(s)\n"
        f"{'='*30}"
    )

    sections = [header]

    if enriched:
        sections.append("\n🔍 *Profils enrichis :*")
        for p in enriched:
            sections.append(_format_profile(p))

    if simple_urls:
        sections.append(f"\n🔗 *Autres profils trouvés ({len(simple_urls)}) :*")
        # Grouper par 10
        for i in range(0, min(len(simple_urls), 50), 10):
            batch = simple_urls[i:i+10]
            sections.append("\n".join(f"  • {u}" for u in batch))

    full = "\n".join(sections)

    if len(full) > 3800:
        await message.answer_document(
            BufferedInputFile(full.encode(), filename=f"profil_{pseudo}.txt"),
            caption=f"📄 Rapport complet pour `{pseudo}`",
            reply_markup=back_main()
        )
    else:
        await message.answer(full, reply_markup=back_main())


@router.message(OSINTForm.waiting_maigret)
@admin_only
@rate_limit(seconds=30)
async def state_profiler(message: Message, state: FSMContext):
    await state.clear()
    await _run_profiler(message.text.strip(), message)


@router.message(Command("profil", "maigret"))
@admin_only
@rate_limit(seconds=30)
async def cmd_profiler(message: Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Usage : `/profil <pseudo>`")
        return
    await _run_profiler(parts[1].strip(), message)
