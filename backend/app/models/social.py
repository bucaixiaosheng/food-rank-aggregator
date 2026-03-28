"""
社交和内容模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Note(Base):
    """
    探店笔记模型
    """
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    restaurant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("restaurants.id"), nullable=True, index=True, comment="餐厅ID")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="笔记标题")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="笔记内容")
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="图片URL列表")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, comment="评分（1-5）")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="标签列表")
    likes_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    comments_count: Mapped[int] = mapped_column(Integer, default=0, comment="评论数")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", back_populates="notes")
    restaurant = relationship("Restaurant", back_populates="notes")
    comments = relationship("Comment", back_populates="note", lazy="dynamic")

    def __repr__(self):
        return f"<Note {self.title}>"


class Comment(Base):
    """
    评论模型
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    note_id: Mapped[int] = mapped_column(Integer, ForeignKey("notes.id"), nullable=False, index=True, comment="笔记ID")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="父评论ID（用于回复）")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容")
    likes_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", back_populates="comments")
    note = relationship("Note", back_populates="comments")

    def __repr__(self):
        return f"<Comment by user {self.user_id}>"


class Follow(Base):
    """
    关注关系模型
    """
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="关注者ID")
    following_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="被关注者ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"


class Favorite(Base):
    """
    收藏夹模型
    """
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="收藏目标类型：restaurant/note")
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="目标ID")
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="收藏分组名称")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    user = relationship("User", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite {self.target_type}:{self.target_id} by user {self.user_id}>"
