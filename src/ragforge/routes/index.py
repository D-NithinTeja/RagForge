from fastapi import APIRouter

from src.ragforge.routes import (
    auth_routes,
    conversation_routes,
    file_routes,
    process_routes,
)

router = APIRouter()

router.include_router(auth_routes.router)
router.include_router(file_routes.router)
router.include_router(process_routes.router)
router.include_router(conversation_routes.router)
