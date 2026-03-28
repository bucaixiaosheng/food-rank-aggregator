# AI推荐模块

from app.ai.taste_parser import TasteParser, TasteQuery
from app.ai.scoring import ScoringEngine, ScoringWeights, RestaurantScore
from app.ai.recommendation import (
    RecommendationService,
    RecommendationRequest,
    RecommendationResult,
    RecommendationCache
)
from app.ai.taste_profile import (
    TasteProfileEngine,
    TasteRadar,
    TasteLabel,
    TasteProfileResult
)
from app.ai.weather import WeatherRecommender, WeatherInfo, WeatherRecommendation
from app.ai.mood import MoodRecommender, Mood, MoodRecommendation
from app.ai.review_summarizer import ReviewSummarizer, ReviewSummary, ReviewKeyword

__all__ = [
    # 口味解析
    'TasteParser',
    'TasteQuery',
    
    # 评分引擎
    'ScoringEngine',
    'ScoringWeights',
    'RestaurantScore',
    
    # 推荐服务
    'RecommendationService',
    'RecommendationRequest',
    'RecommendationResult',
    'RecommendationCache',
    
    # 口味画像
    'TasteProfileEngine',
    'TasteRadar',
    'TasteLabel',
    'TasteProfileResult',
    
    # 天气推荐
    'WeatherRecommender',
    'WeatherInfo',
    'WeatherRecommendation',
    
    # 心情推荐
    'MoodRecommender',
    'Mood',
    'MoodRecommendation',
    
    # 评论摘要
    'ReviewSummarizer',
    'ReviewSummary',
    'ReviewKeyword'
]
