"""
数据清洗和去重
"""
import logging
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from collections import defaultdict

from app.crawlers.schemas import RestaurantData, Platform


logger = logging.getLogger(__name__)


class DataCleaner:
    """
    数据清洗器
    跨平台餐厅名称模糊匹配、数据合并、去重、标准化
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.8,
        min_name_length: int = 2
    ):
        """
        初始化数据清洗器
        
        Args:
            similarity_threshold: 名称相似度阈值
            min_name_length: 最小名称长度
        """
        self.similarity_threshold = similarity_threshold
        self.min_name_length = min_name_length
        self.logger = logging.getLogger(__name__)
    
    def clean(self, data: List[RestaurantData]) -> List[RestaurantData]:
        """
        清洗数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            List[RestaurantData]: 清洗后的数据列表
        """
        if not data:
            return []
        
        self.logger.info(f"开始清洗数据，原始数量: {len(data)}")
        
        # 1. 基础清洗
        cleaned = []
        for item in data:
            if self._is_valid(item):
                cleaned_item = self._clean_item(item)
                cleaned.append(cleaned_item)
        
        self.logger.info(f"基础清洗完成，有效数据: {len(cleaned)}")
        
        # 2. 去重
        deduplicated = self._deduplicate(cleaned)
        
        self.logger.info(f"去重完成，最终数量: {len(deduplicated)}")
        
        return deduplicated
    
    def _is_valid(self, item: RestaurantData) -> bool:
        """
        检查数据是否有效
        
        Args:
            item: 餐厅数据
            
        Returns:
            bool: 是否有效
        """
        # 名称不能为空
        if not item.name or len(item.name.strip()) < self.min_name_length:
            return False
        
        # 评分范围检查
        if item.rating is not None and (item.rating < 0 or item.rating > 5):
            self.logger.warning(f"异常评分: {item.name} - {item.rating}")
            return False
        
        # 价格检查
        if item.avg_price is not None and item.avg_price < 0:
            self.logger.warning(f"异常价格: {item.name} - {item.avg_price}")
            return False
        
        return True
    
    def _clean_item(self, item: RestaurantData) -> RestaurantData:
        """
        清洗单条数据
        
        Args:
            item: 餐厅数据
            
        Returns:
            RestaurantData: 清洗后的数据
        """
        # 标准化名称
        item.name = self._normalize_name(item.name)
        
        # 清洗地址
        if item.address:
            item.address = self._clean_address(item.address)
        
        # 清洗电话
        if item.phone:
            item.phone = self._clean_phone(item.phone)
        
        # 标准化价格区间
        if item.avg_price:
            item.price_range = self._calculate_price_range(item.avg_price)
        
        # 清洗标签
        if item.tags:
            item.tags = [tag.strip() for tag in item.tags if tag and tag.strip()]
        
        return item
    
    def _normalize_name(self, name: str) -> str:
        """
        标准化餐厅名称
        
        Args:
            name: 原始名称
            
        Returns:
            str: 标准化后的名称
        """
        # 去除多余空格
        name = ' '.join(name.split())
        
        # 去除常见后缀（保留核心名称）
        # 但不修改原始名称，只用于匹配
        return name.strip()
    
    def _clean_address(self, address: str) -> str:
        """
        清洗地址
        
        Args:
            address: 原始地址
            
        Returns:
            str: 清洗后的地址
        """
        # 去除多余空格
        address = ' '.join(address.split())
        
        # 去除特殊字符
        address = re.sub(r'[^\w\s\u4e00-\u9fff#\-(),]', '', address)
        
        return address.strip()
    
    def _clean_phone(self, phone: str) -> str:
        """
        清洗电话号码
        
        Args:
            phone: 原始电话
            
        Returns:
            str: 清洗后的电话
        """
        # 只保留数字和横杠
        phone = re.sub(r'[^\d\-]', '', phone)
        
        # 如果有多个号码，取第一个
        if ';' in phone:
            phone = phone.split(';')[0]
        
        return phone.strip()
    
    def _calculate_price_range(self, avg_price: float) -> str:
        """
        计算价格区间
        
        Args:
            avg_price: 人均价格
            
        Returns:
            str: 价格区间符号
        """
        if avg_price < 30:
            return "¥"
        elif avg_price < 80:
            return "¥¥"
        elif avg_price < 150:
            return "¥¥¥"
        else:
            return "¥¥¥¥"
    
    def _deduplicate(self, data: List[RestaurantData]) -> List[RestaurantData]:
        """
        去重
        
        Args:
            data: 数据列表
            
        Returns:
            List[RestaurantData]: 去重后的数据
        """
        if not data:
            return []
        
        # 分组：按平台
        by_platform = defaultdict(list)
        for item in data:
            by_platform[item.platform].append(item)
        
        # 跨平台匹配
        merged = []
        used_indices = set()
        
        for i, item1 in enumerate(data):
            if i in used_indices:
                continue
            
            # 找到相似的其他餐厅
            similar_items = [item1]
            
            for j, item2 in enumerate(data):
                if i != j and j not in used_indices:
                    if self._is_similar(item1, item2):
                        similar_items.append(item2)
                        used_indices.add(j)
            
            # 合并相似餐厅的数据
            if len(similar_items) > 1:
                merged_item = self._merge_similar(similar_items)
                merged.append(merged_item)
            else:
                merged.append(item1)
            
            used_indices.add(i)
        
        return merged
    
    def _is_similar(self, item1: RestaurantData, item2: RestaurantData) -> bool:
        """
        判断两个餐厅是否相似（可能是同一家）
        
        Args:
            item1: 餐厅1
            item2: 餐厅2
            
        Returns:
            bool: 是否相似
        """
        # 名称相似度
        name_similarity = self._calculate_similarity(item1.name, item2.name)
        
        if name_similarity < self.similarity_threshold:
            return False
        
        # 如果名称相似，再检查地址
        if item1.address and item2.address:
            addr_similarity = self._calculate_similarity(item1.address, item2.address)
            # 地址也要有一定相似度
            if addr_similarity < 0.5:
                return False
        
        return True
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算字符串相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            float: 相似度（0-1）
        """
        # 使用SequenceMatcher计算编辑距离相似度
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _merge_similar(self, items: List[RestaurantData]) -> RestaurantData:
        """
        合并相似的餐厅数据
        
        Args:
            items: 相似餐厅列表
            
        Returns:
            RestaurantData: 合并后的数据
        """
        if not items:
            raise ValueError("Empty items list")
        
        if len(items) == 1:
            return items[0]
        
        # 选择最完整的记录作为基础
        base = max(items, key=self._completeness_score)
        
        # 合并各个字段
        platforms = [item.platform for item in items]
        ratings = [item.rating for item in items if item.rating is not None]
        review_counts = [item.review_count for item in items if item.review_count > 0]
        avg_prices = [item.avg_price for item in items if item.avg_price is not None]
        
        # 计算综合评分
        if ratings:
            # 加权平均（按评论数加权）
            if review_counts:
                total_weight = sum(review_counts)
                weighted_rating = sum(
                    r * c for r, c in zip(ratings, review_counts)
                ) / total_weight
                base.rating = round(weighted_rating, 1)
            else:
                base.rating = round(sum(ratings) / len(ratings), 1)
        
        # 合并评论数
        if review_counts:
            base.review_count = sum(review_counts)
        
        # 合并价格
        if avg_prices:
            base.avg_price = round(sum(avg_prices) / len(avg_prices), 2)
        
        # 合并标签
        all_tags = set()
        for item in items:
            if item.tags:
                all_tags.update(item.tags)
        base.tags = list(all_tags) if all_tags else None
        
        # 合并图片
        all_images = []
        for item in items:
            if item.images:
                all_images.extend(item.images)
        if all_images:
            base.images = list(set(all_images))
        
        # 标记为多平台数据
        if len(platforms) > 1:
            base.platform_source = "multi"
        
        # 保存原始数据引用
        base.raw_data = {
            "merged_from": [item.platform for item in items],
            "merge_count": len(items)
        }
        
        return base
    
    def _completeness_score(self, item: RestaurantData) -> int:
        """
        计算数据完整度得分
        
        Args:
            item: 餐厅数据
            
        Returns:
            int: 得分
        """
        score = 0
        
        if item.name:
            score += 10
        if item.address:
            score += 8
        if item.rating:
            score += 7
        if item.phone:
            score += 6
        if item.image_url:
            score += 5
        if item.latitude and item.longitude:
            score += 5
        if item.avg_price:
            score += 4
        if item.tags:
            score += len(item.tags)
        if item.business_hours:
            score += 3
        
        return score


class RestaurantMatcher:
    """
    餐厅匹配器
    用于跨平台识别同一餐厅
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def find_matches(
        self,
        restaurants: List[RestaurantData],
        threshold: float = 0.8
    ) -> List[List[int]]:
        """
        找出相似的餐厅组
        
        Args:
            restaurants: 餐厅列表
            threshold: 相似度阈值
            
        Returns:
            List[List[int]]: 相似餐厅的索引组
        """
        n = len(restaurants)
        if n == 0:
            return []
        
        # 使用并查集
        parent = list(range(n))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 两两比较
        for i in range(n):
            for j in range(i + 1, n):
                if self._is_match(restaurants[i], restaurants[j], threshold):
                    union(i, j)
        
        # 分组
        groups = defaultdict(list)
        for i in range(n):
            groups[find(i)].append(i)
        
        return list(groups.values())
    
    def _is_match(
        self,
        r1: RestaurantData,
        r2: RestaurantData,
        threshold: float
    ) -> bool:
        """
        判断两个餐厅是否匹配
        """
        # 名称相似度
        name_sim = SequenceMatcher(None, r1.name, r2.name).ratio()
        if name_sim < threshold:
            return False
        
        # 地址相似度（如果都有地址）
        if r1.address and r2.address:
            addr_sim = SequenceMatcher(None, r1.address, r2.address).ratio()
            if addr_sim < 0.5:
                return False
        
        # 坐标距离（如果都有坐标）
        if (r1.latitude and r1.longitude and 
            r2.latitude and r2.longitude):
            distance = self._calculate_distance(
                r1.latitude, r1.longitude,
                r2.latitude, r2.longitude
            )
            # 距离超过500米认为不是同一家
            if distance > 500:
                return False
        
        return True
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        计算两点间距离（米）
        使用Haversine公式
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # 地球半径（米）
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
