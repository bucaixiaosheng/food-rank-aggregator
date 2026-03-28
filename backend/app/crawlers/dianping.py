"""
大众点评爬虫
爬取大众点评餐厅列表和详情页
"""
import asyncio
import logging
import re
from typing import List, Optional, Dict
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser

from app.crawlers.base import BaseCrawler
from app.crawlers.schemas import RestaurantData, Platform


logger = logging.getLogger(__name__)


class DianpingCrawler(BaseCrawler):
    """
    大众点评爬虫
    使用Playwright处理反爬（字体加密等）
    """
    
    BASE_URL = "https://www.dianping.com"
    SEARCH_URL = "https://www.dianping.com/search/keyword/{city}/0_{keyword}"
    
    def __init__(self):
        super().__init__(Platform.DIANPING)
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        if not self._browser:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建上下文（模拟真实浏览器）
            context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.anti_crawl.get_user_agent(),
                locale='zh-CN',
            )
            
            self._page = await context.new_page()
            
            # 注入脚本绕过检测
            await self._page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
    
    async def crawl(
        self,
        city: str = "北京",
        cuisine: Optional[str] = None,
        max_pages: int = 3,
        **kwargs
    ) -> List[RestaurantData]:
        """
        爬取大众点评餐厅列表
        
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
        
        # 城市映射
        city_map = {
            "北京": "2",
            "上海": "1",
            "广州": "4",
            "深圳": "7",
            "杭州": "3",
        }
        city_id = city_map.get(city, "2")
        
        try:
            # 构建搜索URL
            url = self.SEARCH_URL.format(
                city=city_id,
                keyword=quote(keyword)
            )
            
            self.logger.info(f"开始爬取: {url}")
            
            for page_num in range(1, max_pages + 1):
                try:
                    # 访问页面
                    page_url = f"{url}/p{page_num}"
                    
                    # 添加请求头
                    await self._page.set_extra_http_headers(
                        self.anti_crawl.get_headers("dianping")
                    )
                    
                    await self._page.goto(page_url, wait_until="networkidle", timeout=30000)
                    
                    # 等待内容加载
                    await self._page.wait_for_selector(".shop-list", timeout=10000)
                    
                    # 解析数据
                    page_data = await self.parse(self._page)
                    restaurants.extend(page_data)
                    
                    self.logger.info(
                        f"第 {page_num} 页爬取完成，"
                        f"获取 {len(page_data)} 条数据"
                    )
                    
                    # 随机延迟（大众点评反爬严格，延迟更长）
                    await self.delay(3.0, 8.0)
                    
                except Exception as e:
                    self.logger.error(f"爬取第 {page_num} 页失败: {e}")
                    break
            
            return restaurants
            
        except Exception as e:
            self.logger.error(f"爬取失败: {e}", exc_info=True)
            return restaurants
    
    async def parse(self, page: Page) -> List[RestaurantData]:
        """
        解析大众点评页面
        注意：大众点评有字体加密，需要特殊处理
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[RestaurantData]: 解析后的餐厅列表
        """
        restaurants = []
        
        try:
            # 使用JavaScript直接提取数据（绕过字体加密）
            shop_data = await page.evaluate("""
                () => {
                    const shops = [];
                    const items = document.querySelectorAll('.shop-list li');
                    
                    items.forEach(item => {
                        try {
                            const nameElem = item.querySelector('.shop-name');
                            const name = nameElem ? nameElem.textContent.trim() : '';
                            
                            if (!name) return;
                            
                            const addrElem = item.querySelector('.shop-addr');
                            const address = addrElem ? addrElem.textContent.trim() : '';
                            
                            const ratingElem = item.querySelector('.shop-score');
                            const rating = ratingElem ? parseFloat(ratingElem.textContent) : null;
                            
                            const priceElem = item.querySelector('.shop-price');
                            const priceText = priceElem ? priceElem.textContent : '';
                            const avgPrice = priceText ? parseFloat(priceText.match(/\\d+/)?.[0] || 0) : null;
                            
                            const commentElem = item.querySelector('.review-num');
                            const commentText = commentElem ? commentElem.textContent : '0';
                            const commentCount = parseInt(commentText.match(/\\d+/)?.[0] || '0');
                            
                            const imgElem = item.querySelector('.shop-img img');
                            const imageUrl = imgElem ? imgElem.src : null;
                            
                            const linkElem = item.querySelector('.shop-name a');
                            const shopUrl = linkElem ? linkElem.href : null;
                            
                            const tagElems = item.querySelectorAll('.shop-tag span');
                            const tags = Array.from(tagElems).map(t => t.textContent.trim()).filter(t => t);
                            
                            shops.push({
                                name, address, rating, avgPrice, 
                                commentCount, imageUrl, shopUrl, tags
                            });
                        } catch (e) {
                            console.error('解析店铺失败:', e);
                        }
                    });
                    
                    return shops;
                }
            """)
            
            # 转换为RestaurantData
            for shop in shop_data:
                # 提取平台ID
                platform_id = None
                if shop.get('shopUrl'):
                    match = re.search(r'/shop/(\d+)', shop['shopUrl'])
                    if match:
                        platform_id = match.group(1)
                
                restaurant = RestaurantData(
                    name=shop['name'],
                    address=shop.get('address', ''),
                    rating=shop.get('rating'),
                    review_count=shop.get('commentCount', 0),
                    avg_price=shop.get('avgPrice'),
                    image_url=shop.get('imageUrl'),
                    platform=Platform.DIANPING,
                    platform_id=platform_id,
                    platform_url=shop.get('shopUrl'),
                    tags=shop.get('tags', []),
                )
                
                restaurants.append(restaurant)
            
        except Exception as e:
            self.logger.error(f"解析页面失败: {e}", exc_info=True)
        
        return restaurants
    
    async def crawl_detail(self, shop_url: str) -> Optional[Dict]:
        """
        爬取餐厅详情页
        
        Args:
            shop_url: 餐厅详情页URL
            
        Returns:
            Optional[Dict]: 详情数据
        """
        try:
            await self._page.goto(shop_url, wait_until="networkidle", timeout=30000)
            
            # 提取推荐菜
            dishes = await self._page.evaluate("""
                () => {
                    const dishElems = document.querySelectorAll('.recommend-dish .dish-name');
                    return Array.from(dishElems).map(d => d.textContent.trim());
                }
            """)
            
            # 提取营业时间
            hours = await self._page.evaluate("""
                () => {
                    const hoursElem = document.querySelector('.shop-hours');
                    return hoursElem ? hoursElem.textContent.trim() : '';
                }
            """)
            
            return {
                'recommended_dishes': dishes,
                'business_hours': hours,
            }
            
        except Exception as e:
            self.logger.error(f"爬取详情页失败: {shop_url}, 错误: {e}")
            return None
    
    async def cleanup(self):
        """清理资源"""
        if self._page:
            await self._page.close()
            self._page = None
        
        if self._browser:
            await self._browser.close()
            self._browser = None
