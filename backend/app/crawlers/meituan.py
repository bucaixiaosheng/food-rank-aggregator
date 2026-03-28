"""
美团爬虫
爬取美团美食排行榜
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser

from app.crawlers.base import BaseCrawler
from app.crawlers.schemas import RestaurantData, Platform


logger = logging.getLogger(__name__)


class MeituanCrawler(BaseCrawler):
    """
    美团美食爬虫
    使用Playwright处理动态加载
    """
    
    BASE_URL = "https://www.meituan.com"
    SEARCH_URL = "https://www.meituan.com/s/{city}/美食/{keyword}"
    
    def __init__(self):
        super().__init__(Platform.MEITUAN)
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        if not self._browser:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self._page = await self._browser.new_page()
            
            # 设置UserAgent
            await self._page.set_extra_http_headers({
                "User-Agent": self.anti_crawl.get_user_agent()
            })
    
    async def crawl(
        self,
        city: str = "北京",
        cuisine: Optional[str] = None,
        max_pages: int = 3,
        **kwargs
    ) -> List[RestaurantData]:
        """
        爬取美团美食排行榜
        
        Args:
            city: 城市名称
            cuisine: 菜系类型（可选）
            max_pages: 最大爬取页数
            **kwargs: 其他参数
            
        Returns:
            List[RestaurantData]: 餐厅数据列表
        """
        await self._init_browser()
        
        restaurants = []
        keyword = cuisine or "美食"
        
        try:
            # 构建搜索URL
            url = self.SEARCH_URL.format(
                city=quote(city),
                keyword=quote(keyword)
            )
            
            self.logger.info(f"开始爬取: {url}")
            
            for page_num in range(1, max_pages + 1):
                try:
                    # 访问页面
                    page_url = f"{url}&page={page_num}"
                    await self._page.goto(page_url, wait_until="networkidle", timeout=30000)
                    
                    # 等待内容加载
                    await self._page.wait_for_selector(".poi-item", timeout=10000)
                    
                    # 解析数据
                    page_data = await self.parse(self._page)
                    restaurants.extend(page_data)
                    
                    self.logger.info(
                        f"第 {page_num} 页爬取完成，"
                        f"获取 {len(page_data)} 条数据"
                    )
                    
                    # 随机延迟
                    await self.delay(2.0, 5.0)
                    
                except Exception as e:
                    self.logger.error(f"爬取第 {page_num} 页失败: {e}")
                    break
            
            return restaurants
            
        except Exception as e:
            self.logger.error(f"爬取失败: {e}", exc_info=True)
            return restaurants
    
    async def parse(self, page: Page) -> List[RestaurantData]:
        """
        解析美团页面
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[RestaurantData]: 解析后的餐厅列表
        """
        restaurants = []
        
        try:
            # 获取所有餐厅卡片
            items = await page.query_selector_all(".poi-item")
            
            for item in items:
                try:
                    # 提取基本信息
                    name_elem = await item.query_selector(".poi-title a")
                    name = await name_elem.inner_text() if name_elem else ""
                    
                    if not name:
                        continue
                    
                    # 地址
                    addr_elem = await item.query_selector(".poi-address")
                    address = await addr_elem.inner_text() if addr_elem else ""
                    
                    # 评分
                    rating_elem = await item.query_selector(".rating-score")
                    rating_text = await rating_elem.inner_text() if rating_elem else "0"
                    rating = float(rating_text) if rating_text else None
                    
                    # 评论数
                    review_elem = await item.query_selector(".review-num")
                    review_text = await review_elem.inner_text() if review_elem else "0"
                    review_count = int(review_text.replace("条评价", "").strip()) if review_text else 0
                    
                    # 价格
                    price_elem = await item.query_selector(".avg-price")
                    price_text = await price_elem.inner_text() if price_elem else ""
                    avg_price = float(price_text.replace("￥", "").replace("/人", "").strip()) if price_text else None
                    
                    # 图片
                    img_elem = await item.query_selector(".poi-img img")
                    image_url = await img_elem.get_attribute("src") if img_elem else None
                    
                    # 链接
                    link_elem = await item.query_selector(".poi-title a")
                    platform_url = await link_elem.get_attribute("href") if link_elem else None
                    
                    # 提取平台ID
                    platform_id = None
                    if platform_url:
                        parts = platform_url.split("/")
                        for part in parts:
                            if part.isdigit():
                                platform_id = part
                                break
                    
                    # 构建餐厅数据
                    restaurant = RestaurantData(
                        name=name.strip(),
                        address=address.strip(),
                        rating=rating,
                        review_count=review_count,
                        avg_price=avg_price,
                        image_url=image_url,
                        platform=Platform.MEITUAN,
                        platform_id=platform_id,
                        platform_url=platform_url,
                        cuisine_type=None,  # 从页面提取
                    )
                    
                    restaurants.append(restaurant)
                    
                except Exception as e:
                    self.logger.error(f"解析餐厅失败: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"解析页面失败: {e}", exc_info=True)
        
        return restaurants
    
    async def crawl_incremental(
        self,
        city: str = "北京",
        cuisine: Optional[str] = None,
        last_count: int = 0,
        **kwargs
    ) -> List[RestaurantData]:
        """
        增量爬取（只爬取新增的餐厅）
        
        Args:
            city: 城市名称
            cuisine: 菜系类型
            last_count: 上次爬取的数量
            **kwargs: 其他参数
            
        Returns:
            List[RestaurantData]: 新增的餐厅列表
        """
        # 爬取所有数据
        all_data = await self.crawl(city=city, cuisine=cuisine, max_pages=1, **kwargs)
        
        # 只返回新增部分（这里简化处理，实际应该对比数据库）
        if len(all_data) > last_count:
            return all_data[last_count:]
        
        return []
    
    async def cleanup(self):
        """清理资源"""
        if self._page:
            await self._page.close()
            self._page = None
        
        if self._browser:
            await self._browser.close()
            self._browser = None
