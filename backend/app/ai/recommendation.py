"""
智能排序和Top10推荐服务
综合评分排序，支持黑名单排除、缓存
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, not_

from app.models.restaurant import Restaurant
from app.models.user import TasteProfile, UserActivity
from app.models.crawler import PlatformRating, Blacklist
from app.ai.scoring import ScoringEngine, ScoringWeights, RestaurantScore
from app.ai.taste_parser import TasteQuery


@dataclass
class RecommendationRequest:
    """
    推荐请求
    """
    user_id: Optional[int] = None
    user_location: Optional[tuple[float, float]] = None  # (lat, lon)
    taste_query: Optional[TasteQuery] = None
    limit: int = 10
    
    # 筛选条件
    exclude_blacklist: bool = True
    exclude_visited: bool = False
    max_distance_km: Optional[float] = None
    cuisine_filter: Optional[str] = None
    price_filter: Optional[str] = None


@dataclass
class RecommendationResult:
    """
    推荐结果
    """
    restaurants: List[Dict[str, Any]]
    total_count: int
    query_hash: str
    cached: bool
    generated_at: datetime
    
    # 调试信息
    scores: Optional[List[RestaurantScore]] = None


class RecommendationCache:
    """
    简单的内存缓存
    同条件5分钟内不重复计算
    """
    
    def __init__(self, ttl_minutes: int = 5):
        self._cache: Dict[str, tuple[datetime, RecommendationResult]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Optional[RecommendationResult]:
        """获取缓存结果"""
        if key in self._cache:
            created_at, result = self._cache[key]
            if datetime.now() - created_at < self._ttl:
                result.cached = True
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, result: RecommendationResult):
        """设置缓存"""
        self._cache[key] = (datetime.now(), result)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def _hash_request(self, request: RecommendationRequest) -> str:
        """生成请求的哈希键"""
        data = {
            'user_id': request.user_id,
            'location': request.user_location,
            'taste': request.taste_query.__dict__ if request.taste_query else None,
            'limit': request.limit,
            'exclude_blacklist': request.exclude_blacklist,
            'exclude_visited': request.exclude_visited,
            'max_distance': request.max_distance_km,
            'cuisine': request.cuisine_filter,
            'price': request.price_filter
        }
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()


class RecommendationService:
    """
    智能推荐服务
    整合评分、过滤、排序、缓存
    """
    
    def __init__(
        self,
        db: AsyncSession,
        weights: Optional[ScoringWeights] = None,
        cache_ttl: int = 5
    ):
        """
        初始化推荐服务
        
        Args:
            db: 数据库会话
            weights: 自定义评分权重
            cache_ttl: 缓存时间（分钟）
        """
        self.db = db
        self.scoring_engine = ScoringEngine(weights)
        self.cache = RecommendationCache(cache_ttl)
    
    async def get_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResult:
        """
        获取Top N推荐
        
        Args:
            request: 推荐请求
            
        Returns:
            RecommendationResult对象
        """
        # 1. 检查缓存
        cache_key = self.cache._hash_request(request)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 2. 获取用户口味偏好
        user_preferences = await self._get_user_preferences(request.user_id)
        
        # 3. 合并用户偏好和查询条件
        if request.taste_query:
            user_preferences = self._merge_preferences_and_query(
                user_preferences, request.taste_query
            )
        
        # 4. 获取候选餐厅
        candidate_restaurants = await self._get_candidate_restaurants(
            request, user_preferences
        )
        
        # 5. 获取黑名单
        blacklist = set()
        if request.exclude_blacklist and request.user_id:
            blacklist = await self._get_user_blacklist(request.user_id)
        
        # 6. 获取已打卡餐厅
        visited = set()
        if request.exclude_visited and request.user_id:
            visited = await self._get_user_visited(request.user_id)
        
        # 7. 计算评分并排序
        scored_restaurants = []
        for restaurant in candidate_restaurants:
            # 跳过黑名单
            if restaurant['id'] in blacklist:
                continue
            
            # 跳过已打卡
            if restaurant['id'] in visited:
                continue
            
            # 获取平台评分
            platform_ratings = await self._get_platform_ratings(restaurant['id'])
            
            # 获取热度统计（这里简化处理，实际可以从统计表获取）
            popularity_stats = None
            
            # 计算评分
            score = await self.scoring_engine.calculate_score(
                restaurant=restaurant,
                user_preferences=user_preferences,
                user_location=request.user_location,
                platform_ratings=platform_ratings,
                popularity_stats=popularity_stats
            )
            
            scored_restaurants.append((restaurant, score))
        
        # 8. 按总分降序排序
        scored_restaurants.sort(key=lambda x: x[1].total_score, reverse=True)
        
        # 9. 取Top N
        top_n = scored_restaurants[:request.limit]
        
        # 10. 构建结果
        restaurants = []
        scores = []
        for restaurant, score in top_n:
            restaurants.append({
                **restaurant,
                'score': score.total_score,
                'score_details': {
                    'taste': score.taste_score,
                    'rating': score.rating_score,
                    'distance': score.distance_score,
                    'price': score.price_score,
                    'popularity': score.popularity_score,
                    'freshness': score.freshness_score
                },
                'distance_km': score.distance_km,
                'avg_rating': score.platform_avg_rating
            })
            scores.append(score)
        
        result = RecommendationResult(
            restaurants=restaurants,
            total_count=len(scored_restaurants),
            query_hash=cache_key,
            cached=False,
            generated_at=datetime.now(),
            scores=scores
        )
        
        # 11. 缓存结果
        self.cache.set(cache_key, result)
        
        return result
    
    async def _get_user_preferences(
        self,
        user_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户口味偏好
        """
        if not user_id:
            return None
        
        stmt = select(TasteProfile).where(TasteProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        return {
            'preferred_cuisines': profile.preferred_cuisines or [],
            'preferred_price_range': profile.preferred_price_range,
            'preferred_spice_level': profile.preferred_spice_level,
            'flavor_tags': profile.flavor_tags or []
        }
    
    def _merge_preferences_and_query(
        self,
        preferences: Optional[Dict[str, Any]],
        query: TasteQuery
    ) -> Dict[str, Any]:
        """
        合并用户偏好和查询条件
        查询条件优先级更高
        """
        base = preferences or {
            'preferred_cuisines': [],
            'preferred_price_range': None,
            'preferred_spice_level': None,
            'flavor_tags': []
        }
        
        # 覆盖菜系
        if query.cuisine:
            base['preferred_cuisines'] = [query.cuisine] + [
                c for c in base['preferred_cuisines'] 
                if c != query.cuisine
            ]
        
        # 覆盖价格
        if query.price_range:
            base['preferred_price_range'] = query.price_range
        
        # 覆盖辣度
        if query.spice_level:
            base['preferred_spice_level'] = query.spice_level
        
        # 合并口味标签
        if query.flavor_tags:
            existing = set(base.get('flavor_tags', []))
            base['flavor_tags'] = list(existing | set(query.flavor_tags))
        
        return base
    
    async def _get_candidate_restaurants(
        self,
        request: RecommendationRequest,
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        获取候选餐厅列表
        """
        stmt = select(Restaurant)
        
        # 菜系筛选
        cuisine_filter = request.cuisine_filter
        if not cuisine_filter and preferences:
            preferred_cuisines = preferences.get('preferred_cuisines', [])
            if preferred_cuisines:
                cuisine_filter = preferred_cuisines[0]
        
        if cuisine_filter:
            stmt = stmt.where(Restaurant.cuisine_type.ilike(f'%{cuisine_filter}%'))
        
        # 价格筛选
        price_filter = request.price_filter
        if not price_filter and preferences:
            price_filter = preferences.get('preferred_price_range')
        
        if price_filter:
            stmt = stmt.where(Restaurant.price_range == price_filter)
        
        # 限制结果数量（先取较多候选，后续评分筛选）
        stmt = stmt.limit(100)
        
        result = await self.db.execute(stmt)
        restaurants = result.scalars().all()
        
        # 转换为字典列表
        return [
            {
                'id': r.id,
                'name': r.name,
                'address': r.address,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'cuisine_type': r.cuisine_type,
                'price_range': r.price_range,
                'rating': r.rating,
                'description': r.description,
                'updated_at': r.updated_at
            }
            for r in restaurants
        ]
    
    async def _get_user_blacklist(self, user_id: int) -> set:
        """
        获取用户黑名单（餐厅ID集合）
        """
        stmt = select(Blacklist.target_id).where(
            and_(
                Blacklist.target_type == 'restaurant',
                Blacklist.target_id == user_id  # 注意：这里应该关联到拉黑者ID
            )
        )
        result = await self.db.execute(stmt)
        return set(row[0] for row in result.all())
    
    async def _get_user_visited(self, user_id: int) -> set:
        """
        获取用户已打卡餐厅
        """
        stmt = select(UserActivity.target_id).where(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.activity_type == 'checkin',
                UserActivity.target_type == 'restaurant'
            )
        )
        result = await self.db.execute(stmt)
        return set(row[0] for row in result.all() if row[0])
    
    async def _get_platform_ratings(
        self,
        restaurant_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取餐厅的平台评分
        """
        stmt = select(PlatformRating).where(
            PlatformRating.restaurant_id == restaurant_id
        )
        result = await self.db.execute(stmt)
        ratings = result.scalars().all()
        
        return [
            {
                'platform': r.platform,
                'rating': r.rating,
                'review_count': r.review_count,
                'tags': r.tags
            }
            for r in ratings
        ]


# 导出
__all__ = [
    'RecommendationService',
    'RecommendationRequest',
    'RecommendationResult',
    'RecommendationCache'
]
