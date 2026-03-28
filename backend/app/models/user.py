"""
用户和口味画像模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    """
    用户模型
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="头像URL")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True, comment="个人简介")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    taste_profile = relationship("TasteProfile", back_populates="user", uselist=False)
    notes = relationship("Note", back_populates="user", lazy="dynamic")
    comments = relationship("Comment", back_populates="user", lazy="dynamic")
    favorites = relationship("Favorite", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.nickname}>"


class TasteProfile(Base):
    """
    用户口味画像模型
    """
    __tablename__ = "taste_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True, comment="用户ID")
    preferred_cuisines: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="偏好菜系列表")
    preferred_price_range: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="偏好价格区间")
    preferred_spice_level: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="辣度偏好（1-5）")
    flavor_tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="口味标签，如：甜、咸、酸等")
    dietary_restrictions: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="饮食限制，如：素食、过敏等")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", back_populates="taste_profile")

    def __repr__(self):
        return f"<TasteProfile user_id={self.user_id}>"


class UserActivity(Base):
    """
    用户行为记录模型
    """
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户ID")
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="行为类型：search/favorite/checkin")
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="目标类型：restaurant/note")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="目标ID")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="行为内容，如搜索关键词")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<UserActivity {self.activity_type} by user {self.user_id}>"
