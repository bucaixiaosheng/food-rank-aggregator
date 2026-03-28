"""
心情推荐模块
根据用户心情推荐合适的美食
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Mood(Enum):
    """
    心情类型枚举
    """
    HAPPY = "happy"           # 开心
    SAD = "sad"               # 难过
    TIRED = "tired"           # 疲惫
    STRESSED = "stressed"     # 压力大
    EXCITED = "excited"       # 兴奋
    ROMANTIC = "romantic"     # 浪漫
    CELEBRATE = "celebrate"   # 庆祝
    BORED = "bored"           # 无聊
    LONELY = "lonely"         # 孤独


@dataclass
class MoodRecommendation:
    """
    心情推荐结果
    """
    mood: Mood
    cuisine_types: List[str]
    dishes: List[str]
    reasons: List[str]
    comfort_message: str
    pairing_suggestions: List[str]


class MoodRecommender:
    """
    心情推荐器
    根据用户心情推荐美食，结合口味画像加权
    """
    
    # 心情-菜系映射
    MOOD_CUISINES = {
        Mood.HAPPY: {
            'cuisines': ['Dessert', 'BBQ', 'Japanese', 'Western'],
            'dishes': ['甜品', '烤肉', '寿司', '牛排', '火锅'],
            'reasons': ['开心时，美食会让快乐加倍', '甜品释放多巴胺，保持好心情'],
            'message': '心情愉悦，正是享受美食的好时光！',
            'pairing': ['和朋友聚餐', '尝试新餐厅', '点一份精致甜品']
        },
        Mood.SAD: {
            'cuisines': ['FastFood', 'Snack', 'Dessert'],
            'dishes': ['巧克力', '炸鸡', '蛋糕', '奶茶', '火锅'],
            'reasons': ['巧克力能提升情绪', '热乎乎的食物带来温暖'],
            'message': '难过时，美食是最好的安慰',
            'pairing': ['点一份治愈系美食', '和朋友聊聊天', '来杯热饮']
        },
        Mood.TIRED: {
            'cuisines': ['Cantonese', 'Snack', 'Jiangzhe'],
            'dishes': ['粥', '清淡菜品', '汤面', '养生汤'],
            'reasons': ['疲劳时需要清淡营养的食物', '易消化的食物减轻负担'],
            'message': '疲惫的身体需要温柔的呵护',
            'pairing': ['来碗热粥', '喝点养生汤', '早点休息']
        },
        Mood.STRESSED: {
            'cuisines': ['Hotpot', 'BBQ', 'Dessert'],
            'dishes': ['火锅', '烤肉', '奶茶', '甜点'],
            'reasons': ['辣味食物释放压力', '大口吃肉缓解焦虑'],
            'message': '压力大时，用美食释放情绪',
            'pairing': ['约上好友吃火锅', '来顿烧烤', '点杯奶茶']
        },
        Mood.EXCITED: {
            'cuisines': ['Japanese', 'Western', 'Hotpot'],
            'dishes': ['刺身', '牛排', '火锅', '海鲜'],
            'reasons': ['兴奋时适合享用高品质美食', '庆祝激动人心的时刻'],
            'message': '充满激情，让美食为这份热情加分！',
            'pairing': ['尝试高级餐厅', '点份豪华套餐', '和朋友分享']
        },
        Mood.ROMANTIC: {
            'cuisines': ['Western', 'Japanese', 'French'],
            'dishes': ['牛排', '红酒炖牛肉', '法式料理', '精致甜品'],
            'reasons': ['浪漫氛围需要精致美食配合', '优雅的用餐环境增进感情'],
            'message': '浪漫时刻，让美食见证美好',
            'pairing': ['选择环境优雅的餐厅', '点份精致套餐', '配上一杯红酒']
        },
        Mood.CELEBRATE: {
            'cuisines': ['Japanese', 'Western', 'Hotpot', 'BBQ'],
            'dishes': ['日料', '西餐', '火锅', '烤肉', '海鲜大餐'],
            'reasons': ['庆祝时刻需要丰盛的美食', '值得享受一顿大餐'],
            'message': '值得庆祝的日子，美食不可辜负！',
            'pairing': ['选择心仪已久的餐厅', '点上拿手好菜', '和朋友欢聚']
        },
        Mood.BORED: {
            'cuisines': ['Snack', 'Hotpot', 'BBQ'],
            'dishes': ['火锅', '烧烤', '小吃', '麻辣烫', '串串'],
            'reasons': ['无聊时尝试新口味激发兴趣', '热闹的用餐氛围驱散无聊'],
            'message': '无聊的时候，美食是最好的陪伴',
            'pairing': ['尝试没吃过的菜系', '去热闹的餐厅', '自己下厨试试']
        },
        Mood.LONELY: {
            'cuisines': ['Hotpot', 'Snack', 'Dessert'],
            'dishes': ['火锅', '面条', '热汤', '甜品'],
            'reasons': ['热腾腾的食物带来温暖', '甜食能缓解孤独感'],
            'message': '一个人也要好好吃饭，照顾好自己',
            'pairing': ['点一份温暖的外卖', '去喜欢的餐厅', '给自己一个小奖励']
        }
    }
    
    # 口味画像加权系数
    TASTE_WEIGHTS = {
        'spicy': {'Sichuan': 0.3, 'Hotpot': 0.2, 'BBQ': 0.1},
        'sweet': {'Dessert': 0.4, 'Jiangzhe': 0.2},
        'light': {'Cantonese': 0.3, 'Japanese': 0.2},
        'fresh': {'Japanese': 0.3, 'Cantonese': 0.2}
    }
    
    def __init__(self):
        """初始化心情推荐器"""
        pass
    
    def recommend_by_mood(
        self,
        mood: Mood,
        user_taste_profile: Optional[Dict[str, Any]] = None
    ) -> MoodRecommendation:
        """
        根据心情推荐美食
        
        Args:
            mood: 用户心情
            user_taste_profile: 用户口味画像（可选）
            
        Returns:
            MoodRecommendation对象
        """
        # 获取基础推荐
        base_config = self.MOOD_CUISINES.get(mood, self.MOOD_CUISINES[Mood.HAPPY])
        
        cuisine_types = base_config['cuisines'].copy()
        dishes = base_config['dishes'].copy()
        reasons = base_config['reasons'].copy()
        comfort_message = base_config['message']
        pairing_suggestions = base_config['pairing'].copy()
        
        # 如果有用户口味画像，进行加权调整
        if user_taste_profile:
            cuisine_types = self._apply_taste_weights(
                cuisine_types, 
                user_taste_profile
            )
        
        return MoodRecommendation(
            mood=mood,
            cuisine_types=cuisine_types,
            dishes=dishes,
            reasons=reasons,
            comfort_message=comfort_message,
            pairing_suggestions=pairing_suggestions
        )
    
    def _apply_taste_weights(
        self,
        base_cuisines: List[str],
        taste_profile: Dict[str, Any]
    ) -> List[str]:
        """
        根据用户口味偏好调整推荐菜系
        
        Args:
            base_cuisines: 基础菜系列表
            taste_profile: 用户口味画像
            
        Returns:
            调整后的菜系列表
        """
        # 提取用户偏好
        preferred_cuisines = taste_profile.get('preferred_cuisines', [])
        flavor_tags = taste_profile.get('flavor_tags', [])
        spice_level = taste_profile.get('preferred_spice_level', 3)
        
        # 计算每个菜系的分数
        cuisine_scores = {}
        
        # 基础分数（心情推荐）
        for i, cuisine in enumerate(base_cuisines):
            cuisine_scores[cuisine] = 1.0 - (i * 0.1)  # 排名越前分数越高
        
        # 用户偏好加分
        for cuisine in preferred_cuisines:
            if cuisine in cuisine_scores:
                cuisine_scores[cuisine] += 0.5
            else:
                cuisine_scores[cuisine] = 0.5
        
        # 口味标签加分
        for tag in flavor_tags:
            if tag in self.TASTE_WEIGHTS:
                for cuisine, weight in self.TASTE_WEIGHTS[tag].items():
                    if cuisine in cuisine_scores:
                        cuisine_scores[cuisine] += weight
        
        # 辣度调整
        if spice_level >= 4:
            for cuisine in ['Sichuan', 'Hotpot', 'BBQ']:
                if cuisine in cuisine_scores:
                    cuisine_scores[cuisine] += 0.3
        elif spice_level <= 2:
            for cuisine in ['Cantonese', 'Japanese', 'Jiangzhe']:
                if cuisine in cuisine_scores:
                    cuisine_scores[cuisine] += 0.3
        
        # 按分数排序
        sorted_cuisines = sorted(
            cuisine_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [cuisine for cuisine, score in sorted_cuisines[:5]]
    
    def get_available_moods(self) -> List[Dict[str, str]]:
        """
        获取所有可用的心情类型
        
        Returns:
            心情列表，包含name和description
        """
        mood_descriptions = {
            Mood.HAPPY: '开心快乐',
            Mood.SAD: '难过伤心',
            Mood.TIRED: '疲惫劳累',
            Mood.STRESSED: '压力山大',
            Mood.EXCITED: '兴奋激动',
            Mood.ROMANTIC: '浪漫甜蜜',
            Mood.CELEBRATE: '庆祝喜事',
            Mood.BORED: '无聊发呆',
            Mood.LONELY: '孤单寂寞'
        }
        
        return [
            {'value': mood.value, 'name': mood_descriptions[mood]}
            for mood in Mood
        ]
    
    def infer_mood_from_text(self, text: str) -> Optional[Mood]:
        """
        从文本推断用户心情（简单关键词匹配）
        
        Args:
            text: 用户输入文本
            
        Returns:
            推断的心情，如果无法推断则返回None
        """
        # 心情关键词映射
        mood_keywords = {
            Mood.HAPPY: ['开心', '高兴', '快乐', '幸福', '好心情', '棒', '赞'],
            Mood.SAD: ['难过', '伤心', '不开心', '郁闷', '沮丧', '失落'],
            Mood.TIRED: ['累', '疲惫', '困', '没精神', '疲倦', '乏力'],
            Mood.STRESSED: ['压力', '紧张', '焦虑', '烦躁', '压力大'],
            Mood.EXCITED: ['兴奋', '激动', '期待', '迫不及待'],
            Mood.ROMANTIC: ['浪漫', '约会', '情人节', '甜蜜'],
            Mood.CELEBRATE: ['庆祝', '恭喜', '成功', '纪念日', '生日'],
            Mood.BORED: ['无聊', '没意思', '发呆', '没事干'],
            Mood.LONELY: ['孤独', '寂寞', '一个人', '单身']
        }
        
        text_lower = text.lower()
        
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return mood
        
        return None


# 导出
__all__ = ['MoodRecommender', 'Mood', 'MoodRecommendation']
