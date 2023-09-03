from fastapi.routing import APIRouter

from cooking_forum_backend.web.api import docs, auth

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(auth.router)
