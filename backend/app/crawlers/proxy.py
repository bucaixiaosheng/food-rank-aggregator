"""
代理池管理
"""
import asyncio
import random
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ProxyStatus(str, Enum):
    """代理状态"""
    AVAILABLE = "available"
    BUSY = "busy"
    FAILED = "failed"
    BANNED = "banned"


@dataclass
class ProxyInfo:
    """代理信息"""
    host: str
    port: int
    protocol: str = "http"  # http/https/socks5
    username: Optional[str] = None
    password: Optional[str] = None
    
    status: ProxyStatus = ProxyStatus.AVAILABLE
    fail_count: int = 0
    success_count: int = 0
    last_used: Optional[datetime] = None
    last_failed: Optional[datetime] = None
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 1.0
        return self.success_count / total


class ProxyManager:
    """
    代理池管理器
    支持代理轮换、健康检查、自动剔除失效代理
    """
    
    def __init__(
        self,
        max_fail_count: int = 3,
        min_success_rate: float = 0.5,
        ban_duration: timedelta = timedelta(hours=1)
    ):
        """
        初始化代理管理器
        
        Args:
            max_fail_count: 最大失败次数
            min_success_rate: 最低成功率
            ban_duration: 禁用时长
        """
        self.proxies: List[ProxyInfo] = []
        self.max_fail_count = max_fail_count
        self.min_success_rate = min_success_rate
        self.ban_duration = ban_duration
        
        self.logger = logging.getLogger(__name__)
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        添加代理
        
        Args:
            host: 代理地址
            port: 端口
            protocol: 协议（http/https/socks5）
            username: 用户名（可选）
            password: 密码（可选）
        """
        proxy = ProxyInfo(
            host=host,
            port=port,
            protocol=protocol,
            username=username,
            password=password
        )
        self.proxies.append(proxy)
        self.logger.info(f"添加代理: {proxy.url}")
    
    def add_proxies_from_list(self, proxy_list: List[str]):
        """
        从字符串列表批量添加代理
        格式: "protocol://host:port" 或 "protocol://user:pass@host:port"
        
        Args:
            proxy_list: 代理列表
        """
        for proxy_str in proxy_list:
            try:
                # 简单解析（实际应该更完善）
                if "@" in proxy_str:
                    # 有认证信息
                    protocol, rest = proxy_str.split("://", 1)
                    auth, host_port = rest.split("@", 1)
                    username, password = auth.split(":", 1)
                    host, port = host_port.split(":", 1)
                    
                    self.add_proxy(
                        host=host,
                        port=int(port),
                        protocol=protocol,
                        username=username,
                        password=password
                    )
                else:
                    # 无认证
                    protocol, rest = proxy_str.split("://", 1)
                    host, port = rest.split(":", 1)
                    
                    self.add_proxy(
                        host=host,
                        port=int(port),
                        protocol=protocol
                    )
                    
            except Exception as e:
                self.logger.error(f"解析代理失败: {proxy_str}, 错误: {e}")
    
    def get_proxy(self) -> Optional[ProxyInfo]:
        """
        获取可用代理（轮换）
        
        Returns:
            Optional[ProxyInfo]: 代理信息
        """
        # 过滤可用代理
        available = [
            p for p in self.proxies
            if p.status == ProxyStatus.AVAILABLE
            and p.success_rate >= self.min_success_rate
        ]
        
        if not available:
            self.logger.warning("没有可用代理")
            return None
        
        # 按成功率排序，优先选择成功率高的
        available.sort(key=lambda p: p.success_rate, reverse=True)
        
        # 从前50%中随机选择（避免总是用同一个）
        top_half = available[:max(1, len(available) // 2)]
        proxy = random.choice(top_half)
        
        proxy.status = ProxyStatus.BUSY
        proxy.last_used = datetime.utcnow()
        
        self.logger.info(f"选择代理: {proxy.host}:{proxy.port}, 成功率: {proxy.success_rate:.2%}")
        
        return proxy
    
    def release_proxy(self, proxy: ProxyInfo, success: bool = True):
        """
        释放代理（更新状态）
        
        Args:
            proxy: 代理信息
            success: 是否成功
        """
        if success:
            proxy.success_count += 1
            proxy.status = ProxyStatus.AVAILABLE
        else:
            proxy.fail_count += 1
            proxy.last_failed = datetime.utcnow()
            
            # 检查是否需要禁用
            if proxy.fail_count >= self.max_fail_count:
                proxy.status = ProxyStatus.BANNED
                self.logger.warning(
                    f"代理 {proxy.host}:{proxy.port} 失败次数过多，已禁用"
                )
            elif proxy.success_rate < self.min_success_rate:
                proxy.status = ProxyStatus.FAILED
                self.logger.warning(
                    f"代理 {proxy.host}:{proxy.port} 成功率过低，已标记失败"
                )
            else:
                proxy.status = ProxyStatus.AVAILABLE
    
    async def check_proxy(self, proxy: ProxyInfo, test_url: str = "https://httpbin.org/ip") -> bool:
        """
        检查代理是否可用
        
        Args:
            proxy: 代理信息
            test_url: 测试URL
            
        Returns:
            bool: 是否可用
        """
        try:
            # 这里应该实际发送请求测试
            # 为简化示例，这里只是模拟
            await asyncio.sleep(0.1)  # 模拟网络请求
            return True
            
        except Exception as e:
            self.logger.error(f"代理检查失败: {proxy.host}:{proxy.port}, 错误: {e}")
            return False
    
    async def health_check(self):
        """
        健康检查所有代理
        """
        self.logger.info("开始代理健康检查...")
        
        for proxy in self.proxies:
            # 检查是否需要解除禁用
            if proxy.status == ProxyStatus.BANNED:
                if (datetime.utcnow() - proxy.last_failed) > self.ban_duration:
                    # 重新测试
                    if await self.check_proxy(proxy):
                        proxy.status = ProxyStatus.AVAILABLE
                        proxy.fail_count = 0
                        self.logger.info(f"代理 {proxy.host}:{proxy.port} 已恢复")
            
            # 检查失败的代理
            elif proxy.status == ProxyStatus.FAILED:
                if await self.check_proxy(proxy):
                    proxy.status = ProxyStatus.AVAILABLE
                    self.logger.info(f"代理 {proxy.host}:{proxy.port} 已恢复")
        
        self.logger.info("代理健康检查完成")
    
    def remove_proxy(self, proxy: ProxyInfo):
        """移除代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.logger.info(f"移除代理: {proxy.host}:{proxy.port}")
    
    def clear_proxies(self):
        """清空所有代理"""
        self.proxies.clear()
        self.logger.info("清空所有代理")
    
    def get_statistics(self) -> Dict:
        """
        获取代理池统计信息
        
        Returns:
            Dict: 统计数据
        """
        if not self.proxies:
            return {"total": 0}
        
        return {
            "total": len(self.proxies),
            "available": sum(1 for p in self.proxies if p.status == ProxyStatus.AVAILABLE),
            "busy": sum(1 for p in self.proxies if p.status == ProxyStatus.BUSY),
            "failed": sum(1 for p in self.proxies if p.status == ProxyStatus.FAILED),
            "banned": sum(1 for p in self.proxies if p.status == ProxyStatus.BANNED),
            "avg_success_rate": sum(p.success_rate for p in self.proxies) / len(self.proxies),
        }


class NoProxyManager:
    """
    空代理管理器（不使用代理）
    用于不需要代理的场景
    """
    
    def get_proxy(self) -> None:
        """返回None表示不使用代理"""
        return None
    
    def release_proxy(self, proxy: None, success: bool = True):
        """空实现"""
        pass
    
    def get_statistics(self) -> Dict:
        """返回空统计"""
        return {"total": 0, "enabled": False}
