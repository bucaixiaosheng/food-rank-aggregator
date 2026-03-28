"""
爬虫模块
"""
from app.crawlers.base import BaseCrawler
from app.crawlers.engine import CrawlerEngine, CrawlerManager
from app.crawlers.schemas import RestaurantData, NoteData, CrawlResult, Platform
from app.crawlers.anti_crawl import AntiCrawlManager, UserAgentPool, RateLimiter
from app.crawlers.proxy import ProxyManager, NoProxyManager
from app.crawlers.cleaner import DataCleaner, RestaurantMatcher

# 平台爬虫（延迟导入避免循环依赖）
__all__ = [
    # 基础类
    "BaseCrawler",
    "CrawlerEngine",
    "CrawlerManager",
    
    # 数据模型
    "RestaurantData",
    "NoteData",
    "CrawlResult",
    "Platform",
    
    # 反爬工具
    "AntiCrawlManager",
    "UserAgentPool",
    "RateLimiter",
    
    # 代理管理
    "ProxyManager",
    "NoProxyManager",
    
    # 数据清洗
    "DataCleaner",
    "RestaurantMatcher",
]


def get_crawler(platform: str):
    """
    获取指定平台的爬虫实例
    
    Args:
        platform: 平台名称（meituan/dianping/xiaohongshu/amap）
        
    Returns:
        BaseCrawler: 爬虫实例
    """
    crawlers = {
        "meituan": "app.crawlers.meituan.MeituanCrawler",
        "dianping": "app.crawlers.dianping.DianpingCrawler",
        "xiaohongshu": "app.crawlers.xiaohongshu.XiaohongshuCrawler",
        "amap": "app.crawlers.amap.AmapCrawler",
    }
    
    if platform not in crawlers:
        raise ValueError(f"Unknown platform: {platform}")
    
    # 延迟导入
    import importlib
    module_path, class_name = crawlers[platform].rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()
