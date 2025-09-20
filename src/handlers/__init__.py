# handlers/__init__.py

def setup_message_routers():
    from aiogram import Router

    from . import parsers_control
    from . import (
        settings_kwork, settings_fl, settings_guru, 
        settings_youdo, settings_habr, settings_vk,
        settings_workzilla, settings_weblancer,
        channel_handler, parser_settings, settings_gpt,
        source_management
    )
    from . import settings_menu
    from . import stats
    from . import start

    router = Router()
    router.include_router(parsers_control.router)
    router.include_router(settings_kwork.router)
    router.include_router(settings_fl.router)
    router.include_router(settings_guru.router)
    router.include_router(settings_youdo.router)
    router.include_router(settings_habr.router)
    router.include_router(settings_vk.router)
    router.include_router(settings_workzilla.router)  # ✅ добавили WebLancer
    router.include_router(settings_menu.router)
    router.include_router(settings_weblancer.router)
    router.include_router(channel_handler.router)
    router.include_router(parser_settings.router)
    router.include_router(settings_gpt.router)
    router.include_router(source_management.router)
    router.include_router(stats.router)
    router.include_router(start.router)
    return router