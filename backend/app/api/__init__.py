from fastapi import APIRouter
from app.api import auth, posts, machines, calculate, analysis

api_router = APIRouter()
api_router.include_router(auth.router, prefix="")
api_router.include_router(posts.router, prefix="")
api_router.include_router(machines.router, prefix="")
api_router.include_router(calculate.router, prefix="")
api_router.include_router(analysis.router, prefix="")
