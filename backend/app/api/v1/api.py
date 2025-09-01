"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import search, test

api_router = APIRouter()

api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(test.router, prefix="/test", tags=["test"])