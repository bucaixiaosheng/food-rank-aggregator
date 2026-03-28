"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "吃什么 - 餐饮聚合推荐平台"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API配置
    api_v1_prefix: str = "/api/v1"
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./data/food_rank.db"
    
    # CORS配置
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # 爬虫配置
    crawl_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    crawl_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
