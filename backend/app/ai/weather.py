"""
天气/季节推荐模块
根据天气和季节推荐合适的美食
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date
import aiohttp
import asyncio


@dataclass
class WeatherInfo:
    """
    天气信息
    """
    temperature: float  # 摄氏度
    weather: str  # 晴/阴/雨/雪等
    humidity: int  # 湿度百分比
    season: str  # 春/夏/秋/冬
    location: str = ""


@dataclass
class WeatherRecommendation:
    """
    天气推荐结果
    """
    cuisine_types: List[str]
    dishes: List[str]
    reasons: List[str]
    weather_info: WeatherInfo
    comfort_tips: List[str]


class WeatherRecommender:
    """
    天气/季节推荐器
    集成免费天气API，根据天气推荐美食
    """
    
    # 季节-菜系映射
    SEASON_CUISINES = {
        '春': {
            'recommended': ['Japanese', 'Cantonese', 'Jiangzhe', 'Snack'],
            'dishes': ['春笋', '香椿', '青团', '时蔬'],
            'reason': '春季养生，推荐清淡鲜美的时令菜品'
        },
        '夏': {
            'recommended': ['Snack', 'Dessert', 'Japanese', 'Cantonese'],
            'dishes': ['凉皮', '冰粉', '沙拉', '冷面', '凉菜'],
            'reason': '夏季炎热，推荐清凉解暑的美食'
        },
        '秋': {
            'recommended': ['Western', 'Hotpot', 'BBQ', 'Jiangzhe'],
            'dishes': ['大闸蟹', '羊肉', '栗子', '秋梨'],
            'reason': '秋季进补，推荐温补滋润的美食'
        },
        '冬': {
            'recommended': ['Hotpot', 'BBQ', 'Sichuan', 'Korean'],
            'dishes': ['火锅', '烤肉', '热汤', '砂锅', '炖菜'],
            'reason': '冬季寒冷，推荐暖身驱寒的美食'
        }
    }
    
    # 天气-菜系映射
    WEATHER_CUISINES = {
        '晴': {
            'recommended': ['BBQ', 'Hotpot', 'Western', 'Japanese'],
            'dishes': ['烧烤', '户外美食'],
            'reason': '天气晴朗，适合户外用餐或烧烤'
        },
        '阴': {
            'recommended': ['Hotpot', 'Snack', 'Dessert'],
            'dishes': ['火锅', '甜品', '小吃'],
            'reason': '阴天适合暖心美食'
        },
        '雨': {
            'recommended': ['Hotpot', 'Snack', 'Sichuan'],
            'dishes': ['麻辣烫', '火锅', '粥', '汤面'],
            'reason': '雨天适合热腾腾的汤类美食'
        },
        '雪': {
            'recommended': ['Hotpot', 'BBQ', 'Korean'],
            'dishes': ['火锅', '烤肉', '泡菜汤'],
            'reason': '雪天最适合火锅和烤肉'
        },
        '热': {
            'recommended': ['Dessert', 'Snack', 'Japanese'],
            'dishes': ['凉皮', '冰粉', '冷面', '沙拉'],
            'reason': '天气炎热，推荐清凉解暑'
        },
        '冷': {
            'recommended': ['Hotpot', 'BBQ', 'Sichuan'],
            'dishes': ['火锅', '烤肉', '热汤'],
            'reason': '天气寒冷，推荐暖身美食'
        }
    }
    
    # 温度范围映射
    TEMP_RANGES = {
        'very_cold': (-999, 0),    # 极冷
        'cold': (0, 10),            # 冷
        'cool': (10, 20),           # 凉爽
        'comfortable': (20, 26),    # 舒适
        'warm': (26, 32),           # 温暖
        'hot': (32, 999)            # 热
    }
    
    # 温度-推荐映射
    TEMP_RECOMMENDATIONS = {
        'very_cold': {
            'dishes': ['火锅', '烤肉', '羊肉汤', '砂锅'],
            'reason': '天气极冷，推荐高热量暖身美食'
        },
        'cold': {
            'dishes': ['热汤', '炖菜', '火锅', '面条'],
            'reason': '天气较冷，推荐热乎的美食'
        },
        'cool': {
            'dishes': ['时令菜品', '汤类', '粥'],
            'reason': '天气凉爽，适合各种美食'
        },
        'comfortable': {
            'dishes': ['各种美食皆宜'],
            'reason': '天气舒适，随心选择'
        },
        'warm': {
            'dishes': ['凉菜', '轻食', '寿司'],
            'reason': '天气温暖，推荐清爽美食'
        },
        'hot': {
            'dishes': ['凉皮', '冰粉', '冷面', '沙拉'],
            'reason': '天气炎热，推荐清凉解暑'
        }
    }
    
    def __init__(self):
        """初始化天气推荐器"""
        self.api_base = "https://wttr.in"
    
    async def get_weather(
        self,
        location: str = "Beijing"
    ) -> WeatherInfo:
        """
        获取天气信息
        使用免费的wttr.in API
        
        Args:
            location: 城市名称或坐标
            
        Returns:
            WeatherInfo对象
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/{location}?format=j1"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_weather_response(data, location)
        except Exception as e:
            # API调用失败，返回默认天气
            print(f"Weather API error: {e}")
            return self._get_default_weather(location)
        
        return self._get_default_weather(location)
    
    def _parse_weather_response(self, data: Dict, location: str) -> WeatherInfo:
        """
        解析wttr.in API响应
        """
        try:
            current = data.get('current_condition', [{}])[0]
            
            temperature = float(current.get('temp_C', 20))
            weather_code = current.get('weatherCode', '113')
            humidity = int(current.get('humidity', 50))
            
            # 将天气代码转换为描述
            weather = self._weather_code_to_desc(weather_code)
            
            # 判断季节
            season = self._get_season()
            
            return WeatherInfo(
                temperature=temperature,
                weather=weather,
                humidity=humidity,
                season=season,
                location=location
            )
        except Exception:
            return self._get_default_weather(location)
    
    def _weather_code_to_desc(self, code: str) -> str:
        """
        将wttr.in天气代码转换为描述
        """
        weather_map = {
            '113': '晴', '116': '晴间多云', '119': '阴',
            '122': '阴', '143': '雾', '176': '小雨',
            '179': '雨夹雪', '182': '雨夹雪', '185': '雨夹雪',
            '200': '雷阵雨', '227': '大雪', '230': '暴雪',
            '248': '雾', '260': '雾', '263': '小雨',
            '266': '小雨', '281': '雨夹雪', '284': '雨夹雪',
            '293': '小雨', '296': '小雨', '299': '中雨',
            '302': '中雨', '305': '大雨', '308': '暴雨',
            '311': '冻雨', '314': '冻雨', '317': '雨夹雪',
            '320': '雨夹雪', '323': '小雪', '326': '小雪',
            '329': '中雪', '332': '中雪', '335': '大雪',
            '338': '大雪', '350': '冰雹', '353': '小雨',
            '356': '中雨', '359': '大雨', '362': '雨夹雪',
            '365': '雨夹雪', '368': '小雪', '371': '中雪',
            '374': '冻雨', '377': '冰雹', '386': '雷阵雨',
            '389': '雷阵雨', '392': '雷阵雨', '395': '雷阵雨'
        }
        return weather_map.get(code, '晴')
    
    def _get_season(self) -> str:
        """
        根据当前日期判断季节
        """
        month = datetime.now().month
        
        if month in [3, 4, 5]:
            return '春'
        elif month in [6, 7, 8]:
            return '夏'
        elif month in [9, 10, 11]:
            return '秋'
        else:
            return '冬'
    
    def _get_default_weather(self, location: str) -> WeatherInfo:
        """
        获取默认天气信息（API失败时使用）
        """
        return WeatherInfo(
            temperature=20.0,
            weather='晴',
            humidity=50,
            season=self._get_season(),
            location=location
        )
    
    async def recommend_by_weather(
        self,
        location: str = "Beijing",
        weather: Optional[WeatherInfo] = None
    ) -> WeatherRecommendation:
        """
        根据天气推荐美食
        
        Args:
            location: 城市名称
            weather: 天气信息（可选，不提供则自动获取）
            
        Returns:
            WeatherRecommendation对象
        """
        # 获取天气信息
        if not weather:
            weather = await self.get_weather(location)
        
        cuisine_types = []
        dishes = []
        reasons = []
        comfort_tips = []
        
        # 1. 基于季节推荐
        season_config = self.SEASON_CUISINES.get(weather.season, {})
        cuisine_types.extend(season_config.get('recommended', []))
        dishes.extend(season_config.get('dishes', []))
        if season_config.get('reason'):
            reasons.append(season_config['reason'])
        
        # 2. 基于天气推荐
        weather_config = self.WEATHER_CUISINES.get(weather.weather, {})
        cuisine_types.extend(weather_config.get('recommended', []))
        dishes.extend(weather_config.get('dishes', []))
        if weather_config.get('reason'):
            reasons.append(weather_config['reason'])
        
        # 3. 基于温度推荐
        temp_category = self._get_temp_category(weather.temperature)
        temp_config = self.TEMP_RECOMMENDATIONS.get(temp_category, {})
        dishes.extend(temp_config.get('dishes', []))
        if temp_config.get('reason'):
            reasons.append(temp_config['reason'])
        
        # 4. 生成舒适提示
        comfort_tips = self._generate_comfort_tips(weather)
        
        # 去重
        cuisine_types = list(dict.fromkeys(cuisine_types))
        dishes = list(dict.fromkeys(dishes))
        
        return WeatherRecommendation(
            cuisine_types=cuisine_types,
            dishes=dishes,
            reasons=reasons,
            weather_info=weather,
            comfort_tips=comfort_tips
        )
    
    def _get_temp_category(self, temperature: float) -> str:
        """
        根据温度获取类别
        """
        for category, (low, high) in self.TEMP_RANGES.items():
            if low <= temperature < high:
                return category
        return 'comfortable'
    
    def _generate_comfort_tips(self, weather: WeatherInfo) -> List[str]:
        """
        生成舒适提示
        """
        tips = []
        
        # 温度提示
        if weather.temperature < 10:
            tips.append('天气较冷，注意保暖')
        elif weather.temperature > 30:
            tips.append('天气炎热，注意防暑')
        
        # 天气提示
        if weather.weather in ['雨', '小雨', '中雨', '大雨']:
            tips.append('下雨天，出门记得带伞')
        elif weather.weather in ['雪', '小雪', '中雪', '大雪']:
            tips.append('下雪天，注意路滑')
        
        # 湿度提示
        if weather.humidity > 80:
            tips.append('湿度较高，注意防潮')
        elif weather.humidity < 30:
            tips.append('空气干燥，多补充水分')
        
        return tips
    
    def get_seasonal_dishes(self, season: str) -> List[str]:
        """
        获取季节性推荐菜品
        
        Args:
            season: 季节（春/夏/秋/冬）
            
        Returns:
            推荐菜品列表
        """
        return self.SEASON_CUISINES.get(season, {}).get('dishes', [])


# 导出
__all__ = ['WeatherRecommender', 'WeatherInfo', 'WeatherRecommendation']
