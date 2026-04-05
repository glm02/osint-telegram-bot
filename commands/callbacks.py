from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.keyboards import (
    main_menu, pseudo_menu, email_menu,
    phone_menu, network_menu, leaks_menu
)
from commands.states import OSINTForm

router = Router()

# ── Menus de navigation ──────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_main")
async def cb_menu_main(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.edit_text(
        "🕵️ *OSINT Bot* — Choisis une catégorie :",
        reply_markup=main_menu()
    )
    await cq.answer()


@router.callback_query(F.data == "menu_pseudo")
async def cb_menu_pseudo(cq: CallbackQuery):
    await cq.message.edit_text(
        "👤 *Recherche par pseudo* — Choisir l'outil :",
        reply_markup=pseudo_menu()
    )
    await cq.answer()


@router.callback_query(F.data == "menu_email")
async def cb_menu_email(cq: CallbackQuery):
    await cq.message.edit_text(
        "📧 *Recherche par email* — Choisir l'action :",
        reply_markup=email_menu()
    )
    await cq.answer()


@router.callback_query(F.data == "menu_phone")
async def cb_menu_phone(cq: CallbackQuery):
    await cq.message.edit_text(
        "📱 *Analyse téléphone* :",
        reply_markup=phone_menu()
    )
    await cq.answer()


@router.callback_query(F.data == "menu_network")
async def cb_menu_network(cq: CallbackQuery):
    await cq.message.edit_text(
        "🌐 *Réseau & Domaines* — Choisir l'outil :",
        reply_markup=network_menu()
    )
    await cq.answer()


@router.callback_query(F.data == "menu_leaks")
async def cb_menu_leaks(cq: CallbackQuery):
    await cq.message.edit_text(
        "🔓 *Fuites de données* — Choisir l'action :",
        reply_markup=leaks_menu()
    )
    await cq.answer()


# ── Demandes de saisie (FSM) ─────────────────────────────────────────────────

ASK_MAP = {
    "ask_sherlock": (OSINTForm.waiting_sherlock,  "🔍 Entre le *pseudo* à rechercher :"),
    "ask_maigret":  (OSINTForm.waiting_maigret,   "🕵️ Entre le *pseudo* pour Maigret :"),
    "ask_email":    (OSINTForm.waiting_email,     "📧 Entre l'*adresse email* :"),
    "ask_breach":   (OSINTForm.waiting_breach,    "🔓 Entre l'*email* à vérifier dans les leaks :"),
    "ask_pwned":    (OSINTForm.waiting_pwned,     "🔑 Entre le *mot de passe* à vérifier :\n_⚠️ Message supprimé immédiatement._"),
    "ask_phone":    (OSINTForm.waiting_phone,     "📱 Entre le *numéro* au format international :\n_Ex: +33612345678_"),
    "ask_ip":       (OSINTForm.waiting_ip,        "🌍 Entre l'*adresse IP* :"),
    "ask_whois":    (OSINTForm.waiting_whois,     "📋 Entre le *domaine* pour WHOIS :\n_Ex: google.com_"),
    "ask_domain":   (OSINTForm.waiting_domain,    "🔎 Entre le *domaine* à analyser :\n_Ex: target.com_"),
}


@router.callback_query(F.data.in_(ASK_MAP.keys()))
async def cb_ask_input(cq: CallbackQuery, state: FSMContext):
    fsm_state, prompt = ASK_MAP[cq.data]
    await state.set_state(fsm_state)
    await cq.message.edit_text(f"{prompt}\n\n_Ou /annuler pour revenir au menu._")
    await cq.answer()
