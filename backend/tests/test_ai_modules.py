"""
AI模块单元测试
"""
import pytest
from app.ai.taste_parser import TasteParser, TasteQuery
from app.ai.scoring import ScoringEngine, ScoringWeights, RestaurantScore
from app.ai.mood import MoodRecommender, Mood
from app.ai.review_summarizer import ReviewSummarizer


class TestTasteParser:
    """口味解析器测试"""
    
    def setup_method(self):
        self.parser = TasteParser()
    
    def test_parse_spicy_food(self):
        """测试辣味解析"""
        query = self.parser.parse("想吃辣的")
        assert query.cuisine == 'Sichuan'
        assert query.spice_level in [4, 5]
        assert query.confidence > 0
    
    def test_parse_hotpot(self):
        """测试火锅解析"""
        query = self.parser.parse("火锅")
        assert query.cuisine == 'Hotpot' or query.dish == 'hotpot'
    
    def test_parse_japanese(self):
        """测试日料解析"""
        query = self.parser.parse("想吃日料")
        assert query.cuisine == 'Japanese'
    
    def test_parse_multiple_keywords(self):
        """测试多关键词解析"""
        query = self.parser.parse("想吃辣的川菜火锅")
        assert query.cuisine is not None
        assert query.spice_level is not None
        assert len(query.cuisine_keywords) > 0
    
    def test_parse_empty_input(self):
        """测试空输入"""
        query = self.parser.parse("")
        assert query.confidence == 0
    
    def test_fuzzy_match(self):
        """测试模糊匹配"""
        matches = self.parser.fuzzy_match("川菜", threshold=0.7)
        assert len(matches) > 0


class TestScoringEngine:
    """评分引擎测试"""
    
    def setup_method(self):
        self.engine = ScoringEngine()
    
    @pytest.mark.asyncio
    async def test_calculate_basic_score(self):
        """测试基本评分计算"""
        restaurant = {
            'id': 1,
            'name': '测试餐厅',
            'cuisine_type': 'Sichuan',
            'rating': 4.5,
            'price_range': '¥¥'
        }
        
        score = await self.engine.calculate_score(restaurant)
        
        assert 0 <= score.total_score <= 1
        assert score.restaurant_id == 1
        assert 0 <= score.taste_score <= 1
        assert 0 <= score.rating_score <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_with_user_preferences(self):
        """测试带用户偏好的评分"""
        restaurant = {
            'id': 1,
            'name': '川菜馆',
            'cuisine_type': 'Sichuan',
            'rating': 4.5
        }
        
        user_preferences = {
            'preferred_cuisines': ['Sichuan'],
            'preferred_spice_level': 5,
            'flavor_tags': ['spicy']
        }
        
        score = await self.engine.calculate_score(
            restaurant,
            user_preferences=user_preferences
        )
        
        # 菜系匹配，口味匹配度高
        assert score.taste_score > 0.5
    
    @pytest.mark.asyncio
    async def test_calculate_with_location(self):
        """测试带位置信息的评分"""
        restaurant = {
            'id': 1,
            'name': '测试餐厅',
            'latitude': 39.9,
            'longitude': 116.4
        }
        
        user_location = (39.91, 116.41)
        
        score = await self.engine.calculate_score(
            restaurant,
            user_location=user_location
        )
        
        assert score.distance_km is not None
        assert score.distance_score > 0.5  # 距离很近
    
    def test_custom_weights(self):
        """测试自定义权重"""
        weights = ScoringWeights(
            taste_match=0.5,
            platform_rating=0.3,
            distance=0.1,
            price_match=0.05,
            popularity=0.03,
            freshness=0.02
        )
        
        engine = ScoringEngine(weights)
        assert engine.weights.taste_match == 0.5
    
    def test_invalid_weights(self):
        """测试无效权重（和不为1）"""
        with pytest.raises(ValueError):
            ScoringWeights(
                taste_match=0.4,
                platform_rating=0.4,
                distance=0.3  # 总和1.1
            )


class TestMoodRecommender:
    """心情推荐测试"""
    
    def setup_method(self):
        self.recommender = MoodRecommender()
    
    def test_recommend_happy_mood(self):
        """测试开心心情推荐"""
        result = self.recommender.recommend_by_mood(Mood.HAPPY)
        
        assert result.mood == Mood.HAPPY
        assert len(result.cuisine_types) > 0
        assert len(result.dishes) > 0
        assert len(result.comfort_message) > 0
    
    def test_recommend_with_taste_profile(self):
        """测试带口味画像的心情推荐"""
        taste_profile = {
            'preferred_cuisines': ['Sichuan', 'Hotpot'],
            'preferred_spice_level': 5,
            'flavor_tags': ['spicy']
        }
        
        result = self.recommender.recommend_by_mood(
            Mood.SAD,
            user_taste_profile=taste_profile
        )
        
        # 应该考虑用户的辣味偏好
        assert 'Sichuan' in result.cuisine_types or 'Hotpot' in result.cuisine_types
    
    def test_infer_mood_from_text(self):
        """测试从文本推断心情"""
        assert self.recommender.infer_mood_from_text('今天很开心') == Mood.HAPPY
        assert self.recommender.infer_mood_from_text('有点难过') == Mood.SAD
        assert self.recommender.infer_mood_from_text('好累啊') == Mood.TIRED
        assert self.recommender.infer_mood_from_text('随便') is None
    
    def test_get_available_moods(self):
        """测试获取所有心情类型"""
        moods = self.recommender.get_available_moods()
        
        assert len(moods) == 9  # 9种心情
        assert all('value' in m and 'name' in m for m in moods)


class TestReviewSummarizer:
    """评论摘要测试"""
    
    def setup_method(self):
        self.summarizer = ReviewSummarizer()
    
    @pytest.mark.asyncio
    async def test_summarize_empty_reviews(self):
        """测试空评论"""
        result = await self.summarizer.summarize_reviews(1, reviews=[])
        
        assert result.total_reviews == 0
        assert result.summary_text == "暂无评论数据"
    
    @pytest.mark.asyncio
    async def test_summarize_positive_reviews(self):
        """测试正面评论"""
        reviews = [
            '这家店很好吃，服务也很好',
            '味道正宗，分量足',
            '环境不错，推荐！'
        ]
        
        result = await self.summarizer.summarize_reviews(1, reviews=reviews)
        
        assert result.total_reviews == 3
        assert len(result.positive_keywords) > 0
        assert result.overall_rating > 3.5
    
    @pytest.mark.asyncio
    async def test_summarize_mixed_reviews(self):
        """测试混合评论"""
        reviews = [
            '好吃但有点贵',
            '味道不错，上菜慢',
            '环境好，服务一般'
        ]
        
        result = await self.summarizer.summarize_reviews(1, reviews=reviews)
        
        assert len(result.positive_keywords) > 0
        assert len(result.negative_keywords) > 0
    
    def test_summarize_from_text(self):
        """测试单文本摘要"""
        text = '这家店很好吃，但是有点贵，服务一般'
        result = self.summarizer.summarize_from_text(text)
        
        assert 'positive_keywords' in result
        assert 'negative_keywords' in result
        assert 'sentiment' in result


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
