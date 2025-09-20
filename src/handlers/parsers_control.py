# handlers/parsers_control.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from .services import (
    kwork_parser_service, habr_parser_service,
    fl_parser_service, guru_parser_service,
    youdo_parser_service, vk_parser_service,
    weblancer_parser_service,   # ✅ добавил WebLancer
    workzilla_parser_service    # ✅ добавил Work-Zilla
)

from keyboards.parser_control import enable_parsers_kb, disable_parsers_kb

router = Router()

# ============================
# ВКЛЮЧЕНИЕ ПАРСЕРОВ
# ============================

@router.message(Command("enable_parser"))
@router.message(F.text == "▶️ Включить парсер")
async def enable_parser(message: Message) -> None:
    await message.answer("Выберите парсер для включения:", reply_markup=enable_parsers_kb())


@router.callback_query(F.data == "enable_kwork")
async def enable_kwork(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Kwork включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_habr")
async def enable_habr(callback: CallbackQuery):
    if habr_parser_service:
        await habr_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Habr Career включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_fl")
async def enable_fl(callback: CallbackQuery):
    if fl_parser_service:
        await fl_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер FL включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_guru")
async def enable_guru(callback: CallbackQuery):
    if guru_parser_service:
        await guru_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Guru включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_youdo")
async def enable_youdo(callback: CallbackQuery):
    if youdo_parser_service:
        await youdo_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер YouDo включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_vk")
async def enable_vk(callback: CallbackQuery):
    if vk_parser_service:
        await vk_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер VK включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_weblancer")
async def enable_weblancer(callback: CallbackQuery):
    if weblancer_parser_service:
        await weblancer_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер WebLancer включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_workzilla")   # ✅ Work-Zilla enable
async def enable_workzilla(callback: CallbackQuery):
    if workzilla_parser_service:
        await workzilla_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Work-Zilla включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_all")
async def enable_all(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.start_parser(chat_id=callback.message.chat.id)
    if habr_parser_service:
        await habr_parser_service.start_parser(chat_id=callback.message.chat.id)
    if fl_parser_service:
        await fl_parser_service.start_parser(chat_id=callback.message.chat.id)
    if guru_parser_service:
        await guru_parser_service.start_parser(chat_id=callback.message.chat.id)
    if youdo_parser_service:
        await youdo_parser_service.start_parser(chat_id=callback.message.chat.id)
    if vk_parser_service:
        await vk_parser_service.start_parser(chat_id=callback.message.chat.id)
    if weblancer_parser_service:
        await weblancer_parser_service.start_parser(chat_id=callback.message.chat.id)
    if workzilla_parser_service:   # ✅ добавил Work-Zilla
        await workzilla_parser_service.start_parser(chat_id=callback.message.chat.id)
    await callback.message.edit_text("✅ Все парсеры включены.")
    await callback.answer()


# ============================
# ВЫКЛЮЧЕНИЕ ПАРСЕРОВ
# ============================

@router.message(Command("disable_parser"))
@router.message(F.text == "⏹️ Выключить парсер")
async def disable_parser(message: Message) -> None:
    await message.answer("Выберите парсер для выключения:", reply_markup=disable_parsers_kb())


@router.callback_query(F.data == "disable_kwork")
async def disable_kwork(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Kwork выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_habr")
async def disable_habr(callback: CallbackQuery):
    if habr_parser_service:
        await habr_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Habr Career выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_fl")
async def disable_fl(callback: CallbackQuery):
    if fl_parser_service:
        await fl_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер FL выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_guru")
async def disable_guru(callback: CallbackQuery):
    if guru_parser_service:
        await guru_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Guru выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_youdo")
async def disable_youdo(callback: CallbackQuery):
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер YouDo выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_vk")
async def disable_vk(callback: CallbackQuery):
    if vk_parser_service:
        await vk_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер VK выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_weblancer")   # ✅ WebLancer disable
async def disable_weblancer(callback: CallbackQuery):
    if weblancer_parser_service:
        await weblancer_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер WebLancer выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_workzilla")   # ✅ Work-Zilla disable
async def disable_workzilla(callback: CallbackQuery):
    if workzilla_parser_service:
        await workzilla_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Work-Zilla выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_all")
async def disable_all(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
    if habr_parser_service:
        await habr_parser_service.stop_parser()
    if fl_parser_service:
        await fl_parser_service.stop_parser()
    if guru_parser_service:
        await guru_parser_service.stop_parser()
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
    if vk_parser_service:
        await vk_parser_service.stop_parser()
    if weblancer_parser_service:
        await weblancer_parser_service.stop_parser()
    if workzilla_parser_service:   # ✅ добавил Work-Zilla
        await workzilla_parser_service.stop_parser()
    await callback.message.edit_text("🛑 Все парсеры выключены.")
    await callback.answer()


# ============================
# ВЫКЛЮЧЕНИЕ ВСЕХ (ReplyKeyboard)
# ============================

@router.message(F.text == "⏹️ Выключить все парсеры")
async def disable_all_from_menu(message: Message):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
    if habr_parser_service:
        await habr_parser_service.stop_parser()
    if fl_parser_service:
        await fl_parser_service.stop_parser()
    if guru_parser_service:
        await guru_parser_service.stop_parser()
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
    if vk_parser_service:
        await vk_parser_service.stop_parser()
    if weblancer_parser_service:
        await weblancer_parser_service.stop_parser()
    if workzilla_parser_service:   # ✅ добавил Work-Zilla
        await workzilla_parser_service.stop_parser()
    await message.answer("🛑 Все парсеры выключены.")