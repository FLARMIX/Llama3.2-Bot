from aiogram import Router
from handlers.basic.menu import router as menu_router
from handlers.basic.start import router as start_router
from handlers.basic.messages import router as msg_router
from handlers.basic.settings import router as settings_router

router = Router()
router.include_router(start_router)
router.include_router(msg_router)
router.include_router(menu_router)
router.include_router(settings_router)
