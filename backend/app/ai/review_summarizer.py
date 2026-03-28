"""
AI美食点评摘要
聚合多平台评论，提取关键评价点，生成摘要
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from collections import Counter
import re
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.crawler import PlatformRating


@dataclass
class ReviewKeyword:
    """
    评论关键词
    """
    text: str
    sentiment: str  # positive/negative/neutral
    frequency: int
    score: float  # TF-IDF分数


@dataclass
class ReviewSummary:
    """
    评论摘要结果
    """
    restaurant_id: int
    restaurant_name: str
    overall_rating: float
    total_reviews: int
    platforms: List[str]
    
    # 关键评价点
    positive_keywords: List[ReviewKeyword] = field(default_factory=list)
    negative_keywords: List[ReviewKeyword] = field(default_factory=list)
    neutral_keywords: List[ReviewKeyword] = field(default_factory=list)
    
    # 一句话摘要
    summary_text: str = ""
    
    # 详细评价点
    highlights: List[str] = field(default_factory=list)


class ReviewSummarizer:
    """
    AI美食点评摘要器
    使用TF-IDF + 规则提取关键评价点
    """
    
    # 停用词表
    STOP_WORDS = set([
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
        '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
        '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
        '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
        '可以', '就是', '这样', '然后', '还是', '但是', '因为'
    ])
    
    # 正面关键词
    POSITIVE_WORDS = {
        '好吃': 2.0, '美味': 2.0, '推荐': 1.5, '不错': 1.5,
        '新鲜': 1.5, '服务好': 2.0, '环境好': 1.8, '干净': 1.5,
        '分量足': 1.8, '性价比高': 2.0, '味道好': 1.8, '正宗': 1.8,
        '精致': 1.5, '地道': 1.8, '实惠': 1.5, '很棒': 2.0,
        '满意': 1.5, '喜欢': 1.5, '值得': 1.8, '回头客': 2.0
    }
    
    # 负面关键词
    NEGATIVE_WORDS = {
        '难吃': -2.0, '不新鲜': -1.8, '服务差': -2.0, '环境差': -1.8,
        '脏': -2.0, '分量少': -1.5, '贵': -1.0, '不推荐': -2.0,
        '失望': -1.5, '一般': -0.5, '凑合': -0.8, '不地道': -1.5,
        '咸': -0.8, '淡': -0.8, '油腻': -1.0, '排队久': -1.2,
        '上菜慢': -1.5, '态度差': -2.0
    }
    
    # 中性关键词
    NEUTRAL_PATTERNS = [
        r'人均.*?元', r'排队.*?分钟', r'营业时间.*?',
        r'位于.*?', r'靠近.*?', r'附近.*?'
    ]
    
    # 评价维度关键词
    DIMENSION_KEYWORDS = {
        '口味': ['好吃', '美味', '味道', '正宗', '地道', '难吃', '咸', '淡', '油腻'],
        '服务': ['服务好', '态度好', '上菜快', '服务差', '态度差', '上菜慢'],
        '环境': ['环境好', '干净', '舒适', '环境差', '脏', '嘈杂', '拥挤'],
        '分量': ['分量足', '量大', '实惠', '分量少', '不够吃'],
        '价格': ['性价比高', '实惠', '便宜', '贵', '不划算']
    }
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """
        初始化点评摘要器
        
        Args:
            db: 数据库会话（可选）
        """
        self.db = db
    
    async def summarize_reviews(
        self,
        restaurant_id: int,
        reviews: Optional[List[str]] = None
    ) -> ReviewSummary:
        """
        聚合某餐厅的评论并生成摘要
        
        Args:
            restaurant_id: 餐厅ID
            reviews: 评论列表（可选，不提供则从数据库获取）
            
        Returns:
            ReviewSummary对象
        """
        # 获取评论数据
        if not reviews:
            reviews, platform_data = await self._fetch_reviews_from_db(restaurant_id)
        else:
            platform_data = {'custom': len(reviews)}
        
        if not reviews:
            return self._create_empty_summary(restaurant_id)
        
        # 1. 预处理评论
        processed_reviews = self._preprocess_reviews(reviews)
        
        # 2. 提取关键词（TF-IDF）
        all_keywords = self._extract_keywords_tfidf(processed_reviews)
        
        # 3. 分类关键词（正/负/中性）
        positive, negative, neutral = self._classify_keywords(all_keywords)
        
        # 4. 提取评价亮点
        highlights = self._extract_highlights(processed_reviews)
        
        # 5. 生成一句话摘要
        summary_text = self._generate_summary_text(
            positive, negative, neutral, highlights
        )
        
        # 6. 计算综合评分
        overall_rating = self._calculate_overall_rating(positive, negative)
        
        return ReviewSummary(
            restaurant_id=restaurant_id,
            restaurant_name="",  # 需要从外部传入或查询
            overall_rating=overall_rating,
            total_reviews=len(reviews),
            platforms=list(platform_data.keys()),
            positive_keywords=positive[:10],
            negative_keywords=negative[:5],
            neutral_keywords=neutral[:5],
            summary_text=summary_text,
            highlights=highlights[:8]
        )
    
    async def _fetch_reviews_from_db(
        self,
        restaurant_id: int
    ) -> tuple[List[str], Dict[str, int]]:
        """
        从数据库获取餐厅评论
        注意：这里简化处理，实际应该有评论表
        """
        reviews = []
        platform_data = {}
        
        if self.db:
            # 获取平台评分信息（模拟评论）
            stmt = select(PlatformRating).where(
                PlatformRating.restaurant_id == restaurant_id
            )
            result = await self.db.execute(stmt)
            ratings = result.scalars().all()
            
            for rating in ratings:
                platform_data[rating.platform] = rating.review_count
                # 从标签生成模拟评论
                if rating.tags:
                    for tag in rating.tags[:3]:
                        reviews.append(f"{tag}")
        
        return reviews, platform_data
    
    def _preprocess_reviews(self, reviews: List[str]) -> List[List[str]]:
        """
        预处理评论：分词、去停用词
        """
        processed = []
        
        for review in reviews:
            # 简单分词（按标点和空格）
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+', review)
            
            # 去停用词
            filtered = [w for w in words if w not in self.STOP_WORDS and len(w) > 1]
            
            if filtered:
                processed.append(filtered)
        
        return processed
    
    def _extract_keywords_tfidf(
        self,
        processed_reviews: List[List[str]]
    ) -> List[ReviewKeyword]:
        """
        使用TF-IDF提取关键词
        """
        # 计算词频（TF）
        doc_count = len(processed_reviews)
        term_freq = Counter()
        doc_freq = Counter()
        
        for doc in processed_reviews:
            term_freq.update(doc)
            unique_terms = set(doc)
            doc_freq.update(unique_terms)
        
        # 计算TF-IDF分数
        keywords = []
        
        for term, tf in term_freq.items():
            # TF: 词频 / 文档总词数
            tf_score = tf / sum(term_freq.values())
            
            # IDF: log(总文档数 / 包含该词的文档数)
            df = doc_freq.get(term, 1)
            idf_score = math.log(doc_count / df) if df > 0 else 0
            
            # TF-IDF
            tfidf = tf_score * idf_score
            
            if tfidf > 0.01:  # 过滤低分词
                # 判断情感
                sentiment = self._get_sentiment(term)
                
                keywords.append(ReviewKeyword(
                    text=term,
                    sentiment=sentiment,
                    frequency=tf,
                    score=tfidf
                ))
        
        # 按分数排序
        keywords.sort(key=lambda x: x.score, reverse=True)
        
        return keywords
    
    def _get_sentiment(self, term: str) -> str:
        """
        判断词语的情感倾向
        """
        if term in self.POSITIVE_WORDS:
            return 'positive'
        elif term in self.NEGATIVE_WORDS:
            return 'negative'
        
        # 检查是否包含情感词
        for pos_word in self.POSITIVE_WORDS:
            if pos_word in term or term in pos_word:
                return 'positive'
        
        for neg_word in self.NEGATIVE_WORDS:
            if neg_word in term or term in neg_word:
                return 'negative'
        
        return 'neutral'
    
    def _classify_keywords(
        self,
        keywords: List[ReviewKeyword]
    ) -> tuple[List[ReviewKeyword], List[ReviewKeyword], List[ReviewKeyword]]:
        """
        分类关键词为正面、负面、中性
        """
        positive = [k for k in keywords if k.sentiment == 'positive']
        negative = [k for k in keywords if k.sentiment == 'negative']
        neutral = [k for k in keywords if k.sentiment == 'neutral']
        
        return positive, negative, neutral
    
    def _extract_highlights(self, processed_reviews: List[List[str]]) -> List[str]:
        """
        提取评价亮点（基于维度）
        """
        highlights = []
        
        for dimension, keywords in self.DIMENSION_KEYWORDS.items():
            # 检查每个维度是否被提及
            mentions = []
            for review in processed_reviews:
                for keyword in keywords:
                    if keyword in review:
                        mentions.append(keyword)
            
            if mentions:
                # 取该维度最常被提及的关键词
                counter = Counter(mentions)
                top_keyword = counter.most_common(1)[0][0]
                highlights.append(f"{dimension}：{top_keyword}")
        
        return highlights
    
    def _generate_summary_text(
        self,
        positive: List[ReviewKeyword],
        negative: List[ReviewKeyword],
        neutral: List[ReviewKeyword],
        highlights: List[str]
    ) -> str:
        """
        生成一句话AI摘要
        """
        parts = []
        
        # 正面评价
        if positive:
            top_positive = positive[0].text
            parts.append(f"顾客普遍认为{top_positive}")
        
        # 负面评价（如果有明显负面）
        if negative:
            top_negative = negative[0].text
            parts.append(f"但{top_negative}")
        
        # 综合评价
        if not parts:
            if positive and not negative:
                parts.append("整体评价较好")
            elif negative and not positive:
                parts.append("整体评价一般")
            else:
                parts.append("评价较为中性")
        
        return '，'.join(parts) + '。'
    
    def _calculate_overall_rating(
        self,
        positive: List[ReviewKeyword],
        negative: List[ReviewKeyword]
    ) -> float:
        """
        计算综合评分（基于关键词情感）
        """
        positive_score = sum(
            self.POSITIVE_WORDS.get(k.text, 1.0) * k.frequency
            for k in positive
        )
        
        negative_score = abs(sum(
            self.NEGATIVE_WORDS.get(k.text, -1.0) * k.frequency
            for k in negative
        ))
        
        if positive_score + negative_score == 0:
            return 3.5  # 默认中等评分
        
        # 计算积极评价占比
        positive_ratio = positive_score / (positive_score + negative_score)
        
        # 映射到1-5分
        rating = 1 + positive_ratio * 4
        
        return round(min(max(rating, 1.0), 5.0), 1)
    
    def _create_empty_summary(self, restaurant_id: int) -> ReviewSummary:
        """
        创建空摘要（无评论时）
        """
        return ReviewSummary(
            restaurant_id=restaurant_id,
            restaurant_name="",
            overall_rating=3.5,
            total_reviews=0,
            platforms=[],
            positive_keywords=[],
            negative_keywords=[],
            neutral_keywords=[],
            summary_text="暂无评论数据",
            highlights=[]
        )
    
    def summarize_from_text(self, text: str) -> Dict[str, Any]:
        """
        从单段文本中提取关键评价点（工具方法）
        
        Args:
            text: 评论文本
            
        Returns:
            包含关键词和情感的字典
        """
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        
        positive = []
        negative = []
        
        for word in words:
            if word in self.POSITIVE_WORDS:
                positive.append(word)
            elif word in self.NEGATIVE_WORDS:
                negative.append(word)
        
        # 计算情感分数
        pos_score = sum(self.POSITIVE_WORDS.get(w, 0) for w in positive)
        neg_score = sum(self.NEGATIVE_WORDS.get(w, 0) for w in negative)
        
        sentiment = 'neutral'
        if pos_score > neg_score:
            sentiment = 'positive'
        elif neg_score > pos_score:
            sentiment = 'negative'
        
        return {
            'positive_keywords': list(set(positive)),
            'negative_keywords': list(set(negative)),
            'sentiment': sentiment,
            'score': pos_score + neg_score
        }


# 导出
__all__ = ['ReviewSummarizer', 'ReviewSummary', 'ReviewKeyword']
