"""
爬虫引擎 - 多爬虫调度器
"""
import asyncio
import logging
from typing import List, Dict, Type, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession

from app.crawlers.base import BaseCrawler
from app.crawlers.schemas import CrawlResult, Platform


logger = logging.getLogger(__name__)


class CrawlerEngine:
    """
    爬虫调度引擎
    管理多个爬虫的并发执行、错误重试、日志记录
    """
    
    def __init__(
        self,
        max_concurrent: int = 3,
        max_retries: int = 3,
        retry_delay: float = 60.0,
    ):
        """
        初始化爬虫引擎
        
        Args:
            max_concurrent: 最大并发数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._crawlers: Dict[Platform, BaseCrawler] = {}
        self._results: List[CrawlResult] = []
        self._is_running = False
        
        self.logger = logging.getLogger(__name__)
    
    def register_crawler(self, crawler: BaseCrawler):
        """
        注册爬虫
        
        Args:
            crawler: 爬虫实例
        """
        if not isinstance(crawler, BaseCrawler):
            raise ValueError("爬虫必须继承 BaseCrawler")
        
        self._crawlers[crawler.platform] = crawler
        self.logger.info(f"注册爬虫: {crawler.platform.value}")
    
    def get_crawler(self, platform: Platform) -> Optional[BaseCrawler]:
        """获取指定平台的爬虫"""
        return self._crawlers.get(platform)
    
    async def run_single(
        self,
        platform: Platform,
        db: AsyncSession,
        **kwargs
    ) -> CrawlResult:
        """
        运行单个爬虫（带重试）
        
        Args:
            platform: 平台名称
            db: 数据库会话
            **kwargs: 爬取参数
            
        Returns:
            CrawlResult: 爬取结果
        """
        crawler = self._crawlers.get(platform)
        if not crawler:
            self.logger.error(f"未注册的爬虫: {platform.value}")
            return CrawlResult(
                platform=platform,
                success=False,
                error=f"爬虫未注册: {platform.value}"
            )
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"执行爬虫 {platform.value} "
                    f"(尝试 {attempt + 1}/{self.max_retries})"
                )
                
                result = await crawler.execute(db, **kwargs)
                
                if result.success:
                    return result
                
                # 如果失败，等待后重试
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"爬虫 {platform.value} 失败，"
                        f"{self.retry_delay}秒后重试..."
                    )
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                self.logger.error(
                    f"爬虫 {platform.value} 异常: {e}",
                    exc_info=True
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # 所有重试都失败
        return CrawlResult(
            platform=platform,
            success=False,
            error=f"重试 {self.max_retries} 次后仍然失败"
        )
    
    async def run_multiple(
        self,
        platforms: List[Platform],
        db: AsyncSession,
        **kwargs
    ) -> List[CrawlResult]:
        """
        并发运行多个爬虫
        
        Args:
            platforms: 平台列表
            db: 数据库会话
            **kwargs: 爬取参数
            
        Returns:
            List[CrawlResult]: 爬取结果列表
        """
        if not platforms:
            self.logger.warning("未指定要运行的爬虫")
            return []
        
        self._is_running = True
        self._results = []
        
        self.logger.info(
            f"开始并发爬取 {len(platforms)} 个平台，"
            f"最大并发数: {self.max_concurrent}"
        )
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_semaphore(platform: Platform):
            async with semaphore:
                try:
                    result = await self.run_single(platform, db, **kwargs)
                    self._results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"爬虫 {platform.value} 执行失败: {e}",
                        exc_info=True
                    )
                    self._results.append(
                        CrawlResult(
                            platform=platform,
                            success=False,
                            error=str(e)
                        )
                    )
        
        # 并发执行
        tasks = [run_with_semaphore(platform) for platform in platforms]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self._is_running = False
        
        # 统计结果
        success_count = sum(1 for r in self._results if r.success)
        self.logger.info(
            f"爬取完成: 成功 {success_count}/{len(self._results)}"
        )
        
        return self._results
    
    async def run_all(
        self,
        db: AsyncSession,
        **kwargs
    ) -> List[CrawlResult]:
        """
        运行所有注册的爬虫
        
        Args:
            db: 数据库会话
            **kwargs: 爬取参数
            
        Returns:
            List[CrawlResult]: 爬取结果列表
        """
        platforms = list(self._crawlers.keys())
        return await self.run_multiple(platforms, db, **kwargs)
    
    def get_results(self) -> List[CrawlResult]:
        """获取最近的爬取结果"""
        return self._results
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计数据
        """
        if not self._results:
            return {}
        
        total = len(self._results)
        success = sum(1 for r in self._results if r.success)
        failed = total - success
        
        total_count = sum(r.count for r in self._results)
        total_duration = sum(r.duration for r in self._results if r.duration)
        
        return {
            "total_platforms": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "0%",
            "total_restaurants": total_count,
            "total_duration": f"{total_duration:.2f}秒",
            "platforms": {
                r.platform.value: {
                    "success": r.success,
                    "count": r.count,
                    "error": r.error
                }
                for r in self._results
            }
        }
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def registered_platforms(self) -> List[Platform]:
        """已注册的平台列表"""
        return list(self._crawlers.keys())


class CrawlerManager:
    """
    爬虫管理器（单例模式）
    用于全局管理爬虫实例
    """
    
    _instance: Optional['CrawlerManager'] = None
    _engine: Optional[CrawlerEngine] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_engine(cls) -> CrawlerEngine:
        """获取爬虫引擎实例"""
        if cls._engine is None:
            cls._engine = CrawlerEngine()
        return cls._engine
    
    @classmethod
    def initialize(cls):
        """初始化爬虫管理器"""
        engine = cls.get_engine()
        
        # 延迟导入避免循环依赖
        from app.crawlers.meituan import MeituanCrawler
        from app.crawlers.dianping import DianpingCrawler
        from app.crawlers.xiaohongshu import XiaohongshuCrawler
        from app.crawlers.amap import AmapCrawler
        
        # 注册所有爬虫
        engine.register_crawler(MeituanCrawler())
        engine.register_crawler(DianpingCrawler())
        engine.register_crawler(XiaohongshuCrawler())
        engine.register_crawler(AmapCrawler())
        
        logger.info("爬虫管理器初始化完成")
