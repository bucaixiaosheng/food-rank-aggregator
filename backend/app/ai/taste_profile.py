"""
AI口味画像引擎
分析用户历史行为，生成口味画像
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.user import User, TasteProfile, UserActivity
from app.models.restaurant import Restaurant


@dataclass
class TasteRadar:
    """
    口味雷达图数据（6维度）
    """
    spicy: float = 0.0     # 辣 0-1
    sweet: float = 0.0     # 甜 0-1
    sour: float = 0.0      # 酸 0-1
    salty: float = 0.0     # 咸 0-1
    fresh: float = 0.0     # 鲜 0-1
    light: float = 0.0     # 清淡 0-1
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'spicy': self.spicy,
            'sweet': self.sweet,
            'sour': self.sour,
            'salty': self.salty,
            'fresh': self.fresh,
            'light': self.light
        }


@dataclass
class TasteLabel:
    """
    口味画像标签
    """
    name: str
    confidence: float  # 置信度 0-1
    description: str
    icon: str = ""


@dataclass
class TasteProfileResult:
    """
    口味画像结果
    """
    user_id: int
    radar: TasteRadar
    labels: List[TasteLabel] = field(default_factory=list)
    preferred_cuisines: List[str] = field(default_factory=list)
    preferred_price_range: Optional[str] = None
    preferred_spice_level: int = 3
    flavor_tags: List[str] = field(default_factory=list)
    behavior_stats: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)


class TasteProfileEngine:
    """
    AI口味画像引擎
    分析用户历史行为，生成口味画像
    """
    
    # 预定义的口味标签模板
    LABEL_TEMPLATES = [
        {
            'name': '辣王',
            'condition': lambda r: r.spicy >= 0.7,
            'description': '无辣不欢，越辣越过瘾',
            'icon': '🌶️'
        },
        {
            'name': '日料控',
            'condition': lambda cuisines: 'Japanese' in cuisines,
            'description': '深爱日本料理的精致',
            'icon': '🍣'
        },
        {
            'name': '甜品爱好者',
            'condition': lambda r: r.sweet >= 0.6,
            'description': '甜食让我快乐',
            'icon': '🍰'
        },
        {
            'name': '清淡党',
            'condition': lambda r: r.light >= 0.7,
            'description': '追求清淡健康的口味',
            'icon': '🥗'
        },
        {
            'name': '肉食动物',
            'condition': lambda cuisines: any(c in cuisines for c in ['BBQ', 'Hotpot', 'Western']),
            'description': '无肉不欢的干饭人',
            'icon': '🥩'
        },
        {
            'name': '重口味',
            'condition': lambda r: r.salty >= 0.7 and r.spicy >= 0.5,
            'description': '喜欢重口味刺激',
            'icon': '🔥'
        },
        {
            'name': '养生达人',
            'condition': lambda r: r.light >= 0.6 and r.fresh >= 0.5,
            'description': '注重健康养生',
            'icon': '🍵'
        },
        {
            'name': '美食探险家',
            'condition': lambda count: count >= 10,
            'description': '勇于尝试各种美食',
            'icon': '🧭'
        }
    ]
    
    # 菜系到口味的映射
    CUISINE_TO_TASTE = {
        'Sichuan': {'spicy': 0.9, 'salty': 0.6},
        'Hunan': {'spicy': 0.85, 'salty': 0.5, 'sour': 0.3},
        'Cantonese': {'light': 0.8, 'fresh': 0.7, 'sweet': 0.3},
        'Japanese': {'fresh': 0.8, 'light': 0.7},
        'Korean': {'spicy': 0.6, 'sour': 0.4, 'salty': 0.5},
        'Western': {'salty': 0.7, 'sweet': 0.4},
        'Hotpot': {'spicy': 0.7, 'salty': 0.6},
        'BBQ': {'salty': 0.8, 'spicy': 0.5},
        'Jiangzhe': {'sweet': 0.6, 'fresh': 0.5, 'light': 0.6},
        'Dessert': {'sweet': 0.95}
    }
    
    # 搜索关键词到口味的映射
    KEYWORD_TO_TASTE = {
        '辣': {'spicy': 0.9},
        '麻辣': {'spicy': 0.95, 'salty': 0.5},
        '清淡': {'light': 0.9},
        '甜': {'sweet': 0.9},
        '甜品': {'sweet': 0.95},
        '酸': {'sour': 0.9},
        '鲜': {'fresh': 0.9},
        '咸': {'salty': 0.8},
        '养生': {'light': 0.8, 'fresh': 0.7},
        '重口': {'salty': 0.9, 'spicy': 0.7}
    }
    
    def __init__(self, db: AsyncSession):
        """
        初始化口味画像引擎
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def generate_profile(
        self,
        user_id: int,
        time_window_days: int = 90
    ) -> TasteProfileResult:
        """
        生成用户口味画像
        
        Args:
            user_id: 用户ID
            time_window_days: 分析的时间窗口（天数）
            
        Returns:
            TasteProfileResult对象
        """
        # 1. 获取用户行为数据
        activities = await self._get_user_activities(user_id, time_window_days)
        
        # 2. 分析行为数据
        behavior_stats = await self._analyze_behaviors(activities)
        
        # 3. 计算雷达图
        radar = self._calculate_radar(behavior_stats)
        
        # 4. 生成口味标签
        labels = self._generate_labels(radar, behavior_stats)
        
        # 5. 提取偏好菜系
        preferred_cuisines = behavior_stats.get('top_cuisines', [])[:5]
        
        # 6. 提取价格偏好
        preferred_price = behavior_stats.get('top_price_range')
        
        # 7. 计算辣度偏好
        spice_level = self._calculate_spice_level(radar)
        
        # 8. 提取口味标签
        flavor_tags = self._extract_flavor_tags(radar)
        
        return TasteProfileResult(
            user_id=user_id,
            radar=radar,
            labels=labels,
            preferred_cuisines=preferred_cuisines,
            preferred_price_range=preferred_price,
            preferred_spice_level=spice_level,
            flavor_tags=flavor_tags,
            behavior_stats=behavior_stats,
            updated_at=datetime.now()
        )
    
    async def update_profile_async(self, user_id: int):
        """
        异步更新用户口味画像
        在用户行为后调用
        
        Args:
            user_id: 用户ID
        """
        # 生成新的画像
        profile_result = await self.generate_profile(user_id)
        
        # 更新数据库
        await self._save_profile(profile_result)
    
    async def _get_user_activities(
        self,
        user_id: int,
        days: int
    ) -> List[UserActivity]:
        """
        获取用户行为记录
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = select(UserActivity).where(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.created_at >= cutoff_date
            )
        ).order_by(UserActivity.created_at.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def _analyze_behaviors(
        self,
        activities: List[UserActivity]
    ) -> Dict[str, Any]:
        """
        分析用户行为数据
        """
        stats = {
            'search_keywords': Counter(),
            'favorite_cuisines': Counter(),
            'favorite_restaurants': [],
            'checkin_cuisines': Counter(),
            'top_cuisines': [],
            'top_price_range': None,
            'total_activities': len(activities),
            'unique_restaurants': set()
        }
        
        for activity in activities:
            if activity.activity_type == 'search' and activity.content:
                # 统计搜索关键词
                stats['search_keywords'][activity.content] += 1
            
            elif activity.activity_type == 'favorite' and activity.target_id:
                stats['unique_restaurants'].add(activity.target_id)
                # 查询餐厅的菜系
                restaurant = await self._get_restaurant(activity.target_id)
                if restaurant and restaurant.cuisine_type:
                    stats['favorite_cuisines'][restaurant.cuisine_type] += 1
                    stats['favorite_restaurants'].append(restaurant.id)
            
            elif activity.activity_type == 'checkin' and activity.target_id:
                stats['unique_restaurants'].add(activity.target_id)
                restaurant = await self._get_restaurant(activity.target_id)
                if restaurant and restaurant.cuisine_type:
                    stats['checkin_cuisines'][restaurant.cuisine_type] += 1
        
        # 合并菜系偏好（收藏+打卡）
        combined_cuisines = Counter()
        combined_cuisines.update(stats['favorite_cuisines'])
        combined_cuisines.update(stats['checkin_cuisines'])
        
        stats['top_cuisines'] = [
            cuisine for cuisine, count in combined_cuisines.most_common(10)
        ]
        
        # 确定价格偏好
        # 这里简化处理，实际可以查询餐厅价格分布
        if stats['favorite_restaurants']:
            stats['top_price_range'] = '¥¥'  # 默认中等
        
        return stats
    
    def _calculate_radar(self, behavior_stats: Dict[str, Any]) -> TasteRadar:
        """
        计算口味雷达图数据
        """
        radar = TasteRadar()
        
        # 基于搜索关键词计算
        search_keywords = behavior_stats.get('search_keywords', {})
        keyword_scores = {dim: 0.0 for dim in ['spicy', 'sweet', 'sour', 'salty', 'fresh', 'light']}
        keyword_count = 0
        
        for keyword, count in search_keywords.items():
            for pattern, taste_scores in self.KEYWORD_TO_TASTE.items():
                if pattern in keyword:
                    for dim, score in taste_scores.items():
                        keyword_scores[dim] += score * count
                    keyword_count += count
                    break
        
        if keyword_count > 0:
            for dim in keyword_scores:
                keyword_scores[dim] = min(keyword_scores[dim] / keyword_count, 1.0)
        
        # 基于菜系偏好计算
        top_cuisines = behavior_stats.get('top_cuisines', [])
        cuisine_scores = {dim: 0.0 for dim in ['spicy', 'sweet', 'sour', 'salty', 'fresh', 'light']}
        
        for cuisine in top_cuisines[:5]:
            if cuisine in self.CUISINE_TO_TASTE:
                taste_map = self.CUISINE_TO_TASTE[cuisine]
                for dim, score in taste_map.items():
                    cuisine_scores[dim] += score
        
        if top_cuisines:
            for dim in cuisine_scores:
                cuisine_scores[dim] = min(cuisine_scores[dim] / min(len(top_cuisines), 5), 1.0)
        
        # 合并两种来源的分数（关键词权重更高）
        final_scores = {}
        for dim in ['spicy', 'sweet', 'sour', 'salty', 'fresh', 'light']:
            if keyword_count > 0:
                final_scores[dim] = keyword_scores[dim] * 0.6 + cuisine_scores[dim] * 0.4
            else:
                final_scores[dim] = cuisine_scores[dim]
        
        # 更新雷达图
        radar.spicy = round(final_scores['spicy'], 2)
        radar.sweet = round(final_scores['sweet'], 2)
        radar.sour = round(final_scores['sour'], 2)
        radar.salty = round(final_scores['salty'], 2)
        radar.fresh = round(final_scores['fresh'], 2)
        radar.light = round(final_scores['light'], 2)
        
        return radar
    
    def _generate_labels(
        self,
        radar: TasteRadar,
        behavior_stats: Dict[str, Any]
    ) -> List[TasteLabel]:
        """
        生成口味画像标签
        """
        labels = []
        top_cuisines = behavior_stats.get('top_cuisines', [])
        unique_count = len(behavior_stats.get('unique_restaurants', set()))
        
        for template in self.LABEL_TEMPLATES:
            matched = False
            confidence = 0.0
            
            # 检查雷达条件
            if 'condition' in template:
                import inspect
                sig = inspect.signature(template['condition'])
                params = list(sig.parameters.keys())
                
                if params and params[0] == 'r':
                    # 雷达条件
                    if template['condition'](radar):
                        matched = True
                        # 置信度基于雷达值
                        attr = params[0]
                        confidence = 0.8
                
                elif params and params[0] == 'cuisines':
                    # 菜系条件
                    if template['condition'](top_cuisines):
                        matched = True
                        confidence = 0.9
                
                elif params and params[0] == 'count':
                    # 数量条件
                    if template['condition'](unique_count):
                        matched = True
                        confidence = 0.7
            
            if matched:
                labels.append(TasteLabel(
                    name=template['name'],
                    confidence=confidence,
                    description=template['description'],
                    icon=template['icon']
                ))
        
        # 按置信度排序，最多返回5个标签
        labels.sort(key=lambda x: x.confidence, reverse=True)
        return labels[:5]
    
    def _calculate_spice_level(self, radar: TasteRadar) -> int:
        """
        计算辣度偏好（1-5）
        """
        if radar.spicy >= 0.8:
            return 5
        elif radar.spicy >= 0.6:
            return 4
        elif radar.spicy >= 0.4:
            return 3
        elif radar.spicy >= 0.2:
            return 2
        else:
            return 1
    
    def _extract_flavor_tags(self, radar: TasteRadar) -> List[str]:
        """
        提取口味标签
        """
        tags = []
        
        if radar.spicy >= 0.5:
            tags.append('spicy')
        if radar.sweet >= 0.5:
            tags.append('sweet')
        if radar.sour >= 0.5:
            tags.append('sour')
        if radar.salty >= 0.5:
            tags.append('salty')
        if radar.fresh >= 0.5:
            tags.append('fresh')
        if radar.light >= 0.5:
            tags.append('light')
        
        return tags
    
    async def _get_restaurant(self, restaurant_id: int) -> Optional[Restaurant]:
        """
        获取餐厅信息
        """
        stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _save_profile(self, profile_result: TasteProfileResult):
        """
        保存口味画像到数据库
        """
        # 查询现有画像
        stmt = select(TasteProfile).where(
            TasteProfile.user_id == profile_result.user_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新
            existing.preferred_cuisines = profile_result.preferred_cuisines
            existing.preferred_price_range = profile_result.preferred_price_range
            existing.preferred_spice_level = profile_result.preferred_spice_level
            existing.flavor_tags = profile_result.flavor_tags
        else:
            # 创建
            new_profile = TasteProfile(
                user_id=profile_result.user_id,
                preferred_cuisines=profile_result.preferred_cuisines,
                preferred_price_range=profile_result.preferred_price_range,
                preferred_spice_level=profile_result.preferred_spice_level,
                flavor_tags=profile_result.flavor_tags
            )
            self.db.add(new_profile)
        
        await self.db.commit()


# 导出
__all__ = [
    'TasteProfileEngine',
    'TasteRadar',
    'TasteLabel',
    'TasteProfileResult'
]
