"""
爬虫数据和排行榜模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CrawlTask(Base):
    """
    爬虫任务模型
    """
    __tablename__ = "crawl_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="平台名称")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", comment="任务状态：pending/running/completed/failed")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="完成时间")
    result_count: Mapped[int] = mapped_column(Integer, default=0, comment="抓取结果数量")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<CrawlTask {self.platform} - {self.status}>"


class PlatformRating(Base):
    """
    平台评分模型
    """
    __tablename__ = "platform_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True, comment="餐厅ID")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, comment="平台名称")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, comment="平台评分")
    review_count: Mapped[int] = mapped_column(Integer, default=0, comment="评论数")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="平台标签")
    platform_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="平台餐厅URL")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    restaurant = relationship("Restaurant", back_populates="platform_ratings")

    def __repr__(self):
        return f"<PlatformRating {self.platform} for restaurant {self.restaurant_id}>"


class Ranking(Base):
    """
    排行榜模型
    """
    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="榜单名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="榜单描述")
    ranking_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="榜单类型：hot/new/rating")
    restaurants: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="餐厅ID列表（按排名顺序）")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<Ranking {self.name}>"


class Blacklist(Base):
    """
    黑名单模型
    """
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="类型：restaurant/user")
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="目标ID")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="拉黑原因")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<Blacklist {self.target_type}:{self.target_id}>"
