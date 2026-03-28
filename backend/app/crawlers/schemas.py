"""
爬虫数据模型 - 统一数据结构
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class Platform(str, Enum):
    """平台枚举"""
    MEITUAN = "meituan"
    DIANPING = "dianping"
    XIAOHONGSHU = "xiaohongshu"
    AMAP = "amap"


class RestaurantData(BaseModel):
    """
    统一餐厅数据模型
    用于各平台爬虫返回数据
    """
    # 基本信息
    name: str = Field(..., description="餐厅名称")
    address: Optional[str] = Field(None, description="详细地址")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    phone: Optional[str] = Field(None, description="电话")
    
    # 菜系和价格
    cuisine_type: Optional[str] = Field(None, description="菜系类型")
    price_range: Optional[str] = Field(None, description="价格区间")
    avg_price: Optional[float] = Field(None, description="人均消费")
    
    # 评分和评论
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分（0-5分）")
    review_count: Optional[int] = Field(0, ge=0, description="评论数")
    
    # 描述和图片
    description: Optional[str] = Field(None, description="餐厅描述")
    image_url: Optional[str] = Field(None, description="主图URL")
    images: Optional[List[str]] = Field(default_factory=list, description="图片列表")
    
    # 平台信息
    platform: Platform = Field(..., description="数据来源平台")
    platform_id: Optional[str] = Field(None, description="平台餐厅ID")
    platform_url: Optional[str] = Field(None, description="平台餐厅URL")
    
    # 标签和推荐菜
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    recommended_dishes: Optional[List[str]] = Field(default_factory=list, description="推荐菜")
    
    # 营业时间
    business_hours: Optional[str] = Field(None, description="营业时间")
    
    # 元数据
    crawled_at: datetime = Field(default_factory=datetime.utcnow, description="爬取时间")
    raw_data: Optional[dict] = Field(None, description="原始数据（用于调试）")

    class Config:
        use_enum_values = True


class NoteData(BaseModel):
    """
    小红书笔记数据模型
    """
    title: str = Field(..., description="笔记标题")
    content: Optional[str] = Field(None, description="笔记内容")
    author: Optional[str] = Field(None, description="作者")
    
    # 互动数据
    likes: Optional[int] = Field(0, description="点赞数")
    collects: Optional[int] = Field(0, description="收藏数")
    comments: Optional[int] = Field(0, description="评论数")
    
    # 图片和标签
    images: Optional[List[str]] = Field(default_factory=list, description="图片列表")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    
    # 提取的餐厅信息
    mentioned_restaurants: Optional[List[str]] = Field(default_factory=list, description="提到的餐厅")
    
    # 平台信息
    platform: Platform = Platform.XIAOHONGSHU
    platform_id: Optional[str] = Field(None, description="笔记ID")
    platform_url: Optional[str] = Field(None, description="笔记URL")
    
    crawled_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlResult(BaseModel):
    """
    爬取结果模型
    """
    platform: Platform = Field(..., description="平台")
    success: bool = Field(..., description="是否成功")
    count: int = Field(default=0, description="爬取数量")
    data: List[RestaurantData | NoteData] = Field(default_factory=list, description="爬取数据")
    error: Optional[str] = Field(None, description="错误信息")
    duration: Optional[float] = Field(None, description="耗时（秒）")
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
