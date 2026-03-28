"""
餐厅评分算法
多维度评分引擎，支持可配置权重
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import math


@dataclass
class ScoringWeights:
    """
    评分权重配置
    所有权重之和应为1.0
    """
    taste_match: float = 0.30      # 口味匹配度
    platform_rating: float = 0.30   # 平台评分
    distance: float = 0.15          # 距离分数
    price_match: float = 0.10       # 价格匹配度
    popularity: float = 0.10        # 热度
    freshness: float = 0.05         # 新鲜度（数据更新时间）
    
    def __post_init__(self):
        """自动验证权重之和是否为1.0"""
        if not self.validate():
            total = (
                self.taste_match + self.platform_rating + 
                self.distance + self.price_match + 
                self.popularity + self.freshness
            )
            raise ValueError(f"权重之和必须为1.0，当前为{total:.2f}")
    
    def validate(self) -> bool:
        """验证权重之和是否为1.0"""
        total = (
            self.taste_match + self.platform_rating + 
            self.distance + self.price_match + 
            self.popularity + self.freshness
        )
        return abs(total - 1.0) < 0.01


@dataclass
class RestaurantScore:
    """
    餐厅评分结果
    """
    restaurant_id: int
    total_score: float  # 总分 0-1
    taste_score: float  # 口味匹配分 0-1
    rating_score: float  # 平台评分 0-1
    distance_score: float  # 距离分 0-1
    price_score: float  # 价格匹配分 0-1
    popularity_score: float  # 热度分 0-1
    freshness_score: float  # 新鲜度分 0-1
    
    # 详细信息
    distance_km: Optional[float] = None
    platform_avg_rating: Optional[float] = None
    review_count: int = 0


class ScoringEngine:
    """
    多维度餐厅评分引擎
    各维度归一化到0-1，加权计算总分
    """
    
    # 价格区间映射到数值（用于计算匹配度）
    PRICE_LEVELS = {
        '¥': 1, '¥¥': 2, '¥¥¥': 3, '¥¥¥¥': 4
    }
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        """
        初始化评分引擎
        
        Args:
            weights: 自定义权重配置，默认使用标准权重
        """
        self.weights = weights or ScoringWeights()
        if not self.weights.validate():
            raise ValueError("权重之和必须为1.0")
    
    async def calculate_score(
        self,
        restaurant: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        user_location: Optional[tuple[float, float]] = None,
        platform_ratings: Optional[List[Dict[str, Any]]] = None,
        popularity_stats: Optional[Dict[str, Any]] = None
    ) -> RestaurantScore:
        """
        计算单个餐厅的综合评分
        
        Args:
            restaurant: 餐厅信息字典
            user_preferences: 用户口味偏好
            user_location: 用户位置 (lat, lon)
            platform_ratings: 平台评分列表
            popularity_stats: 热度统计信息
            
        Returns:
            RestaurantScore对象
        """
        restaurant_id = restaurant.get('id', 0)
        
        # 1. 计算口味匹配度
        taste_score = await self._calculate_taste_score(
            restaurant, user_preferences
        )
        
        # 2. 计算平台评分
        rating_score, avg_rating, review_count = await self._calculate_rating_score(
            platform_ratings, restaurant.get('rating')
        )
        
        # 3. 计算距离分数
        distance_score, distance_km = await self._calculate_distance_score(
            restaurant.get('latitude'),
            restaurant.get('longitude'),
            user_location
        )
        
        # 4. 计算价格匹配度
        price_score = await self._calculate_price_score(
            restaurant.get('price_range'),
            user_preferences.get('preferred_price_range') if user_preferences else None
        )
        
        # 5. 计算热度分数
        popularity_score = await self._calculate_popularity_score(
            popularity_stats
        )
        
        # 6. 计算新鲜度分数
        freshness_score = await self._calculate_freshness_score(
            restaurant.get('updated_at')
        )
        
        # 加权计算总分
        total_score = (
            taste_score * self.weights.taste_match +
            rating_score * self.weights.platform_rating +
            distance_score * self.weights.distance +
            price_score * self.weights.price_match +
            popularity_score * self.weights.popularity +
            freshness_score * self.weights.freshness
        )
        
        return RestaurantScore(
            restaurant_id=restaurant_id,
            total_score=round(total_score, 4),
            taste_score=round(taste_score, 4),
            rating_score=round(rating_score, 4),
            distance_score=round(distance_score, 4),
            price_score=round(price_score, 4),
            popularity_score=round(popularity_score, 4),
            freshness_score=round(freshness_score, 4),
            distance_km=round(distance_km, 2) if distance_km else None,
            platform_avg_rating=round(avg_rating, 2) if avg_rating else None,
            review_count=review_count
        )
    
    async def _calculate_taste_score(
        self,
        restaurant: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算口味匹配度
        基于菜系偏好、口味标签、辣度偏好
        """
        if not user_preferences:
            return 0.5  # 无偏好信息，返回中等分数
        
        score = 0.0
        max_score = 3.0
        
        # 1. 菜系匹配（权重最高）
        restaurant_cuisine = restaurant.get('cuisine_type', '')
        preferred_cuisines = user_preferences.get('preferred_cuisines', [])
        if preferred_cuisines and restaurant_cuisine:
            if restaurant_cuisine in preferred_cuisines:
                score += 1.5  # 菜系完全匹配
            elif any(c in restaurant_cuisine or restaurant_cuisine in c 
                    for c in preferred_cuisines):
                score += 0.8  # 部分匹配
        
        # 2. 辣度匹配
        restaurant_spice = self._estimate_spice_level(restaurant_cuisine)
        user_spice = user_preferences.get('preferred_spice_level', 3)
        if restaurant_spice:
            spice_diff = abs(restaurant_spice - user_spice)
            score += max(0, 1.0 - spice_diff * 0.2)  # 差异越小分数越高
        
        # 3. 口味标签匹配
        user_flavor_tags = set(user_preferences.get('flavor_tags', []))
        restaurant_tags = self._extract_restaurant_tags(restaurant)
        if user_flavor_tags and restaurant_tags:
            overlap = len(user_flavor_tags & restaurant_tags)
            total = len(user_flavor_tags)
            score += overlap / total if total > 0 else 0
        
        # 归一化到0-1
        return min(score / max_score, 1.0)
    
    async def _calculate_rating_score(
        self,
        platform_ratings: Optional[List[Dict[str, Any]]],
        restaurant_rating: Optional[float]
    ) -> tuple[float, Optional[float], int]:
        """
        计算平台评分
        返回：(归一化分数, 平均评分, 总评论数)
        """
        if platform_ratings:
            # 聚合多平台评分
            ratings = [r.get('rating', 0) for r in platform_ratings if r.get('rating')]
            review_counts = [r.get('review_count', 0) for r in platform_ratings]
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                total_reviews = sum(review_counts)
                
                # 评分归一化（假设评分范围1-5）
                normalized = (avg_rating - 1) / 4.0
                
                # 评论数加成（评论越多越可信）
                review_bonus = min(total_reviews / 1000, 0.1)
                
                return min(normalized + review_bonus, 1.0), avg_rating, total_reviews
        
        # 使用餐厅自身评分
        if restaurant_rating:
            return (restaurant_rating - 1) / 4.0, restaurant_rating, 0
        
        return 0.5, None, 0  # 无评分信息，返回中等分数
    
    async def _calculate_distance_score(
        self,
        restaurant_lat: Optional[float],
        restaurant_lon: Optional[float],
        user_location: Optional[tuple[float, float]]
    ) -> tuple[float, Optional[float]]:
        """
        计算距离分数
        返回：(归一化分数, 距离km)
        """
        if not user_location or not restaurant_lat or not restaurant_lon:
            return 0.5, None  # 无位置信息，返回中等分数
        
        # 计算距离（Haversine公式）
        distance_km = self._haversine_distance(
            user_location[0], user_location[1],
            restaurant_lat, restaurant_lon
        )
        
        # 距离分数归一化（3km内高分，之后快速衰减）
        if distance_km <= 0.5:
            score = 1.0
        elif distance_km <= 1.0:
            score = 0.9
        elif distance_km <= 2.0:
            score = 0.8
        elif distance_km <= 3.0:
            score = 0.7
        elif distance_km <= 5.0:
            score = 0.5
        elif distance_km <= 10.0:
            score = 0.3
        else:
            score = 0.1
        
        return score, distance_km
    
    async def _calculate_price_score(
        self,
        restaurant_price: Optional[str],
        preferred_price: Optional[str]
    ) -> float:
        """
        计算价格匹配度
        """
        if not preferred_price or not restaurant_price:
            return 0.5  # 无价格偏好，返回中等分数
        
        user_level = self.PRICE_LEVELS.get(preferred_price, 2)
        restaurant_level = self.PRICE_LEVELS.get(restaurant_price, 2)
        
        # 价格差异越小，分数越高
        diff = abs(user_level - restaurant_level)
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        else:
            return max(0.3, 1.0 - diff * 0.25)
    
    async def _calculate_popularity_score(
        self,
        popularity_stats: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算热度分数
        基于收藏数、打卡数、评论数等
        """
        if not popularity_stats:
            return 0.5  # 无热度信息，返回中等分数
        
        favorite_count = popularity_stats.get('favorite_count', 0)
        checkin_count = popularity_stats.get('checkin_count', 0)
        note_count = popularity_stats.get('note_count', 0)
        
        # 加权热度分数
        total_popularity = (
            favorite_count * 1.0 +
            checkin_count * 0.8 +
            note_count * 0.5
        )
        
        # 归一化（假设1000为一个热度单位）
        return min(total_popularity / 1000, 1.0)
    
    async def _calculate_freshness_score(
        self,
        updated_at: Optional[datetime]
    ) -> float:
        """
        计算数据新鲜度分数
        数据越新，分数越高
        """
        if not updated_at:
            return 0.5  # 无更新时间，返回中等分数
        
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except:
                return 0.5
        
        # 计算距今天数
        days_old = (datetime.now(updated_at.tzinfo) - updated_at).days
        
        # 新鲜度衰减
        if days_old <= 7:
            return 1.0
        elif days_old <= 30:
            return 0.8
        elif days_old <= 90:
            return 0.6
        elif days_old <= 180:
            return 0.4
        else:
            return 0.2
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        使用Haversine公式计算两点间的球面距离（km）
        """
        R = 6371  # 地球半径（km）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _estimate_spice_level(self, cuisine: str) -> Optional[int]:
        """
        根据菜系估算辣度
        """
        spicy_cuisines = ['Sichuan', 'Hunan', 'Hotpot', 'BBQ']
        mild_cuisines = ['Cantonese', 'Japanese', 'Jiangzhe']
        
        cuisine_lower = cuisine.lower() if cuisine else ''
        
        if any(c.lower() in cuisine_lower for c in spicy_cuisines):
            return 4
        elif any(c.lower() in cuisine_lower for c in mild_cuisines):
            return 1
        return 3  # 默认中等
    
    def _extract_restaurant_tags(self, restaurant: Dict[str, Any]) -> set:
        """
        从餐厅信息中提取口味标签
        """
        tags = set()
        
        cuisine = restaurant.get('cuisine_type', '')
        if '川' in cuisine or '辣' in cuisine:
            tags.add('spicy')
        if '粤' in cuisine or '广' in cuisine:
            tags.add('light')
        if '日' in cuisine:
            tags.add('fresh')
        if '甜' in cuisine or '甜品' in cuisine:
            tags.add('sweet')
        
        description = restaurant.get('description', '')
        if '清淡' in description:
            tags.add('light')
        if '麻辣' in description:
            tags.add('spicy')
        if '酸' in description:
            tags.add('sour')
        
        return tags


# 导出
__all__ = ['ScoringEngine', 'ScoringWeights', 'RestaurantScore']
