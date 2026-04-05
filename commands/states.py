from aiogram.fsm.state import State, StatesGroup


class OSINTForm(StatesGroup):
    """États FSM pour attendre la saisie de l'utilisateur après clic sur un bouton."""
    waiting_sherlock  = State()
    waiting_maigret   = State()
    waiting_email     = State()
    waiting_breach    = State()
    waiting_pwned     = State()
    waiting_phone     = State()
    waiting_ip        = State()
    waiting_whois     = State()
    waiting_domain    = State()
