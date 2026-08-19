from fastapi.routing import APIRouter

from application.features.login import router as login_r
from application.features.logout import router as logout_r
from application.features.logout_all import router as logout_all_r
from application.features.me import router as me_r
from application.features.refresh import router as refresh_r
from application.features.register import router as register_r

router = APIRouter(prefix="/api/auth")

router.include_router(login_r)
router.include_router(me_r)
router.include_router(refresh_r)
router.include_router(register_r)
router.include_router(logout_r)
router.include_router(logout_all_r)
