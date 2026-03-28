"""
口味意图解析器
解析自然语言输入为结构化查询
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re
from difflib import SequenceMatcher


@dataclass
class TasteQuery:
    """
    口味查询数据类
    """
    # 菜系相关
    cuisine: Optional[str] = None  # 具体菜系：Sichuan, Cantonese, Japanese等
    cuisine_keywords: List[str] = field(default_factory=list)  # 菜系关键词
    
    # 菜品相关
    dish: Optional[str] = None  # 具体菜品：hotpot, barbecue等
    dish_keywords: List[str] = field(default_factory=list)  # 菜品关键词
    
    # 口味维度
    spice_level: Optional[int] = None  # 辣度：1-5 (None表示无要求)
    flavor_tags: List[str] = field(default_factory=list)  # 口味标签：sweet, sour, light, rich等
    
    # 其他条件
    price_range: Optional[str] = None  # 价格区间：¥, ¥¥, ¥¥¥, ¥¥¥¥
    temperature: Optional[str] = None  # 温度偏好：hot, cold
    
    # 原始文本
    raw_text: str = ""
    confidence: float = 0.0  # 解析置信度 0-1


class TasteParser:
    """
    口味意图解析器
    使用规则+同义词匹配，不依赖外部LLM
    """
    
    # 菜系映射表（同义词 -> 标准菜系名）
    CUISINE_SYNONYMS = {
        # 川菜
        '川菜': 'Sichuan', '四川菜': 'Sichuan', '麻辣': 'Sichuan', 
        '辣的': 'Sichuan', '辣': 'Sichuan', '麻': 'Sichuan',
        '水煮': 'Sichuan', '毛血旺': 'Sichuan', '回锅肉': 'Sichuan',
        
        # 粤菜
        '粤菜': 'Cantonese', '广东菜': 'Cantonese', '广式': 'Cantonese',
        '早茶': 'Cantonese', '点心': 'Cantonese', '烧腊': 'Cantonese',
        
        # 日料
        '日料': 'Japanese', '日本料理': 'Japanese', '日式': 'Japanese',
        '寿司': 'Japanese', '刺身': 'Japanese', '拉面': 'Japanese',
        '生鱼片': 'Japanese', '鳗鱼饭': 'Japanese',
        
        # 韩餐
        '韩餐': 'Korean', '韩国菜': 'Korean', '韩式': 'Korean',
        '烤肉': 'Korean', '石锅拌饭': 'Korean', '泡菜': 'Korean',
        
        # 西餐
        '西餐': 'Western', '西式': 'Western', '牛排': 'Western',
        '意大利面': 'Western', '披萨': 'Western', '意餐': 'Western',
        
        # 火锅
        '火锅': 'Hotpot', '涮锅': 'Hotpot', '涮羊肉': 'Hotpot',
        '重庆火锅': 'Hotpot', '北京火锅': 'Hotpot',
        
        # 烧烤
        '烧烤': 'BBQ', '烤串': 'BBQ', '撸串': 'BBQ',
        '羊肉串': 'BBQ', '烤肉': 'BBQ',
        
        # 湘菜
        '湘菜': 'Hunan', '湖南菜': 'Hunan', '剁椒': 'Hunan',
        
        # 江浙菜
        '江浙菜': 'Jiangzhe', '江浙': 'Jiangzhe', '苏菜': 'Jiangzhe',
        '杭帮菜': 'Jiangzhe', '上海菜': 'Jiangzhe',
        
        # 其他
        '甜品': 'Dessert', '甜点': 'Dessert', '蛋糕': 'Dessert',
        '奶茶': 'Dessert', '冰激凌': 'Dessert',
        '快餐': 'FastFood', '汉堡': 'FastFood', '炸鸡': 'FastFood',
        '小吃': 'Snack', '夜宵': 'Snack', '麻辣烫': 'Snack',
    }
    
    # 菜品关键词映射
    DISH_KEYWORDS = {
        '火锅': 'hotpot', '涮锅': 'hotpot', '涮羊肉': 'hotpot',
        '烧烤': 'bbq', '烤串': 'bbq', '烤肉': 'bbq',
        '寿司': 'sushi', '刺身': 'sashimi',
        '面条': 'noodles', '拉面': 'ramen', '米线': 'rice_noodles',
        '饺子': 'dumpling', '包子': 'dumpling',
        '粥': 'porridge', '稀饭': 'porridge',
        '汤': 'soup', '热汤': 'soup',
        '凉皮': 'cold_noodles', '冰粉': 'ice_jelly',
        '沙拉': 'salad', '轻食': 'salad',
        '甜品': 'dessert', '蛋糕': 'cake', '奶茶': 'milk_tea',
    }
    
    # 口味维度映射
    FLAVOR_MAPPING = {
        # 辣度
        '辣': 'spicy', '麻辣': 'spicy', '重辣': 'spicy', 
        '变态辣': 'extreme_spicy', '特辣': 'very_spicy',
        '微辣': 'mild_spicy', '中辣': 'medium_spicy',
        
        # 清淡
        '清淡': 'light', '清爽': 'light', '不辣': 'light',
        '养生': 'light', '健康': 'light',
        
        # 其他口味
        '甜': 'sweet', '甜品': 'sweet',
        '酸': 'sour', '开胃': 'sour',
        '咸': 'salty', '重口': 'salty',
        '鲜': 'fresh', '鲜美': 'fresh',
        '香': 'fragrant', '香辣': 'fragrant',
    }
    
    # 辣度级别映射
    SPICE_LEVELS = {
        '不辣': 1, '清淡': 1, '微辣': 2, '中辣': 3,
        '辣': 4, '麻辣': 4, '重辣': 5, '特辣': 5, '变态辣': 5,
    }
    
    # 价格区间映射
    PRICE_MAPPING = {
        '便宜': '¥', '实惠': '¥', '平价': '¥',
        '中等': '¥¥', '适中': '¥¥',
        '高档': '¥¥¥', '高级': '¥¥¥',
        '豪华': '¥¥¥¥', '奢侈': '¥¥¥¥',
    }
    
    # 温度映射
    TEMPERATURE_MAPPING = {
        '热': 'hot', '烫': 'hot', '暖': 'hot',
        '冷': 'cold', '凉': 'cold', '冰': 'cold',
    }
    
    def __init__(self):
        # 预编译常用正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """预编译正则表达式"""
        self.cuisine_pattern = re.compile('|'.join(self.CUISINE_SYNONYMS.keys()))
        self.dish_pattern = re.compile('|'.join(self.DISH_KEYWORDS.keys()))
        self.flavor_pattern = re.compile('|'.join(self.FLAVOR_MAPPING.keys()))
        self.spice_pattern = re.compile('|'.join(self.SPICE_LEVELS.keys()))
        self.price_pattern = re.compile('|'.join(self.PRICE_MAPPING.keys()))
        self.temp_pattern = re.compile('|'.join(self.TEMPERATURE_MAPPING.keys()))
    
    def parse(self, text: str) -> TasteQuery:
        """
        解析自然语言输入为结构化查询
        
        Args:
            text: 用户输入的自然语言，如"想吃辣的火锅"
            
        Returns:
            TasteQuery对象，包含解析后的结构化查询
        """
        query = TasteQuery(raw_text=text)
        
        if not text or not text.strip():
            return query
        
        text = text.strip()
        matched_keywords = []
        
        # 1. 解析菜系
        cuisine_matches = self.cuisine_pattern.findall(text)
        if cuisine_matches:
            # 选择匹配度最高的菜系
            best_cuisine = self._get_best_match(cuisine_matches, self.CUISINE_SYNONYMS)
            query.cuisine = self.CUISINE_SYNONYMS.get(best_cuisine)
            query.cuisine_keywords = cuisine_matches
            matched_keywords.extend(cuisine_matches)
        
        # 2. 解析菜品
        dish_matches = self.dish_pattern.findall(text)
        if dish_matches:
            query.dish = self.DISH_KEYWORDS.get(dish_matches[0])
            query.dish_keywords = dish_matches
            matched_keywords.extend(dish_matches)
        
        # 3. 解析口味维度
        flavor_matches = self.flavor_pattern.findall(text)
        if flavor_matches:
            query.flavor_tags = list(set([
                self.FLAVOR_MAPPING.get(f) for f in flavor_matches
            ]))
            matched_keywords.extend(flavor_matches)
        
        # 4. 解析辣度
        spice_matches = self.spice_pattern.findall(text)
        if spice_matches:
            # 取最高辣度
            spice_levels = [self.SPICE_LEVELS.get(s, 0) for s in spice_matches]
            query.spice_level = max(spice_levels) if spice_levels else None
            matched_keywords.extend(spice_matches)
        
        # 5. 解析价格
        price_matches = self.price_pattern.findall(text)
        if price_matches:
            query.price_range = self.PRICE_MAPPING.get(price_matches[0])
            matched_keywords.extend(price_matches)
        
        # 6. 解析温度
        temp_matches = self.temp_pattern.findall(text)
        if temp_matches:
            query.temperature = self.TEMPERATURE_MAPPING.get(temp_matches[0])
            matched_keywords.extend(temp_matches)
        
        # 计算置信度
        query.confidence = self._calculate_confidence(text, matched_keywords)
        
        return query
    
    def _get_best_match(self, matches: List[str], mapping: Dict[str, Any]) -> str:
        """
        从多个匹配中选择最佳匹配
        优先选择长度最长的匹配
        """
        if not matches:
            return ""
        return max(matches, key=len)
    
    def _calculate_confidence(self, text: str, matched_keywords: List[str]) -> float:
        """
        计算解析置信度
        基于匹配关键词覆盖率和匹配质量
        """
        if not text or not matched_keywords:
            return 0.0
        
        # 计算匹配覆盖率
        matched_length = sum(len(kw) for kw in matched_keywords)
        coverage = matched_length / len(text)
        
        # 计算匹配质量（不同类型的匹配数量）
        unique_types = len(set([
            kw in self.CUISINE_SYNONYMS for kw in matched_keywords if kw in self.CUISINE_SYNONYMS
        ] + [
            kw in self.DISH_KEYWORDS for kw in matched_keywords if kw in self.DISH_KEYWORDS
        ] + [
            kw in self.FLAVOR_MAPPING for kw in matched_keywords if kw in self.FLAVOR_MAPPING
        ]))
        
        # 综合置信度
        confidence = min(coverage * 0.6 + unique_types * 0.15, 1.0)
        
        return round(confidence, 2)
    
    def fuzzy_match(self, text: str, threshold: float = 0.7) -> List[str]:
        """
        模糊匹配菜系和菜品
        用于处理未完全匹配的输入
        
        Args:
            text: 输入文本
            threshold: 相似度阈值（0-1）
            
        Returns:
            匹配到的关键词列表
        """
        matches = []
        
        # 在菜系同义词中模糊匹配
        for synonym in self.CUISINE_SYNONYMS.keys():
            similarity = SequenceMatcher(None, text, synonym).ratio()
            if similarity >= threshold:
                matches.append(synonym)
        
        return matches
    
    def suggest_cuisines(self, partial: str) -> List[str]:
        """
        根据部分输入建议可能的菜系
        用于自动补全
        
        Args:
            partial: 部分输入文本
            
        Returns:
            建议的菜系列表
        """
        suggestions = []
        
        for synonym in self.CUISINE_SYNONYMS.keys():
            if synonym.startswith(partial):
                suggestions.append(synonym)
        
        return suggestions[:10]  # 最多返回10个建议


# 导出
__all__ = ['TasteParser', 'TasteQuery']
