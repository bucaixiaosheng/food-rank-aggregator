"""
高德地图爬虫
通过API搜索周边美食
"""
import asyncio
import logging
import aiohttp
from typing import List, Optional, Dict
from urllib.parse import quote

from app.crawlers.base import BaseCrawler
from app.crawlers.schemas import RestaurantData, Platform
from app.core.config import settings


logger = logging.getLogger(__name__)


class AmapCrawler(BaseCrawler):
    """
    高德地图爬虫
    使用高德地图API搜索餐厅POI
    """
    
    # API端点
    POI_SEARCH_URL = "https://restapi.amap.com/v3/place/text"
    POI_AROUND_URL = "https://restapi.amap.com/v3/place/around"
    GEO_URL = "https://restapi.amap.com/v3/geocode/geo"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化高德爬虫
        
        Args:
            api_key: 高德API密钥（可选，默认从配置读取）
        """
        super().__init__(Platform.AMAP)
        self.api_key = api_key or getattr(settings, 'amap_api_key', None)
        
        if not self.api_key:
            self.logger.warning("未配置高德API密钥，将无法使用高德爬虫")
    
    async def crawl(
        self,
        city: str = "北京",
        location: Optional[str] = None,
        keywords: str = "美食",
        radius: int = 5000,
        max_results: int = 50,
        **kwargs
    ) -> List[RestaurantData]:
        """
        爬取高德地图餐厅POI
        
        Args:
            city: 城市名称
            location: 中心点坐标（经度,纬度），可选
            keywords: 搜索关键词
            radius: 搜索半径（米），仅当location有效时使用
            max_results: 最大结果数
            **kwargs: 其他参数
            
        Returns:
            List[RestaurantData]: 餐厅数据列表
        """
        if not self.api_key:
            self.logger.error("未配置高德API密钥")
            return []
        
        restaurants = []
        
        try:
            # 如果没有提供坐标，先获取城市中心点
            if not location:
                location = await self._get_city_center(city)
                if not location:
                    self.logger.error(f"无法获取城市坐标: {city}")
                    return []
            
            # 搜索周边美食
            pois = await self._search_around(
                location=location,
                keywords=keywords,
                radius=radius,
                max_results=max_results
            )
            
            # 解析POI数据
            for poi in pois:
                try:
                    restaurant = await self._parse_poi(poi)
                    if restaurant:
                        restaurants.append(restaurant)
                except Exception as e:
                    self.logger.error(f"解析POI失败: {e}")
                    continue
            
            self.logger.info(f"爬取完成，获取 {len(restaurants)} 家餐厅")
            
            return restaurants
            
        except Exception as e:
            self.logger.error(f"爬取失败: {e}", exc_info=True)
            return restaurants
    
    async def _get_city_center(self, city: str) -> Optional[str]:
        """
        获取城市中心点坐标
        
        Args:
            city: 城市名称
            
        Returns:
            Optional[str]: 坐标（经度,纬度）
        """
        try:
            params = {
                "key": self.api_key,
                "address": city,
                "output": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.GEO_URL, params=params) as response:
                    data = await response.json()
                    
                    if data.get("status") == "1" and data.get("geocodes"):
                        location = data["geocodes"][0].get("location")
                        return location
            
        except Exception as e:
            self.logger.error(f"获取城市坐标失败: {city}, 错误: {e}")
        
        return None
    
    async def _search_around(
        self,
        location: str,
        keywords: str,
        radius: int = 5000,
        max_results: int = 50
    ) -> List[Dict]:
        """
        周边搜索
        
        Args:
            location: 中心点坐标
            keywords: 关键词
            radius: 半径（米）
            max_results: 最大结果数
            
        Returns:
            List[Dict]: POI列表
        """
        pois = []
        page_size = 25  # 每页最大25条
        page = 1
        
        try:
            async with aiohttp.ClientSession() as session:
                while len(pois) < max_results:
                    params = {
                        "key": self.api_key,
                        "location": location,
                        "keywords": keywords,
                        "radius": radius,
                        "extensions": "all",
                        "offset": page_size,
                        "page": page,
                        "output": "json"
                    }
                    
                    # 频率限制
                    await self.anti_crawl.acquire_rate_limit()
                    await self.delay(0.5, 1.5)
                    
                    async with session.get(self.POI_AROUND_URL, params=params) as response:
                        data = await response.json()
                        
                        if data.get("status") != "1":
                            self.logger.error(f"API错误: {data.get('info')}")
                            break
                        
                        poi_list = data.get("pois", [])
                        
                        if not poi_list:
                            break
                        
                        pois.extend(poi_list)
                        
                        # 检查是否还有下一页
                        if len(poi_list) < page_size:
                            break
                        
                        page += 1
            
            return pois[:max_results]
            
        except Exception as e:
            self.logger.error(f"搜索失败: {e}", exc_info=True)
            return pois
    
    async def _parse_poi(self, poi: Dict) -> Optional[RestaurantData]:
        """
        解析POI数据
        
        Args:
            poi: POI数据字典
            
        Returns:
            Optional[RestaurantData]: 餐厅数据
        """
        try:
            name = poi.get("name", "")
            if not name:
                return None
            
            # 坐标
            location = poi.get("location", "").split(",")
            longitude = float(location[0]) if len(location) > 0 else None
            latitude = float(location[1]) if len(location) > 1 else None
            
            # 地址
            address = poi.get("address", "")
            pname = poi.get("pname", "")  # 省
            cityname = poi.get("cityname", "")  # 市
            adname = poi.get("adname", "")  # 区
            
            full_address = f"{cityname}{adname}{address}" if address else ""
            
            # 电话
            tel = poi.get("tel", "")
            
            # 类型
            type_code = poi.get("typecode", "")
            type_name = poi.get("type", "")
            
            # 评分（高德POI一般没有评分，需要详情接口）
            rating = None  # 高德POI基础数据不含评分
            
            # 图片
            photos = poi.get("photos", [])
            image_url = photos[0].get("url") if photos else None
            
            # 平台ID
            platform_id = poi.get("id")
            
            # 构建餐厅数据
            restaurant = RestaurantData(
                name=name,
                address=full_address,
                latitude=latitude,
                longitude=longitude,
                phone=tel,
                cuisine_type=type_name,
                rating=rating,
                image_url=image_url,
                platform=Platform.AMAP,
                platform_id=platform_id,
                tags=[type_name] if type_name else [],
            )
            
            return restaurant
            
        except Exception as e:
            self.logger.error(f"解析POI失败: {e}")
            return None
    
    async def search_by_name(
        self,
        restaurant_name: str,
        city: str = "北京"
    ) -> List[RestaurantData]:
        """
        按名称搜索餐厅
        
        Args:
            restaurant_name: 餐厅名称
            city: 城市名称
            
        Returns:
            List[RestaurantData]: 餐厅列表
        """
        if not self.api_key:
            return []
        
        try:
            params = {
                "key": self.api_key,
                "keywords": restaurant_name,
                "city": city,
                "citylimit": "true",
                "extensions": "all",
                "output": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.POI_SEARCH_URL, params=params) as response:
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        return []
                    
                    pois = data.get("pois", [])
                    restaurants = []
                    
                    for poi in pois:
                        restaurant = await self._parse_poi(poi)
                        if restaurant:
                            restaurants.append(restaurant)
                    
                    return restaurants
            
        except Exception as e:
            self.logger.error(f"搜索餐厅失败: {restaurant_name}, 错误: {e}")
            return []
    
    async def search_by_location(
        self,
        latitude: float,
        longitude: float,
        radius: int = 3000,
        keywords: str = "美食"
    ) -> List[RestaurantData]:
        """
        按位置搜索餐厅
        
        Args:
            latitude: 纬度
            longitude: 经度
            radius: 半径（米）
            keywords: 关键词
            
        Returns:
            List[RestaurantData]: 餐厅列表
        """
        location = f"{longitude},{latitude}"
        return await self.crawl(
            location=location,
            keywords=keywords,
            radius=radius
        )
