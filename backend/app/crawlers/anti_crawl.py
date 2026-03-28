"""
反爬策略 - UserAgent轮换、请求间隔、请求头伪装
"""
import asyncio
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import deque


logger = logging.getLogger(__name__)


class UserAgentPool:
    """
    UserAgent轮换池
    """
    
    # 常用UserAgent列表
    DEFAULT_USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        
        # Mobile
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]
    
    def __init__(self, user_agents: Optional[List[str]] = None):
        """
        初始化UserAgent池
        
        Args:
            user_agents: 自定义UserAgent列表（可选）
        """
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS.copy()
        self._recently_used = deque(maxlen=5)  # 避免短期内重复使用
    
    def get_random(self) -> str:
        """获取随机UserAgent"""
        available = [ua for ua in self.user_agents if ua not in self._recently_used]
        
        if not available:
            available = self.user_agents
        
        user_agent = random.choice(available)
        self._recently_used.append(user_agent)
        
        return user_agent


class RequestHeaders:
    """
    请求头生成器
    """
    
    # 通用请求头
    COMMON_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    # 平台特定请求头
    PLATFORM_HEADERS = {
        "meituan": {
            "Referer": "https://www.meituan.com/",
            "Host": "www.meituan.com",
        },
        "dianping": {
            "Referer": "https://www.dianping.com/",
            "Host": "www.dianping.com",
        },
        "xiaohongshu": {
            "Referer": "https://www.xiaohongshu.com/",
            "Host": "www.xiaohongshu.com",
        },
        "amap": {
            "Referer": "https://www.amap.com/",
            "Host": "restapi.amap.com",
        },
    }
    
    @classmethod
    def generate(
        cls,
        platform: str,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成请求头
        
        Args:
            platform: 平台名称
            user_agent: UserAgent（可选）
            
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = cls.COMMON_HEADERS.copy()
        
        # 添加平台特定请求头
        if platform in cls.PLATFORM_HEADERS:
            headers.update(cls.PLATFORM_HEADERS[platform])
        
        # 添加UserAgent
        if user_agent:
            headers["User-Agent"] = user_agent
        
        return headers


class RateLimiter:
    """
    请求频率限制器
    使用令牌桶算法
    """
    
    def __init__(
        self,
        requests_per_minute: int = 10,
        burst_size: int = 5
    ):
        """
        初始化频率限制器
        
        Args:
            requests_per_minute: 每分钟最大请求数
            burst_size: 突发请求大小
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = datetime.utcnow()
        self.lock = asyncio.Lock()
        
        # 令牌补充间隔
        self.refill_interval = 60.0 / requests_per_minute
    
    async def acquire(self):
        """
        获取令牌（如果可用）
        如果不可用，等待直到有令牌
        """
        async with self.lock:
            now = datetime.utcnow()
            time_passed = (now - self.last_update).total_seconds()
            
            # 补充令牌
            self.tokens = min(
                self.burst_size,
                self.tokens + time_passed / self.refill_interval
            )
            self.last_update = now
            
            # 如果没有令牌，等待
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * self.refill_interval
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class AntiCrawlManager:
    """
    反爬策略管理器
    整合UserAgent轮换、请求间隔、请求头伪装
    """
    
    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 8.0,
        requests_per_minute: int = 10
    ):
        """
        初始化反爬管理器
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            requests_per_minute: 每分钟最大请求数
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        self.ua_pool = UserAgentPool()
        self.rate_limiter = RateLimiter(requests_per_minute)
        
        self.logger = logging.getLogger(__name__)
    
    async def random_delay(
        self,
        min_seconds: Optional[float] = None,
        max_seconds: Optional[float] = None
    ):
        """
        随机延迟
        
        Args:
            min_seconds: 最小延迟（可选，覆盖默认值）
            max_seconds: 最大延迟（可选，覆盖默认值）
        """
        min_sec = min_seconds or self.min_delay
        max_sec = max_seconds or self.max_delay
        
        delay = random.uniform(min_sec, max_sec)
        self.logger.debug(f"延迟 {delay:.2f} 秒")
        await asyncio.sleep(delay)
    
    def get_user_agent(self) -> str:
        """获取随机UserAgent"""
        return self.ua_pool.get_random()
    
    def get_headers(
        self,
        platform: str,
        with_user_agent: bool = True
    ) -> Dict[str, str]:
        """
        获取请求头
        
        Args:
            platform: 平台名称
            with_user_agent: 是否包含UserAgent
            
        Returns:
            Dict[str, str]: 请求头
        """
        user_agent = self.get_user_agent() if with_user_agent else None
        return RequestHeaders.generate(platform, user_agent)
    
    async def acquire_rate_limit(self):
        """获取频率限制许可"""
        await self.rate_limiter.acquire()
    
    async def safe_request(
        self,
        platform: str,
        request_func,
        *args,
        **kwargs
    ):
        """
        安全请求（带反爬策略）
        
        Args:
            platform: 平台名称
            request_func: 请求函数
            *args, **kwargs: 请求函数参数
            
        Returns:
            请求结果
        """
        # 频率限制
        await self.acquire_rate_limit()
        
        # 随机延迟
        await self.random_delay()
        
        # 添加请求头
        if "headers" not in kwargs:
            kwargs["headers"] = self.get_headers(platform)
        
        # 执行请求
        return await request_func(*args, **kwargs)


class CookieManager:
    """
    Cookie管理器
    """
    
    def __init__(self):
        self.cookies: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    def save_cookies(self, platform: str, cookies: Dict):
        """保存平台的Cookie"""
        self.cookies[platform] = cookies
        self.logger.info(f"保存 {platform} 的Cookie")
    
    def get_cookies(self, platform: str) -> Optional[Dict]:
        """获取平台的Cookie"""
        return self.cookies.get(platform)
    
    def clear_cookies(self, platform: Optional[str] = None):
        """清除Cookie"""
        if platform:
            self.cookies.pop(platform, None)
            self.logger.info(f"清除 {platform} 的Cookie")
        else:
            self.cookies.clear()
            self.logger.info("清除所有Cookie")
