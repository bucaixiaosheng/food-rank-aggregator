"""
API路由配置
"""
from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/", tags=["API信息"])
async def api_info():
    """
    API信息接口
    返回API基本信息
    """
    return {
        "message": "欢迎使用餐饮聚合推荐平台API",
        "version": "v1",
        "docs": "/docs",
    }
