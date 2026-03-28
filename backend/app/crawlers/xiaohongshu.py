"""
小红书爬虫
搜索美食笔记
"""
import asyncio
import logging
import re
from typing import List, Optional, Dict
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser

from app.crawlers.base import BaseCrawler
from app.crawlers.schemas import NoteData, RestaurantData, Platform


logger = logging.getLogger(__name__)


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫
    搜索美食笔记，提取餐厅信息
    """
    
    BASE_URL = "https://www.xiaohongshu.com"
    SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}"
    
    def __init__(self):
        super().__init__(Platform.XIAOHONGSHU)
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
            
            context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.anti_crawl.get_user_agent(),
                locale='zh-CN',
            )
            
            self._page = await context.new_page()
            
            # 绕过检测
            await self._page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
    
    async def crawl(
        self,
        keyword: str = "美食",
        max_notes: int = 50,
        **kwargs
    ) -> List[NoteData]:
        """
        爬取小红书美食笔记
        
        Args:
            keyword: 搜索关键词
            max_notes: 最大笔记数量
            **kwargs: 其他参数
            
        Returns:
            List[NoteData]: 笔记数据列表
        """
        await self._init_browser()
        
        notes = []
        
        try:
            # 构建搜索URL
            url = self.SEARCH_URL.format(keyword=quote(keyword))
            
            self.logger.info(f"开始爬取: {url}")
            
            # 访问页面
            await self._page.set_extra_http_headers(
                self.anti_crawl.get_headers("xiaohongshu")
            )
            await self._page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 等待内容加载
            await self._page.wait_for_selector(".note-item", timeout=10000)
            
            # 滚动加载更多
            await self._scroll_for_more(max_notes)
            
            # 解析数据
            notes = await self.parse(self._page)
            
            # 限制数量
            notes = notes[:max_notes]
            
            self.logger.info(f"爬取完成，获取 {len(notes)} 条笔记")
            
            return notes
            
        except Exception as e:
            self.logger.error(f"爬取失败: {e}", exc_info=True)
            return notes
    
    async def _scroll_for_more(self, target_count: int):
        """
        滚动页面加载更多笔记
        
        Args:
            target_count: 目标数量
        """
        last_count = 0
        scroll_times = 0
        max_scrolls = 10  # 最多滚动10次
        
        while scroll_times < max_scrolls:
            # 滚动到底部
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 等待加载
            await asyncio.sleep(2)
            
            # 检查是否加载了新内容
            current_count = await self._page.evaluate("""
                () => document.querySelectorAll('.note-item').length
            """)
            
            if current_count >= target_count or current_count == last_count:
                break
            
            last_count = current_count
            scroll_times += 1
            
            # 随机延迟
            await self.delay(1.0, 3.0)
    
    async def parse(self, page: Page) -> List[NoteData]:
        """
        解析小红书页面
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[NoteData]: 解析后的笔记列表
        """
        notes = []
        
        try:
            # 提取笔记数据
            note_data = await page.evaluate("""
                () => {
                    const notes = [];
                    const items = document.querySelectorAll('.note-item');
                    
                    items.forEach(item => {
                        try {
                            const titleElem = item.querySelector('.title');
                            const title = titleElem ? titleElem.textContent.trim() : '';
                            
                            if (!title) return;
                            
                            const authorElem = item.querySelector('.author-name');
                            const author = authorElem ? authorElem.textContent.trim() : '';
                            
                            const likesElem = item.querySelector('.like-count');
                            const likesText = likesElem ? likesElem.textContent : '0';
                            const likes = parseInt(likesText.replace('赞', '').trim()) || 0;
                            
                            const imgElem = item.querySelector('img');
                            const imageUrl = imgElem ? imgElem.src : null;
                            
                            const linkElem = item.querySelector('a');
                            const noteUrl = linkElem ? linkElem.href : null;
                            
                            // 提取笔记ID
                            const noteId = noteUrl ? noteUrl.split('/').pop() : null;
                            
                            notes.push({
                                title, author, likes, imageUrl, noteUrl, noteId
                            });
                        } catch (e) {
                            console.error('解析笔记失败:', e);
                        }
                    });
                    
                    return notes;
                }
            """)
            
            # 转换为NoteData
            for note in note_data:
                # 提取餐厅名称（从标题中）
                mentioned_restaurants = self._extract_restaurant_names(note['title'])
                
                note_obj = NoteData(
                    title=note['title'],
                    author=note.get('author', ''),
                    likes=note.get('likes', 0),
                    images=[note['imageUrl']] if note.get('imageUrl') else [],
                    platform=Platform.XIAOHONGSHU,
                    platform_id=note.get('noteId'),
                    platform_url=note.get('noteUrl'),
                    mentioned_restaurants=mentioned_restaurants,
                )
                
                notes.append(note_obj)
            
        except Exception as e:
            self.logger.error(f"解析页面失败: {e}", exc_info=True)
        
        return notes
    
    def _extract_restaurant_names(self, title: str) -> List[str]:
        """
        从标题中提取餐厅名称
        使用简单的启发式规则
        
        Args:
            title: 笔记标题
            
        Returns:
            List[str]: 提取的餐厅名称列表
        """
        restaurants = []
        
        # 常见模式：店名、餐厅、店、火锅等
        patterns = [
            r'【(.+?)】',  # 【店名】
            r'「(.+?)」',  # 「店名」
            r'《(.+?)》',  # 《店名》
            r'([^，。！？]+(?:店|餐厅|馆|楼|居|坊|轩|阁|厅))',  # 包含关键词
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, title)
            restaurants.extend(matches)
        
        # 去重
        return list(set(restaurants))
    
    async def crawl_note_detail(self, note_url: str) -> Optional[Dict]:
        """
        爬取笔记详情
        
        Args:
            note_url: 笔记URL
            
        Returns:
            Optional[Dict]: 详情数据
        """
        try:
            await self._page.goto(note_url, wait_until="networkidle", timeout=30000)
            
            # 提取内容
            detail = await self._page.evaluate("""
                () => {
                    const contentElem = document.querySelector('.note-content');
                    const content = contentElem ? contentElem.textContent.trim() : '';
                    
                    const collectElem = document.querySelector('.collect-count');
                    const collectsText = collectElem ? collectElem.textContent : '0';
                    const collects = parseInt(collectsText) || 0;
                    
                    const commentElem = document.querySelector('.comment-count');
                    const commentsText = commentElem ? commentElem.textContent : '0';
                    const comments = parseInt(commentsText) || 0;
                    
                    const tagElems = document.querySelectorAll('.tag');
                    const tags = Array.from(tagElems).map(t => t.textContent.trim().replace('#', ''));
                    
                    const imgElems = document.querySelectorAll('.note-image img');
                    const images = Array.from(imgElems).map(img => img.src);
                    
                    return {
                        content, collects, comments, tags, images
                    };
                }
            """)
            
            return detail
            
        except Exception as e:
            self.logger.error(f"爬取笔记详情失败: {note_url}, 错误: {e}")
            return None
    
    async def search_restaurants(
        self,
        restaurant_name: str,
        max_notes: int = 20
    ) -> List[NoteData]:
        """
        搜索特定餐厅的笔记
        
        Args:
            restaurant_name: 餐厅名称
            max_notes: 最大笔记数
            
        Returns:
            List[NoteData]: 笔记列表
        """
        keyword = f"{restaurant_name} 美食"
        return await self.crawl(keyword=keyword, max_notes=max_notes)
    
    async def cleanup(self):
        """清理资源"""
        if self._page:
            await self._page.close()
            self._page = None
        
        if self._browser:
            await self._browser.close()
            self._browser = None
