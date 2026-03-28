"""
数据模型初始化
"""
from app.models.restaurant import Cuisine, Restaurant
from app.models.user import User, TasteProfile, UserActivity
from app.models.social import Note, Comment, Follow, Favorite
from app.models.crawler import CrawlTask, PlatformRating, Ranking, Blacklist

__all__ = [
    "Cuisine",
    "Restaurant",
    "User",
    "TasteProfile",
    "UserActivity",
    "Note",
    "Comment",
    "Follow",
    "Favorite",
    "CrawlTask",
    "PlatformRating",
    "Ranking",
    "Blacklist",
]
