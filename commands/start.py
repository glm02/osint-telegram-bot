from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from utils.keyboards import main_menu

router = Router()


@router.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🕵️ *OSINT Bot* — Bienvenue !\n\n"
        "Sélectionne une catégorie ci-dessous :",
        reply_markup=main_menu()
    )


@router.message(Command("annuler", "cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Action annulée.\n",
        reply_markup=main_menu()
    )
