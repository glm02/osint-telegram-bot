from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    """Clavier principal avec toutes les catégories."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Pseudo",    callback_data="menu_pseudo"),
        InlineKeyboardButton(text="📧 Email",     callback_data="menu_email"),
    )
    builder.row(
        InlineKeyboardButton(text="📱 Téléphone", callback_data="menu_phone"),
        InlineKeyboardButton(text="🌐 Réseau",    callback_data="menu_network"),
    )
    builder.row(
        InlineKeyboardButton(text="🔓 Leaks & Fuites", callback_data="menu_leaks"),
    )
    return builder.as_markup()


def pseudo_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Sherlock",  callback_data="ask_sherlock"),
        InlineKeyboardButton(text="🕵️ Maigret",   callback_data="ask_maigret"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Retour", callback_data="menu_main"))
    return builder.as_markup()


def email_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Comptes liés (Holehe)", callback_data="ask_email"),
    )
    builder.row(
        InlineKeyboardButton(text="🔓 Fuites (BD + LC + HIBP)", callback_data="ask_breach"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Retour", callback_data="menu_main"))
    return builder.as_markup()


def phone_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Analyser un numéro", callback_data="ask_phone"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Retour", callback_data="menu_main"))
    return builder.as_markup()


def network_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌍 Géoloc IP",     callback_data="ask_ip"),
        InlineKeyboardButton(text="📋 WHOIS",          callback_data="ask_whois"),
    )
    builder.row(
        InlineKeyboardButton(text="🔎 Recon Domaine", callback_data="ask_domain"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Retour", callback_data="menu_main"))
    return builder.as_markup()


def leaks_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔍 Recherche multi-bases",
            callback_data="ask_breach"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔑 Password compromis ?",
            callback_data="ask_pwned"
        ),
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Sources utilisées", callback_data="leaks_info"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Retour", callback_data="menu_main"))
    return builder.as_markup()


def back_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Menu principal", callback_data="menu_main"))
    return builder.as_markup()
