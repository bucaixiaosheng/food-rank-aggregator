"""
爬虫基类 - 定义通用接口
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crawlers.schemas import RestaurantData, NoteData, CrawlResult, Platform
from app.crawlers.anti_crawl import AntiCrawlManager
from app.models.restaurant import Restaurant
from app.models.crawler import CrawlTask, PlatformRating


logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    爬虫抽象基类
    所有平台爬虫必须继承此类
    """
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.anti_crawl = AntiCrawlManager()
        self.logger = logging.getLogger(f"{__name__}.{platform.value}")
        self._session: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._is_running = False
    
    @abstractmethod
    async def crawl(self, **kwargs) -> List[RestaurantData | NoteData]:
        """
        爬取数据（抽象方法，子类必须实现）
        
        Args:
            **kwargs: 爬取参数（如城市、关键词等）
            
        Returns:
            List[RestaurantData | NoteData]: 爬取的数据列表
        """
        pass
    
    @abstractmethod
    async def parse(self, raw_data: Any) -> List[RestaurantData | NoteData]:
        """
        解析数据（抽象方法，子类必须实现）
        
        Args:
            raw_data: 原始数据（HTML、JSON等）
            
        Returns:
            List[RestaurantData | NoteData]: 解析后的数据列表
        """
        pass
    
    async def save(
        self, 
        data: List[RestaurantData | NoteData], 
        db: AsyncSession
    ) -> int:
        """
        保存数据到数据库
        
        Args:
            data: 数据列表
            db: 数据库会话
            
        Returns:
            int: 成功保存的数量
        """
        saved_count = 0
        
        for item in data:
            try:
                if isinstance(item, RestaurantData):
                    # 检查是否已存在（根据平台ID去重）
                    existing = await self._get_existing_restaurant(db, item)
                    
                    if existing:
                        # 更新现有记录
                        restaurant = await self._update_restaurant(existing, item, db)
                    else:
                        # 创建新记录
                        restaurant = await self._create_restaurant(item, db)
                    
                    # 创建或更新平台评分
                    await self._save_platform_rating(restaurant.id, item, db)
                    
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"保存数据失败: {item.name if hasattr(item, 'name') else item}, 错误: {e}")
                continue
        
        await db.commit()
        return saved_count
    
    async def _get_existing_restaurant(
        self, 
        db: AsyncSession, 
        data: RestaurantData
    ) -> Optional[Restaurant]:
        """检查餐厅是否已存在"""
        # 先按平台ID查找
        if data.platform_id:
            stmt = select(Restaurant).where(
                Restaurant.platform == data.platform,
                Restaurant.platform_id == data.platform_id
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                return result.scalar_one_or_none()
        
        # 再按名称+地址模糊匹配
        if data.name and data.address:
            stmt = select(Restaurant).where(
                Restaurant.name == data.name,
                Restaurant.address == data.address
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        
        return None
    
    async def _create_restaurant(
        self, 
        data: RestaurantData, 
        db: AsyncSession
    ) -> Restaurant:
        """创建新餐厅"""
        restaurant = Restaurant(
            name=data.name,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            phone=data.phone,
            cuisine_type=data.cuisine_type,
            price_range=data.price_range,
            rating=data.rating,
            description=data.description,
            business_hours=data.business_hours,
            image_url=data.image_url,
            platform_source=data.platform,
            platform_id=data.platform_id,
        )
        db.add(restaurant)
        await db.flush()  # 获取ID
        return restaurant
    
    async def _update_restaurant(
        self, 
        restaurant: Restaurant, 
        data: RestaurantData, 
        db: AsyncSession
    ) -> Restaurant:
        """更新现有餐厅"""
        # 更新非空字段
        update_fields = {
            'address': data.address,
            'latitude': data.latitude,
            'longitude': data.longitude,
            'phone': data.phone,
            'cuisine_type': data.cuisine_type,
            'price_range': data.price_range,
            'rating': data.rating,
            'description': data.description,
            'business_hours': data.business_hours,
            'image_url': data.image_url,
        }
        
        for field, value in update_fields.items():
            if value is not None:
                setattr(restaurant, field, value)
        
        restaurant.updated_at = datetime.utcnow()
        return restaurant
    
    async def _save_platform_rating(
        self, 
        restaurant_id: int, 
        data: RestaurantData, 
        db: AsyncSession
    ) -> None:
        """保存平台评分"""
        # 检查是否已存在该平台的评分
        stmt = select(PlatformRating).where(
            PlatformRating.restaurant_id == restaurant_id,
            PlatformRating.platform == data.platform
        )
        result = await db.execute(stmt)
        rating_record = result.scalar_one_or_none()
        
        if rating_record:
            # 更新
            rating_record.rating = data.rating
            rating_record.review_count = data.review_count
            rating_record.tags = data.tags
            rating_record.platform_url = data.platform_url
            rating_record.updated_at = datetime.utcnow()
        else:
            # 创建
            rating_record = PlatformRating(
                restaurant_id=restaurant_id,
                platform=data.platform,
                rating=data.rating,
                review_count=data.review_count,
                tags=data.tags,
                platform_url=data.platform_url,
            )
            db.add(rating_record)
    
    async def execute(
        self, 
        db: AsyncSession, 
        **kwargs
    ) -> CrawlResult:
        """
        执行爬取任务（入口方法）
        
        Args:
            db: 数据库会话
            **kwargs: 爬取参数
            
        Returns:
            CrawlResult: 爬取结果
        """
        start_time = datetime.utcnow()
        
        try:
            self._is_running = True
            self.logger.info(f"开始爬取 {self.platform.value} 数据，参数: {kwargs}")
            
            # 创建爬取任务记录
            crawl_task = CrawlTask(
                platform=self.platform.value,
                status="running",
                started_at=start_time
            )
            db.add(crawl_task)
            await db.commit()
            
            # 执行爬取
            data = await self.crawl(**kwargs)
            
            # 保存数据
            saved_count = await self.save(data, db)
            
            # 更新任务状态
            crawl_task.status = "completed"
            crawl_task.finished_at = datetime.utcnow()
            crawl_task.result_count = saved_count
            await db.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"爬取完成: {self.platform.value}, "
                f"获取 {len(data)} 条，保存 {saved_count} 条，耗时 {duration:.2f}秒"
            )
            
            return CrawlResult(
                platform=self.platform,
                success=True,
                count=saved_count,
                data=data,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"爬取失败: {self.platform.value}, 错误: {e}", exc_info=True)
            
            # 更新任务状态为失败
            crawl_task.status = "failed"
            crawl_task.finished_at = datetime.utcnow()
            crawl_task.error_message = str(e)
            await db.commit()
            
            return CrawlResult(
                platform=self.platform,
                success=False,
                error=str(e)
            )
            
        finally:
            self._is_running = False
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._session:
            await self._session.close()
            self._session = None
    
    async def delay(self, min_seconds: float = 2.0, max_seconds: float = 8.0):
        """随机延迟（反爬）"""
        await self.anti_crawl.random_delay(min_seconds, max_seconds)
